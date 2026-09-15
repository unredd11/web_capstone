from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

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
