from django.test import TestCase
from django.urls import reverse
from django.core.management import call_command
from django.contrib.auth.models import User


class AdminSeededTemplateSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed")
        cls.staff = User.objects.create_user(
            username="adminuser",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )

    def test_admin_dashboard_template_contains_kpi_labels(self):
        self.client.login(username="adminuser", password="pass12345")
        resp = self.client.get(reverse("admin_dashboard"))

        self.assertContains(resp, "Total Users")
        self.assertContains(resp, "Total Saves")
        self.assertContains(resp, "Completed Saves")
        self.assertContains(resp, "Average Progress")

    def test_admin_statistics_template_contains_core_labels(self):
        self.client.login(username="adminuser", password="pass12345")
        resp = self.client.get(reverse("admin_statistics"))

        self.assertContains(resp, "Ongoing")
        self.assertContains(resp, "Completed")
