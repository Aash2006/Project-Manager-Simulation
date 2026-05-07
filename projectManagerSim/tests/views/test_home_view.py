from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class HomeViewTests(TestCase):

    def setUp(self):
        # Create users
        self.staff_user = User.objects.create_user(
            username="staff",
            password="password123"
        )
        self.staff_user.is_staff = True
        self.staff_user.save()

        self.normal_user = User.objects.create_user(
            username="normal",
            password="password123"
        )
        self.normal_user.is_staff = False
        self.normal_user.save()

    def test_redirect_anonymous_user_to_login(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log_in"))

    def test_redirect_staff_user_to_admin_dashboard(self):
        self.client.login(username="staff", password="password123")

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin_dashboard"))

    def test_redirect_normal_user_to_dashboard(self):
        self.client.login(username="normal", password="password123")

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("user_dashboard"))