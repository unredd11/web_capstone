from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class TestDashboardAccess(TestCase):
    def test_dashboard_requires_an_administrator(self):
        response = self.client.get(reverse('dashboard:overview'))

        self.assertEqual(response.status_code, 302)

    def test_dashboard_renders_for_an_administrator(self):
        administrator = User.objects.create_user(
            username='dashboard-admin@example.com',
            password='test-password',
            is_staff=True,
        )
        self.client.force_login(administrator)

        response = self.client.get(reverse('dashboard:overview'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Active Projects')
        self.assertContains(response, 'Project Location Map')
