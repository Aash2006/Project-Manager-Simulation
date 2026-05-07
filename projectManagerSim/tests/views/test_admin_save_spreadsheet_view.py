from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projectManagerSim.models import Character, Save, SaveCharacter, Task, TaskType


class AdminSaveSpreadsheetViewTests(TestCase):
    def setUp(self):
        # Staff user (allowed)
        self.staff = User.objects.create_user(
            username="adminuser",
            password="pass12345",
            is_staff=True,
        )

        # Non-staff user (blocked)
        self.normal = User.objects.create_user(
            username="normaluser",
            password="pass12345",
            is_staff=False,
        )

        # Players + saves
        self.player1 = User.objects.create_user(username="alice", password="pass12345")
        self.player2 = User.objects.create_user(username="bob", password="pass12345")

        self.save1 = Save.objects.create(
            user=self.player1,
            save_name="Alice Save A",
            progress_percent=25,
            current_day=3,
            score=10,
            status=Save.Status.ONGOING,
        )
        self.save2 = Save.objects.create(
            user=self.player2,
            save_name="Bob Final Run",
            progress_percent=100,
            current_day=12,
            score=999,
            status=Save.Status.COMPLETED,
        )

        # Team state for save1
        tt = TaskType.objects.create(task_type_name="Backend")
        task = Task.objects.create(name="API work", time_to_complete=5, task_type=tt)

        c1 = Character.objects.create(
            first_name="Eve", last_name="Ng", description="desc"
        )
        c2 = Character.objects.create(
            first_name="Max", last_name="Li", description="desc"
        )

        s1 = SaveCharacter.objects.create(
            game_save=self.save1,
            character=c1,
            task_assigned=task,
            time_remaining_on_task=2,
            current_energy=80,
            current_happiness=90,
        )
        s1.current_energy = 80
        s1.current_happiness = 90
        s1.save()
        s2 = SaveCharacter.objects.create(
            game_save=self.save1,
            character=c2,
            task_assigned=None,
            time_remaining_on_task=0,
            current_energy=60,
            current_happiness=70,
        )
        s2.current_energy = 60
        s2.current_happiness = 70
        s2.save()

    def test_non_staff_redirected(self):
        self.client.login(username="normaluser", password="pass12345")
        resp = self.client.get(reverse("admin_save_list"))
        self.assertEqual(resp.status_code, 302)  # redirect to admin login

    def test_staff_can_access(self):
        self.client.login(username="adminuser", password="pass12345")
        resp = self.client.get(reverse("admin_save_list"))
        self.assertEqual(resp.status_code, 200)

    def test_renders_rows_for_saves(self):
        self.client.login(username="adminuser", password="pass12345")
        resp = self.client.get(reverse("admin_save_list"))

        self.assertContains(resp, "alice")
        self.assertContains(resp, "Alice Save A")
        self.assertContains(resp, "ONGOING")
        self.assertContains(resp, "Days")  # header check

        self.assertContains(resp, "bob")
        self.assertContains(resp, "Bob Final Run")
        self.assertContains(resp, "COMPLETED")

    def test_search_by_username_or_save_name(self):
        self.client.login(username="adminuser", password="pass12345")

        resp = self.client.get(reverse("admin_save_list"), {"q": "ali"})
        self.assertContains(resp, "alice")
        self.assertNotContains(resp, "bob")

        resp2 = self.client.get(reverse("admin_save_list"), {"q": "Final"})
        self.assertContains(resp2, "Bob Final Run")
        self.assertNotContains(resp2, "Alice Save A")

    def test_team_state_shown_for_save(self):
        self.client.login(username="adminuser", password="pass12345")
        resp = self.client.get(reverse("admin_save_list"))

        self.assertContains(resp, "Eve")
        self.assertContains(resp, "Max")
        self.assertContains(resp, "API work")
        self.assertContains(resp, "Energy: 80")
        self.assertContains(resp, "Happiness: 90")
        self.assertContains(resp, "Time left: 2")

    def test_team_member_wlb_shown(self):
        self.client.login(username="adminuser", password="pass12345")
        resp = self.client.get(reverse("admin_save_list"))
        self.assertContains(resp, "WLB: 50")  # both characters have default WLB of 50
