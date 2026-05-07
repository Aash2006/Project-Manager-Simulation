from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class AdminSettingsViewTests(TestCase):

    def setUp(self):
        self.staff = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="old-password",
            is_staff=True,
            is_superuser=True,
        )
        self.url = reverse("admin_settings")
        self.client.login(username="adminuser", password="old-password")

    # ---- Access control ----

    def test_staff_can_access_settings(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_redirected(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_non_staff_user_redirected(self):
        self.client.logout()
        User.objects.create_user(username="player", password="pass12345", is_staff=False)
        self.client.login(username="player", password="pass12345")
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    # ---- GET ----

    def test_get_renders_both_forms(self):
        response = self.client.get(self.url)
        self.assertIn("form", response.context)
        self.assertIn("email_form", response.context)

    def test_get_uses_admin_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "admin/admin_settings.html")
        self.assertTemplateUsed(response, "admin_base.html")

    # ---- Password change ----

    def test_password_change_success(self):
        response = self.client.post(
            self.url,
            {
                "change_password": "",
                "old_password": "old-password",
                "new_password1": "ReallyAwfulPasswordThatSucks",
                "new_password2": "ReallyAwfulPasswordThatSucks",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.check_password("ReallyAwfulPasswordThatSucks"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_password_change_redirects_to_admin_settings(self):
        response = self.client.post(
            self.url,
            {
                "change_password": "",
                "old_password": "old-password",
                "new_password1": "ReallyAwfulPasswordThatSucks",
                "new_password2": "ReallyAwfulPasswordThatSucks",
            },
        )
        self.assertRedirects(response, self.url)

    def test_password_change_invalid_stays_on_page(self):
        response = self.client.post(
            self.url,
            {
                "change_password": "",
                "old_password": "wrong-password",
                "new_password1": "ReallyAwfulPasswordThatSucks",
                "new_password2": "ReallyAwfulPasswordThatSucks",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("old_password", response.context["form"].errors)

    # ---- Email change ----

    def test_email_change_success(self):
        response = self.client.post(
            self.url,
            {
                "change_email": "",
                "email": "new@example.com",
                "password": "old-password",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.email, "new@example.com")

    def test_email_change_redirects_to_admin_settings(self):
        response = self.client.post(
            self.url,
            {
                "change_email": "",
                "email": "new@example.com",
                "password": "old-password",
            },
        )
        self.assertRedirects(response, self.url)

    def test_email_change_invalid_password_stays_on_page(self):
        response = self.client.post(
            self.url,
            {
                "change_email": "",
                "email": "new@example.com",
                "password": "wrong-password",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("password", response.context["email_form"].errors)
