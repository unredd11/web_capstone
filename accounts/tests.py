from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projects.models import Project
from verifications.models import AuditLog

from .models import Inspector


class InspectorAuditTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin@example.com',
            password='test-password',
            is_staff=True,
        )
        inspector_user = User.objects.create_user(
            username='inspector@example.com',
            password='test-password',
        )
        self.inspector = Inspector.objects.create(
            user=inspector_user,
            employee_id='DPWH-AUDIT-001',
            district='LDN 1st DEO',
        )

    def test_toggle_status_requires_admin(self):
        response = self.client.post(
            reverse(
                'accounts:toggle_inspector_status',
                args=[self.inspector.pk],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_toggle_status_updates_user_and_creates_audit_log(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                'accounts:toggle_inspector_status',
                args=[self.inspector.pk],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.inspector.refresh_from_db()
        self.inspector.user.refresh_from_db()
        self.assertFalse(self.inspector.is_active)
        self.assertFalse(self.inspector.user.is_active)
        self.assertTrue(
            AuditLog.objects.filter(
                action_type='deactivate_inspector',
                target_entity='Inspector',
                target_id=self.inspector.pk,
            ).exists()
        )

    def test_active_project_prevents_inspector_deactivation(self):
        Project.objects.create(
            project_name='Active Project',
            district='LDN 1st DEO',
            status='Ongoing',
            assigned_inspector=self.inspector,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                'accounts:toggle_inspector_status',
                args=[self.inspector.pk],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.inspector.refresh_from_db()
        self.inspector.user.refresh_from_db()
        self.assertTrue(self.inspector.is_active)
        self.assertTrue(self.inspector.user.is_active)
        self.assertFalse(
            AuditLog.objects.filter(
                action_type='deactivate_inspector',
                target_id=self.inspector.pk,
            ).exists()
        )

    def test_admin_can_edit_inspector_and_action_is_audited(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                'accounts:edit_inspector',
                args=[self.inspector.pk],
            ),
            {
                'first_name': 'Updated',
                'last_name': 'Inspector',
                'email': 'updated@example.com',
                'phone': '+639123456789',
                'district': 'LDN 2nd DEO',
                'position': 'Project Engineer',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.inspector.refresh_from_db()
        self.inspector.user.refresh_from_db()
        self.assertEqual(
            self.inspector.user.username,
            'updated@example.com',
        )
        self.assertEqual(self.inspector.district, 'LDN 2nd DEO')
        self.assertTrue(
            AuditLog.objects.filter(
                action_type='update_inspector',
                target_id=self.inspector.pk,
            ).exists()
        )

    def test_logout_requires_post_and_is_audited(self):
        self.client.force_login(self.admin)

        get_response = self.client.get(reverse('accounts:logout'))
        post_response = self.client.post(reverse('accounts:logout'))

        self.assertEqual(get_response.status_code, 405)
        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(
            AuditLog.objects.filter(
                action_type='admin_logout',
                target_id=self.admin.pk,
            ).exists()
        )

    def test_login_does_not_redirect_to_external_host(self):
        response = self.client.post(
            reverse('accounts:login'),
            {
                'username': self.admin.username,
                'password': 'test-password',
                'next': 'https://example.com/phishing',
            },
        )

        self.assertRedirects(
            response,
            reverse('dashboard:overview'),
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action_type='admin_login',
                target_id=self.admin.pk,
            ).exists()
        )
