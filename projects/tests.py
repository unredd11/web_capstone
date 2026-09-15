from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Inspector
from verifications.models import AuditLog

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
