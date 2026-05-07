from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class AccountSettingsViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="old@example.com",
            password="old-password",
        )

        self.url = reverse("user_settings")
        self.client.login(username="testuser", password="old-password")

    def test_get_renders_both_forms(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertIn("email_form", response.context)


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

        self.user.refresh_from_db()
        self.assertTrue(
            self.user.check_password("ReallyAwfulPasswordThatSucks")
        )

        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

    def test_password_change_invalid(self):
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

        self.assertIn("form", response.context)
        form = response.context["form"]

        self.assertIn("old_password", form.errors)
        self.assertTrue(
            any("incorrect" in e.lower() for e in form.errors["old_password"])
        )


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

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")

    def test_email_change_invalid_password(self):
        response = self.client.post(
            self.url,
            {
                "change_email": "",
                "email": "new@example.com",
                "password": "wrong-password",
            },
        )

        

        self.assertEqual(response.status_code, 200)

        self.assertIn("email_form", response.context)
        form = response.context["email_form"]

        self.assertIn("password", form.errors)
        self.assertTrue(
            any("incorrect" in e.lower() for e in form.errors["password"])
        )
