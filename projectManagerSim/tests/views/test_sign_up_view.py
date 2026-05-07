from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class SignUpViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("sign_up")

    def test_get_renders_signup_template(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "sign_up.html")
        self.assertIn("form", response.context)

    def test_valid_signup_creates_user_and_logs_in(self):
        payload = {
            "username": "newuser",
            "email" : "New@User.com",
            "password1": "TestingPassWoahCrazyTestingVeryHardToGuess!",
            "password2": "TestingPassWoahCrazyTestingVeryHardToGuess!",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(response.status_code, 302)

        self.assertTrue(User.objects.filter(username="newuser").exists())

        user = User.objects.get(username="newuser")
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            user.id,
        )

    def test_invalid_signup_rerenders_form_with_errors(self):
        payload = {
            "username": "baduser",
            "email" : "Bad@User.com",
            "password1": "123",
            "password2": "456",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "sign_up.html")

        self.assertFalse(User.objects.filter(username="baduser").exists())

        form = response.context["form"]
        self.assertTrue(form.errors)

    def test_signup_does_not_log_in_on_invalid_form(self):
        payload = {
            "username": "",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)