from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Inspector
from verifications.models import AuditLog

from .forms import AssignInspectorForm, ProjectForm
from .models import Project


class ProjectAuditTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin@example.com',
            password='test-password',
            is_staff=True,
        )
        inspector_user = User.objects.create_user(
            username='inspector@example.com',
        )
        self.inspector = Inspector.objects.create(
            user=inspector_user,
            employee_id='DPWH-PROJECT-001',
            district='LDN 1st DEO',
        )
        self.project = Project.objects.create(
            project_name='Audit Test Project',
            district='LDN 1st DEO',
        )

    def test_project_pages_require_admin(self):
        urls = [
            reverse('projects:project_list'),
            reverse('projects:project_add'),
            reverse('projects:project_edit', args=[self.project.pk]),
            reverse('projects:assign_inspector', args=[self.project.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('accounts:login'), response.url)

    def test_assign_inspector_creates_audit_log(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                'projects:assign_inspector',
                args=[self.project.pk],
            ),
            {
                'inspector': str(self.inspector.pk),
                'notes': 'Assigned for testing.',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.project.refresh_from_db()
        self.assertEqual(
            self.project.assigned_inspector,
            self.inspector,
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action_type='assign_inspector',
                target_entity='Project',
                target_id=self.project.pk,
            ).exists()
        )

    def test_project_form_rejects_incomplete_coordinates(self):
        form = ProjectForm(
            data={
                'project_name': 'Invalid Coordinates',
                'district': 'LDN 1st DEO',
                'latitude': '8.2280000',
                'longitude': '',
                'geofence_radius': '100',
                'budget': '1000000',
                'progress_percentage': '0',
                'status': 'Pending',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            'Latitude and longitude must be provided together.',
            form.non_field_errors(),
        )

    def test_project_form_rejects_invalid_dates_and_district(self):
        other_user = User.objects.create_user(
            username='other@example.com',
        )
        other_inspector = Inspector.objects.create(
            user=other_user,
            employee_id='DPWH-PROJECT-002',
            district='LDN 2nd DEO',
        )
        form = ProjectForm(
            data={
                'project_name': 'Invalid Assignment',
                'district': 'LDN 1st DEO',
                'assigned_inspector': str(other_inspector.pk),
                'latitude': '8.2280000',
                'longitude': '124.2452000',
                'geofence_radius': '100',
                'budget': '1000000',
                'progress_percentage': '0',
                'start_date': '2026-09-20',
                'end_date': '2026-09-19',
                'status': 'Pending',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)
        self.assertIn('assigned_inspector', form.errors)

    def test_assignment_form_lists_only_active_same_district_inspectors(self):
        other_user = User.objects.create_user(
            username='different-district@example.com',
        )
        other_inspector = Inspector.objects.create(
            user=other_user,
            employee_id='DPWH-PROJECT-003',
            district='LDN 2nd DEO',
        )

        form = AssignInspectorForm(project=self.project)
        inspector_ids = set(
            form.fields['inspector'].queryset.values_list(
                'pk',
                flat=True,
            )
        )

        self.assertIn(self.inspector.pk, inspector_ids)
        self.assertNotIn(other_inspector.pk, inspector_ids)
