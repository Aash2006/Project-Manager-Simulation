from django.test import TestCase
from django.urls import reverse
from django.core.management import call_command
from django.contrib.auth.models import User

from projectManagerSim.models import Save


class AdminHomeSeededViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed")

        cls.staff = User.objects.create_user(
            username="adminuser",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )

    def test_staff_can_access_admin_dashboard(self):
        self.client.login(username="adminuser", password="pass12345")
        resp = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(resp.status_code, 200)

    def test_admin_dashboard_has_seeded_kpi_context(self):
        self.client.login(username="adminuser", password="pass12345")
        resp = self.client.get(reverse("admin_dashboard"))

        self.assertIn("total_users", resp.context)
        self.assertIn("total_saves", resp.context)
        self.assertIn("completed_saves", resp.context)
        self.assertIn("avg_progress", resp.context)

        # Expected seeded values
        expected_players = User.objects.filter(is_superuser=False).count()
        self.assertEqual(resp.context["total_users"], expected_players)

        self.assertEqual(resp.context["total_saves"], Save.objects.count())
        self.assertEqual(resp.context["completed_saves"], Save.objects.filter(status=Save.Status.COMPLETED).count())

        avg = resp.context["avg_progress"]
        self.assertTrue(isinstance(avg, int))
        self.assertGreaterEqual(avg, 0)
        self.assertLessEqual(avg, 100)
