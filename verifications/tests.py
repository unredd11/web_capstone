import json
from datetime import datetime
from decimal import Decimal
from io import BytesIO
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import Inspector
from projects.models import Project, ProjectAssignment
from verifications.models import AuditLog, BlockchainRecord, InspectionImage, VerificationReport


class VerificationSchemaTests(SimpleTestCase):
    def test_report_contains_review_and_progress_fields(self):
        field_names = {field.name for field in VerificationReport._meta.get_fields()}

        self.assertTrue({
            'progress_percentage',
            'accomplishment_description',
            'reviewed_by',
            'reviewed_at',
            'review_notes',
        }.issubset(field_names))

    def test_inspection_image_contains_authentication_metadata(self):
        field_names = {field.name for field in InspectionImage._meta.get_fields()}

        self.assertTrue({
            'image_file',
            'sha256_hash',
            'perceptual_hash',
            'latitude',
            'longitude',
            'gps_accuracy',
            'captured_at',
            'geofence_distance',
            'geofence_status',
        }.issubset(field_names))

    def test_blockchain_receipt_is_one_to_one_with_image(self):
        field = BlockchainRecord._meta.get_field('inspection_image')

        self.assertTrue(field.one_to_one)

    def test_audit_log_keeps_user_optional(self):
        field = AuditLog._meta.get_field('user')

        self.assertTrue(field.null)
        self.assertEqual(field.remote_field.on_delete.__name__, 'SET_NULL')


