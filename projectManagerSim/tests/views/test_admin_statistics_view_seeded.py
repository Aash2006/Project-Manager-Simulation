from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from projectManagerSim.models import Save


class AdminStatisticsSeededViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed")
        cls.staff = User.objects.create_user(
            username="adminuser",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )

    def test_statistics_page_accessible(self):
        self.client.login(username="adminuser", password="pass12345")
        resp = self.client.get(reverse("admin_statistics"))
        self.assertEqual(resp.status_code, 200)

    def test_statistics_context_matches_seeded_data(self):
        self.client.login(username="adminuser", password="pass12345")
        resp = self.client.get(reverse("admin_statistics"))

        self.assertEqual(resp.context["ongoing_saves_count"], Save.objects.filter(status=Save.Status.ONGOING).count())
        self.assertEqual(resp.context["completed_saves_count"], Save.objects.filter(status=Save.Status.COMPLETED).count())
        
