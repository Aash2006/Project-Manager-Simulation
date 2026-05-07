from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class LogoutViewTests(TestCase):
    def setUp(self):
        # Create a user for testing
        self.username = "testuser"
        self.password = "password123"
        self.user = User.objects.create_user(
            username=self.username, 
            password=self.password
        )
        self.logout_url = reverse('log_out')
        self.home_url = reverse('home')

    def test_logout_redirects_to_home(self):
        """Verify successful logout redirects to the home page."""
        self.client.login(username=self.username, password=self.password)

        response = self.client.get(self.logout_url)
        
        self.assertRedirects(response, self.home_url, fetch_redirect_response=False)

    def test_logout_clears_session(self):
        """Verify the user is actually logged out of the session."""
        self.client.login(username=self.username, password=self.password)
    
        self.client.get(self.logout_url)
        
        # Check if '_auth_user_id' is gone from the session
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_requires_login(self):
        """Verify that an anonymous user is redirected to login page."""
        response = self.client.get(self.logout_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/log_in/', response.url)