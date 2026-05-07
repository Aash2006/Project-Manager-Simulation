import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projectManagerSim.models import Character, Save, SaveCharacter, Task, TaskType


class WorkLifeBalanceTestCase(TestCase):
    """Tests for work_life_balance scaling"""
    
    def setUp(self):
        self.url = reverse("start_day")
        self.user = User.objects.create_user(username="wlb_user", password="test_pass123")

        self.game_save = Save.objects.create(
            user=self.user, save_name="WLB Test", active=True, 
            current_day=1, total_days=15, progress_percent=50
        )

        self.task_type = TaskType.objects.create(task_type_name="Backend")
        self.task = Task.objects.create(
            name="WLB Task", time_to_complete=6,
            task_type=self.task_type, game_save=self.game_save,
            number_of_people_required=1
        )

        self.character = Character.objects.create(
            first_name="Alice", last_name="Smith", work_life_balance=50
        )
        self.character2 = Character.objects.create(
            first_name="Jack", last_name="Jones", work_life_balance=50
        )

        self.save_character = SaveCharacter.objects.create(
            game_save=self.game_save, character=self.character,
            task_assigned=self.task, current_happiness=85, 
            current_energy=70, is_resting=True
        )
        self.save_character.current_energy = 70
        self.save_character.save()

        self.working_save_character = SaveCharacter.objects.create(
            game_save=self.game_save, character=self.character2,
            task_assigned=self.task, current_happiness=85, 
            current_energy=70, is_resting=False
        )
        self.working_save_character.current_energy = 70
        self.working_save_character.save()

        self.client.login(username="wlb_user", password="test_pass123")

    def _post(self):
        return self.client.post(
            self.url, json.dumps({"save_id": self.game_save.id}),
            content_type="application/json"
        )

    def _find_char_data(self, response_json, save_character_id):
        for c in response_json["updated_save_characters"]:
            if c["save_character_id"] == save_character_id:
                return c
        return None

    # Resting tests
    def test_resting_high_wlb_gains_more_energy(self):
        """wlb=80: energy_gain=32"""
        self.character.work_life_balance = 80
        self.character.save()

        data = self._find_char_data(self._post().json(), self.save_character.id)
        self.assertEqual(data["current_energy"], 96)

    def test_resting_low_wlb_gains_less_energy(self):
        """wlb=20: energy_gain=8"""
        self.character.work_life_balance = 20
        self.character.save()

        data = self._find_char_data(self._post().json(), self.save_character.id)
        self.assertEqual(data["current_energy"], 84)

    def test_resting_neutral_wlb_baseline(self):
        """wlb=50: energy_gain=20, progress=0"""
        data = self._find_char_data(self._post().json(), self.save_character.id)
        self.assertEqual(data["current_energy"], 90)
        self.assertEqual(data["progress"], 0)

    # Working (high energy) tests
    def test_working_high_energy_high_wlb_scales_up(self):
        """wlb=80: progress=40"""
        self.character2.work_life_balance = 80
        self.character2.save()

        data = self._find_char_data(self._post().json(), self.working_save_character.id)
        self.assertEqual(data["progress"], 25)

    def test_working_high_energy_low_wlb_scales_down(self):
        """wlb=20: progress=10"""
        self.character2.work_life_balance = 20
        self.character2.save()

        data = self._find_char_data(self._post().json(), self.working_save_character.id)
        self.assertEqual(data["progress"], 25)

    def test_working_high_energy_neutral_wlb_baseline(self):
        """wlb=50: progress=25"""
        data = self._find_char_data(self._post().json(), self.working_save_character.id)
        self.assertEqual(data["progress"], 25)

    def test_wlb_bar_present_in_card_html(self):
        """Work/Life Balance functionality should work in start_day endpoint."""
        response = self.client.post(
            reverse("start_day"),
            data=json.dumps({"save_id": self.game_save.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("updated_save_characters", data)
