from django.test import TestCase
from django.contrib.auth import get_user_model

from projectManagerSim.forms import EmailChangeForm

User = get_user_model()


class EmailChangeFormTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="old@example.com",
            password="correct-password",
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            email="taken@example.com",
            password="other-password",
        )

    def test_valid_email_change(self):
        """Form is valid with correct password and unused email."""
        form = EmailChangeForm(
            data={
                "email": "new@example.com",
                "password": "correct-password",
            },
            user=self.user,
            instance=self.user,
        )

        self.assertTrue(form.is_valid())

    def test_invalid_password(self):
        """Form is invalid if password is incorrect."""
        form = EmailChangeForm(
            data={
                "email": "new@example.com",
                "password": "wrong-password",
            },
            user=self.user,
            instance=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)
        self.assertEqual(
            form.errors["password"][0],
            "Incorrect password.",
        )

    def test_email_already_in_use(self):
        """Form is invalid if email belongs to another user."""
        form = EmailChangeForm(
            data={
                "email": "taken@example.com",
                "password": "correct-password",
            },
            user=self.user,
            instance=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(
            form.errors["email"][0],
            "This email is already in use.",
        )

    def test_same_email_is_allowed(self):
        """User can submit their current email without error."""
        form = EmailChangeForm(
            data={
                "email": "old@example.com",
                "password": "correct-password",
            },
            user=self.user,
            instance=self.user,
        )

        self.assertTrue(form.is_valid())

    def test_form_save_updates_email(self):
        """Calling form.save() updates the user's email in the database."""
        form = EmailChangeForm(
            data={
                "email": "new@example.com",
                "password": "correct-password",
            },
            user=self.user,
            instance=self.user,
        )

        self.assertTrue(form.is_valid())

        form.save()

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")