from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from projectManagerSim.models import Save, TaskType, Task, Character, SaveCharacter


class AdminSaveSpreadsheetTemplateTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="adminuser",
            password="pass12345",
            is_staff=True,
        )

        player = User.objects.create_user(username="alice", password="pass12345")
        save = Save.objects.create(
            user=player,
            save_name="Alice Save A",
            progress_percent=25,
            current_day=3,
            score=10,
            status=Save.Status.ONGOING,
        )

        tt = TaskType.objects.create(task_type_name="Backend")
        task = Task.objects.create(name="API work", time_to_complete=5, task_type=tt)
        char = Character.objects.create(first_name="Eve", last_name="Ng", primary_role='backend', description="desc")

        SaveCharacter.objects.create(
            game_save=save,
            character=char,
            task_assigned=task,
            time_remaining_on_task=2,
            current_energy=80,
            current_happiness=90,
        )

    def test_uses_expected_template(self):
        self.client.login(username="adminuser", password="pass12345")
        resp = self.client.get(reverse("admin_save_list"))
        self.assertTemplateUsed(resp, "admin_save_list.html")

    def test_template_contains_table_headers(self):
        self.client.login(username="adminuser", password="pass12345")
        resp = self.client.get(reverse("admin_save_list"))

        self.assertContains(resp, "<table", html=False)
        c1 = Character.objects.create(first_name="Eve", last_name="Ng", primary_role='backend', description="desc")
        c2 = Character.objects.create(first_name="Max", last_name="Li", primary_role='tester', description="desc")
        self.assertContains(resp, "<th>Status</th>", html=False)
        self.assertContains(resp, "<th>Days</th>", html=False)
