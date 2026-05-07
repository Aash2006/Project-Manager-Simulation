import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projectManagerSim.models import Character, Save, SaveCharacter, Task, TaskType


class ToggleRestingViewTestCase(TestCase):

    def setUp(self):
        # User setup
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.other_user = User.objects.create_user(
            username="testuser2", password="testpass123"
        )

        # Character setup
        self.character = Character.objects.create(
            first_name="Alice", last_name="Developer", description="Senior developer"
        )

        # Save setup (called game_save because another model uses it as game_save)
        self.game_save = Save.objects.create(
            user=self.user, save_name="Test Game", active=True
        )

        self.other_game_save = Save.objects.create(
            user=self.other_user, save_name="Test Game", active=True
        )

        # Task setup
        self.task_type = TaskType.objects.create(task_type_name="Backend")

        self.task = Task.objects.create(
            name="API Development",
            time_to_complete=6,
            task_type=self.task_type,
            unlocks_at_percent=0,
        )
        self.first_task = Task.objects.create(
            name="API Development",
            time_to_complete=6,
            task_type=self.task_type,
            unlocks_at_percent=0,
        )
        self.save_character = SaveCharacter.objects.create(
            game_save=self.game_save,
            character=self.character,
            task_assigned=self.task,
            time_remaining_on_task=4,
            current_happiness=85,
            current_energy=70,
            current_effective_productivity=90,
        )

        self.other_save_character = SaveCharacter.objects.create(
            game_save=self.other_game_save,
            character=self.character,
            task_assigned=self.task,
            time_remaining_on_task=4,
            current_happiness=85,
            current_energy=70,
            current_effective_productivity=90,
        )

        # URL
        self.url = reverse("toggle_resting")

    def test_toggle_resting_false(self):
        self.client.login(username="testuser", password="testpass123")

        payload = {
            "save_character_id": self.save_character.id,
            "is_resting": False,
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("character_card_html", data)

        self.save_character.refresh_from_db()
        self.assertEqual(self.save_character.is_resting, False)

    def test_toggle_resting_true(self):
        self.client.login(username="testuser", password="testpass123")

        payload = {
            "save_character_id": self.save_character.id,
            "is_resting": True,
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_CSRFTOKEN="testtoken",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("character_card_html", data)

        self.save_character.refresh_from_db()
        self.assertEqual(self.save_character.is_resting, True)

    def test_toggle_resting_not_our_character(self):
        self.client.login(username="testuser", password="testpass123")

        payload = {
            "save_character_id": self.other_save_character.id,
            "is_resting": True,
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_CSRFTOKEN="testtoken",
        )

        self.assertEqual(response.status_code, 403)

        data = response.json()
        self.assertFalse(data["success"])

    def test_toggle_resting_invalid_character_id(self):
        self.client.login(username="testuser", password="testpass123")

        payload = {
            "save_character_id": 999999,
            "is_resting": True,
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_CSRFTOKEN="testtoken",
        )

        self.assertEqual(response.status_code, 404)

        data = response.json()
        self.assertFalse(data["success"])

    def test_toggle_resting_missing_character_id(self):
        self.client.login(username="testuser", password="testpass123")

        payload = {
            "is_resting": True,
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_CSRFTOKEN="testtoken",
        )

        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertFalse(data["success"])

    def test_toggle_resting_missing_is_resting(self):
        self.client.login(username="testuser", password="testpass123")

        payload = {
            "save_character_id": 999999,
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_CSRFTOKEN="testtoken",
        )

        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertFalse(data["success"])

    def test_toggle_resting_invalid_payload(self):
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            self.url,
            data='{"save_character_id": 1, "is_resting": true',
            content_type="application/json",
            HTTP_X_CSRFTOKEN="testtoken",
        )

        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertFalse(data["success"])

    @patch("projectManagerSim.views.toggle_resting_view.SaveCharacter.save")
    def test_unexpected_exception_returns_500(self, mock_save):
        self.client.login(username="testuser", password="testpass123")

        mock_save.side_effect = Exception("Something broke")

        payload = {"save_character_id": self.save_character.id, "is_resting": True}

        response = self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )

        self.assertEqual(response.status_code, 500)

        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Something broke")
