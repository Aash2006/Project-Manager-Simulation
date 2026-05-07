from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projectManagerSim.models import Character, Save, SaveCharacter, Task, TaskType


class SavePrecheckViewTests(TestCase):
    "Testing for save_precheck_view."

    def setUp(self):
        "Regular setup for testing."
        # Creating users
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )

        self.user2 = User.objects.create_user(
            username="testuser2", password="password123"
        )

        # Creating saves
        self.save = Save.objects.create(
            user=self.user,
            save_name="User 1 Test Game",
            progress_percent=50,
            active=True,
        )

        self.save2 = Save.objects.create(
            user=self.user2,
            save_name="User 2 Test Game",
            progress_percent=50,
            active=True,
        )

        # Creating characters
        self.character = Character.objects.create(
            first_name="Alice", last_name="Smith", description="Senior Developer"
        )

        # Create a test task type
        self.task_type = TaskType.objects.create(task_type_name="Backend")

        # Create a test task
        self.first_task = Task.objects.create(
            name="API Development",
            time_to_complete=6,
            task_type=self.task_type,
            unlocks_at_percent=0,
        )

        self.save_character = SaveCharacter.objects.create(
            game_save=self.save,
            character=self.character,
            task_assigned=self.first_task,
            time_remaining_on_task=4,
            current_happiness=85,
            current_energy=100,
            is_resting=True,
            current_effective_productivity=90,
        )

        # User 1's save
        self.url = reverse("save_precheck", args=[self.save.id])

        # User 2's save
        self.url2 = reverse("save_precheck", args=[self.save2.id])

    def test_save_not_found(self):
        """Returns 404 if save does not exist."""
        self.client.login(username="testuser", password="password123")

        response = self.client.get(reverse("save_precheck", args=[9999]))

        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(
            response.content, {"success": False, "message": "Save not found"}
        )

    def test_low_energy_warning(self):
        """Character with low energy triggers warning."""
        self.client.login(username="testuser", password="password123")

        self.save_character.current_energy = 18
        self.save_character.is_resting = False
        self.save_character.task_assigned = self.first_task
        self.save_character.save()

        response = self.client.get(self.url)
        data = response.json()

        self.assertTrue(data["success"])
        self.assertEqual(len(data["character_warnings"]), 1)
        self.assertEqual(data["character_warnings"][0]["type"], "low_energy")

    def test_unassigned_task_warning(self):
        """Character without task triggers warning."""
        self.client.login(username="testuser", password="password123")

        self.save_character.current_energy = 50
        self.save_character.is_resting = False
        self.save_character.task_assigned = None
        self.save_character.save()

        response = self.client.get(self.url)
        data = response.json()

        self.assertTrue(data["success"])
        self.assertEqual(len(data["character_warnings"]), 1)
        self.assertEqual(data["character_warnings"][0]["type"], "unassigned_task")

    def test_multiple_warnings_same_character(self):
        """Character can trigger both low energy and unassigned task."""
        self.client.login(username="testuser", password="password123")

        self.save_character.current_energy = 10
        self.save_character.is_resting = False
        self.save_character.task_assigned = None
        self.save_character.save()

        response = self.client.get(self.url)
        data = response.json()

        self.assertTrue(data["success"])
        self.assertEqual(len(data["character_warnings"]), 2)

        types = set()

        for w in data["character_warnings"]:
            types.add(w["type"])
        self.assertIn("low_energy", types)
        self.assertIn("unassigned_task", types)

    def test_no_warnings(self):
        """No warnings when character is healthy and assigned."""
        self.client.login(username="testuser", password="password123")

        response = self.client.get(self.url)
        data = response.json()

        self.assertTrue(data["success"])
        self.assertEqual(len(data["character_warnings"]), 0)

    def test_save_user_not_equal_to_request_user(self):
        "A different save owner should not match with a different user."
        self.client.login(username="testuser", password="password123")

        response = self.client.get(self.url2)
        data = response.json()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(data, {"success": False, "message": "Not allowed"})
