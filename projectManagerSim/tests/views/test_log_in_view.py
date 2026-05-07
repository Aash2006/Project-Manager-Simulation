from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class LogInViewTests(TestCase):
    def setUp(self):
        self.url = reverse("log_in")

        # Staff user
        self.staff_user = User.objects.create_user(
            username="staff",
            password="password123"
        )
        self.staff_user.is_staff = True
        self.staff_user.save()

        # Normal user
        self.normal_user = User.objects.create_user(
            username="normal",
            password="password123"
        )

    # ------------------
    # GET Tests
    # ------------------

    def test_get_login_page_anonymous(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "log_in.html")

    def test_get_login_redirect_authenticated_user(self):
        self.client.login(username="staff", password="password123")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))

    # ------------------
    # POST Tests
    # ------------------

    def test_post_valid_staff_login(self):
        response = self.client.post(
            self.url,
            {
                "username": "staff",
                "password": "password123"
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin_dashboard"))

    def test_post_valid_normal_login(self):
        response = self.client.post(
            self.url,
            {
                "username": "normal",
                "password": "password123"
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("user_dashboard"))

    def test_post_invalid_credentials(self):
        response = self.client.post(
            self.url,
            {
                "username": "wrong",
                "password": "wrong"
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User does not exist")

    def test_post_invalid_form(self):
        response = self.client.post(
            self.url,
            {}  # Missing fields, form invalid
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid form")