class VerificationWorkflowTests(TestCase):
    def setUp(self):
        self.media_directory = tempfile.mkdtemp(prefix='dpwh-verification-tests-')
        self.override_media = override_settings(MEDIA_ROOT=self.media_directory)
        self.override_media.enable()
        self.addCleanup(self.override_media.disable)
        self.addCleanup(shutil.rmtree, self.media_directory, True)

        self.admin = User.objects.create_user(
            username='admin@example.com',
            password='test-password',
            is_staff=True,
        )
        inspector_user = User.objects.create_user(
            username='inspector@example.com',
            password='test-password',
            first_name='Field',
            last_name='Inspector',
        )
        self.inspector = Inspector.objects.create(
            user=inspector_user,
            employee_id='DPWH-TEST-001',
            district='LDN 1st DEO',
        )
        self.project = Project.objects.create(
            project_name='Test Road Project',
            district='LDN 1st DEO',
            assigned_inspector=self.inspector,
            latitude=Decimal('8.2280000'),
            longitude=Decimal('124.2452000'),
            geofence_radius=Decimal('100.00'),
            status='Ongoing',
        )
        self.report = VerificationReport.objects.create(
            project=self.project,
            inspector=self.inspector,
            progress_percentage=Decimal('25.00'),
            accomplishment_description='Initial site work completed.',
        )

    def create_test_image(self):
        image_bytes = BytesIO()
        Image.new('RGB', (32, 32), color=(20, 100, 180)).save(image_bytes, format='PNG')
        return SimpleUploadedFile(
            'inspection.png',
            image_bytes.getvalue(),
            content_type='image/png',
        )

    def test_pending_reports_requires_admin(self):
        response = self.client.get(reverse('verifications:pending'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_upload_generates_hashes_geofence_and_audit_log(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('verifications:upload_image', args=[self.report.pk]),
            {
                'image_file': self.create_test_image(),
                'latitude': '8.2280000',
                'longitude': '124.2452000',
                'altitude': '20.00',
                'gps_accuracy': '5.00',
                'captured_at': timezone.make_aware(datetime(2026, 9, 9, 10, 0)),
            },
        )

        self.assertEqual(response.status_code, 302)
        image = InspectionImage.objects.get(report=self.report)
        blockchain_record = BlockchainRecord.objects.get(
            inspection_image=image
        )
        self.assertEqual(len(image.sha256_hash), 64)
        self.assertEqual(len(image.perceptual_hash), 16)
        self.assertEqual(image.geofence_status, 'Inside')
        self.assertEqual(image.geofence_distance, Decimal('0.00'))
        self.assertEqual(blockchain_record.commit_status, 'Pending')
        self.assertTrue(
            AuditLog.objects.filter(
                action_type='upload_image',
                target_entity='InspectionImage',
                target_id=image.pk,
            ).exists()
        )

    def test_rejection_requires_notes_and_creates_audit_log(self):
        self.client.force_login(self.admin)
        review_url = reverse('verifications:review_report', args=[self.report.pk])

        self.client.post(review_url, {'decision': 'Rejected', 'review_notes': ''})
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, 'Pending')

        self.client.post(
            review_url,
            {'decision': 'Rejected', 'review_notes': 'Image does not show the project site.'},
        )
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, 'Rejected')
        self.assertEqual(self.report.reviewed_by, self.admin)
        self.assertIsNotNone(self.report.reviewed_at)
        self.assertTrue(
            AuditLog.objects.filter(
                action_type='rejected',
                target_entity='VerificationReport',
                target_id=self.report.pk,
            ).exists()
        )

    def test_approval_is_blocked_without_an_image(self):
        self.client.force_login(self.admin)
        self.client.post(
            reverse('verifications:review_report', args=[self.report.pk]),
            {'decision': 'Approved', 'review_notes': ''},
        )

        self.report.refresh_from_db()
        self.assertEqual(self.report.status, 'Pending')

    def test_approval_updates_project_progress(self):
        InspectionImage.objects.create(
            report=self.report,
            image_file=self.create_test_image(),
            sha256_hash='a' * 64,
            perceptual_hash='b' * 16,
            latitude=Decimal('8.2280000'),
            longitude=Decimal('124.2452000'),
            captured_at=timezone.now(),
            geofence_distance=Decimal('0.00'),
            geofence_status='Inside',
            file_size=100,
            mime_type='image/png',
        )
        self.project.progress_percentage = Decimal('10.00')
        self.project.status = 'Pending'
        self.project.save(
            update_fields=['progress_percentage', 'status']
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                'verifications:review_report',
                args=[self.report.pk],
            ),
            {
                'decision': 'Approved',
                'review_notes': 'Evidence confirmed.',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.report.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(self.report.status, 'Approved')
        self.assertEqual(
            self.project.progress_percentage,
            Decimal('25.00'),
        )
        self.assertEqual(self.project.status, 'Ongoing')

    def test_mobile_login_and_report_history(self):
        login_response = self.client.post(
            reverse('verifications:mobile_login'),
            data=json.dumps(
                {
                    'username': 'inspector@example.com',
                    'password': 'test-password',
                }
            ),
            content_type='application/json',
        )

        self.assertEqual(login_response.status_code, 200)
        token = login_response.json()['token']
        history_response = self.client.get(
            reverse('verifications:mobile_report_history'),
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        self.assertEqual(history_response.status_code, 200)
        history_data = history_response.json()
        self.assertEqual(history_data['count'], 1)
        self.assertEqual(
            history_data['reports'][0]['id'],
            self.report.pk,
        )

    def test_mobile_submission_prepares_blockchain_and_audit_records(self):
        login_response = self.client.post(
            reverse('verifications:mobile_login'),
            data=json.dumps(
                {
                    'username': 'inspector@example.com',
                    'password': 'test-password',
                }
            ),
            content_type='application/json',
        )
        token = login_response.json()['token']

        response = self.client.post(
            reverse('verifications:mobile_submit_report'),
            {
                'project_id': str(self.project.pk),
                'progress_percentage': '30.00',
                'accomplishment_description': 'Mobile submission.',
                'image_file': self.create_test_image(),
                'latitude': '8.2280000',
                'longitude': '124.2452000',
                'altitude': '20.00',
                'gps_accuracy': '5.00',
                'captured_at': timezone.now().isoformat(),
            },
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        self.assertEqual(response.status_code, 201)
        submitted_report = VerificationReport.objects.get(
            accomplishment_description='Mobile submission.'
        )
        submitted_image = submitted_report.images.get()
        self.assertTrue(
            BlockchainRecord.objects.filter(
                inspection_image=submitted_image,
                commit_status='Pending',
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action_type='mobile_report_submission',
                target_id=submitted_report.pk,
            ).exists()
        )

    def test_previous_inspector_cannot_access_reassigned_project(self):
        replacement_user = User.objects.create_user(
            username='replacement@example.com',
            password='test-password',
        )
        replacement_inspector = Inspector.objects.create(
            user=replacement_user,
            employee_id='DPWH-TEST-002',
            district='LDN 1st DEO',
        )
        ProjectAssignment.objects.create(
            project=self.project,
            inspector=self.inspector,
        )
        self.project.assigned_inspector = replacement_inspector
        self.project.save(update_fields=['assigned_inspector'])

        login_response = self.client.post(
            reverse('verifications:mobile_login'),
            data=json.dumps(
                {
                    'username': 'inspector@example.com',
                    'password': 'test-password',
                }
            ),
            content_type='application/json',
        )
        token = login_response.json()['token']

        projects_response = self.client.get(
            reverse('verifications:mobile_projects'),
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        submission_response = self.client.post(
            reverse('verifications:mobile_submit_report'),
            {
                'project_id': str(self.project.pk),
                'progress_percentage': '40.00',
                'accomplishment_description': 'Unauthorized submission.',
            },
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        self.assertEqual(projects_response.status_code, 200)
        self.assertEqual(projects_response.json()['count'], 0)
        self.assertEqual(submission_response.status_code, 403)
