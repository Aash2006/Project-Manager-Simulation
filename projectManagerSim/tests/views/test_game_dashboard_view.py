from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projectManagerSim.models import Character, Save, SaveCharacter, Task, TaskType


class GameDashboardViewTests(TestCase):

    def setUp(self):
        # Create users
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", password="password123"
        )

        # Create saves
        self.save = Save.objects.create(
            user=self.user, active=True, save_name="User 1 Game"
        )
        self.save2 = Save.objects.create(
            user=self.user2, active=True, save_name="User 2 Game"
        )

        # Create characters
        self.character1 = Character.objects.create(
            first_name="Alice", last_name="Smith", description="Senior Dev",initial_energy=10
        )
        self.character2 = Character.objects.create(
            first_name="Bob", last_name="Jones", description="Junior Dev",initial_energy=100
        )

        # Create tasks and task types
        self.task_type = TaskType.objects.create(task_type_name="Backend")
        self.task1 = Task.objects.create(
            name="API Development",
            time_to_complete=6,
            task_type=self.task_type,
            energy_cost=25,
            unlocks_at_percent=0
        )

        # Assign characters to saves
        # Working character with no task and max energy
        self.save_character1 = SaveCharacter.objects.create(
            game_save=self.save,
            character=self.character1,
            task_assigned=None,
            current_energy=10,
            is_resting=False,
        )
        # Resting character with low energy
        self.save_character2 = SaveCharacter.objects.create(
            game_save=self.save,
            character=self.character2,
            task_assigned=None,
            current_energy=100,
            is_resting=True,
        )

        # URL for dashboard
        self.url = reverse("game_dashboard")  # use your actual URL name
        self.client.force_login(self.user)

    def test_dashboard_renders_and_context_keys(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        expected_keys = [
            "current_user",
            "save",
            "save_characters",
            "working_characters",
            "resting_characters",
            "working_no_task",
            "low_energy",
            "max_energy",
            "tasks",
            "save_characters_id_list",
        ]

        for key in expected_keys:
            self.assertIn(key, response.context)

    def test_context_filtered_correctly(self):
        response = self.client.get(self.url)

        # DB objects from setUp that we will use to compare
        actual_save_characters = SaveCharacter.objects.all()
        actual_tasks = Task.objects.all()
        actual_save_characters_id_list = list(
            actual_save_characters.values_list("pk", flat=True)
        )

        # JSON response
        save_characters = response.context["save_characters"]
        working_chars = response.context["working_characters"]
        resting_chars = response.context["resting_characters"]
        working_no_task = response.context["working_no_task"]
        low_energy = response.context["low_energy"]
        max_energy = response.context["max_energy"]
        save = response.context["save"]
        save_characters_id_list = response.context["save_characters_id_list"]

        # Asserting out data to the JSON response
        self.assertQuerySetEqual(actual_save_characters, save_characters, ordered=False)
        self.assertIn(self.save_character1, working_chars)
        self.assertIn(self.save_character2, resting_chars)
        self.assertIn(self.save_character1, working_no_task)
        self.assertIn(self.save_character1, low_energy)
        self.assertIn(self.save_character2, max_energy)
        self.assertQuerySetEqual(
            actual_save_characters_id_list, save_characters_id_list, ordered=False
        )
        self.assertEqual(save, Save.objects.get(pk=self.save.pk))
