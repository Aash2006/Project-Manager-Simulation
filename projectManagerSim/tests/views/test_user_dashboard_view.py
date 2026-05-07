from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class UserDashboardViewTest(TestCase):
    def setUp(self):
        self.url = reverse('user_dashboard')
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_dashboard_requires_login(self):
        """Verify that an unauthenticated request redirects to login."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/log_in/', response.url)

    def test_dashboard_renders_for_logged_in_user(self):
        """Verify that an authenticated user can access the dashboard."""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user_dashboard.html")