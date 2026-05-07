import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projectManagerSim.models import Character, Save, SaveCharacter, Task, TaskType


class DeferralTestCase(TestCase):
    """Tests for the task deferral system where low-energy characters defer work"""

    def setUp(self):
        self.url = reverse("start_day")
        self.user = User.objects.create_user(username="user1", password="pass123")
        self.save = Save.objects.create(
            user=self.user, save_name="Test Save", active=True,
            current_day=1, total_days=15
        )
        self.task_type = TaskType.objects.create(task_type_name="Backend")
        self.character = Character.objects.create(
            first_name="Alice", last_name="Test", work_life_balance=50
        )
        self.character2 = Character.objects.create(
            first_name="Bob", last_name="Builder", work_life_balance=50
        )

    def _post_start_day(self):
        payload = {'save_id': self.save.id}
        return self.client.post(self.url, json.dumps(payload), content_type='application/json')

    def _get_char_data(self, response_data, char_id):
        return next(
            c for c in response_data['updated_save_characters']
            if c['save_character_id'] == char_id
        )

    def test_deferral_increments_from_zero(self):
        """Character with energy <= 30 and deferral_time=0 should defer to 1"""
        self.client.login(username="user1", password="pass123")
        task = Task.objects.create(
            name="Task", time_to_complete=5, task_type=self.task_type,
            game_save=self.save, number_of_people_required=1
        )
        char = SaveCharacter.objects.create(
            game_save=self.save, character=self.character,
            task_assigned=task, current_energy=25, is_resting=False,
            deferral_time=0
        )
        char.current_energy = 25
        char.save()

        response = self._post_start_day()
        data = response.json()
        char_data = self._get_char_data(data, char.id)

        char.refresh_from_db()
        self.assertEqual(char.deferral_time, 1)
        self.assertEqual(char_data['progress'], -10)
        self.assertEqual(char_data['deferral_time'], 1)

    def test_deferral_increments_progressively(self):
        """Deferral_time should increment each day when energy stays low"""
        self.client.login(username="user1", password="pass123")
        task = Task.objects.create(
            name="Task", time_to_complete=10, task_type=self.task_type,
            game_save=self.save, number_of_people_required=1
        )
        char = SaveCharacter.objects.create(
            game_save=self.save, character=self.character,
            task_assigned=task, current_energy=20, is_resting=False,
            deferral_time=3
        )
        char.current_energy = 20
        char.save()

        response = self._post_start_day()
        char.refresh_from_db()

        self.assertEqual(char.deferral_time, 4)

    def test_deferral_at_max_resets_energy(self):
        """After 5 deferrals, energy resets to 50 and deferral_time resets to 0"""
        self.client.login(username="user1", password="pass123")
        task = Task.objects.create(
            name="Task", time_to_complete=5, task_type=self.task_type,
            game_save=self.save, number_of_people_required=1
        )
        char = SaveCharacter.objects.create(
            game_save=self.save, character=self.character,
            task_assigned=task, current_energy=15, is_resting=False,
            deferral_time=5
        )
        char.current_energy = 15
        char.save()

        response = self._post_start_day()
        char.refresh_from_db()

        self.assertEqual(char.deferral_time, 0)
        self.assertEqual(char.current_energy, 50)

    def test_deferral_penalty_in_progress(self):
        """Deferral should give -10 progress penalty"""
        self.client.login(username="user1", password="pass123")
        task = Task.objects.create(
            name="Task", time_to_complete=5, task_type=self.task_type,
            game_save=self.save, number_of_people_required=1
        )
        char = SaveCharacter.objects.create(
            game_save=self.save, character=self.character,
            task_assigned=task, current_energy=10, is_resting=False,
            deferral_time=2
        )
        char.current_energy = 10
        char.save()

        response = self._post_start_day()
        data = response.json()
        char_data = self._get_char_data(data, char.id)

        self.assertEqual(char_data['progress'], -10)

    def test_deferral_reset_gives_zero_progress(self):
        """When deferral resets after 5 days, progress should be 0 (no penalty)"""
        self.client.login(username="user1", password="pass123")
        task = Task.objects.create(
            name="Task", time_to_complete=5, task_type=self.task_type,
            game_save=self.save, number_of_people_required=1
        )
        char = SaveCharacter.objects.create(
            game_save=self.save, character=self.character,
            task_assigned=task, current_energy=20, is_resting=False,
            deferral_time=5
        )
        char.current_energy = 20
        char.save()

        response = self._post_start_day()
        data = response.json()
        char_data = self._get_char_data(data, char.id)

        self.assertEqual(char_data['progress'], 0)

    def test_deferral_warning_message(self):
        """Deferred character should have a warning about deferring"""
        self.client.login(username="user1", password="pass123")
        task = Task.objects.create(
            name="Task", time_to_complete=5, task_type=self.task_type,
            game_save=self.save, number_of_people_required=1
        )
        char = SaveCharacter.objects.create(
            game_save=self.save, character=self.character,
            task_assigned=task, current_energy=30, is_resting=False,
            deferral_time=0
        )
        char.current_energy = 30
        char.save()

        response = self._post_start_day()
        data = response.json()
        char_data = self._get_char_data(data, char.id)

        self.assertIn('deferred', char_data['warning'])

    def test_resting_character_deferral_decrements(self):
        """Resting character's deferral_time should decrement by 1"""
        self.client.login(username="user1", password="pass123")
        char = SaveCharacter.objects.create(
            game_save=self.save, character=self.character,
            current_energy=50, is_resting=True, deferral_time=4
        )

        response = self._post_start_day()
        char.refresh_from_db()

        self.assertEqual(char.deferral_time, 3)

    def test_resting_character_deferral_does_not_go_below_zero(self):
        """Resting character with deferral_time=0 should stay at 0"""
        self.client.login(username="user1", password="pass123")
        char = SaveCharacter.objects.create(
            game_save=self.save, character=self.character,
            current_energy=50, is_resting=True, deferral_time=0
        )

        response = self._post_start_day()
        char.refresh_from_db()

        self.assertEqual(char.deferral_time, 0)

    def test_high_energy_character_does_not_defer(self):
        """Character with energy > 30 should NOT defer"""
        self.client.login(username="user1", password="pass123")
        task = Task.objects.create(
            name="Task", time_to_complete=5, task_type=self.task_type,
            game_save=self.save, number_of_people_required=1
        )
        char = SaveCharacter.objects.create(
            game_save=self.save, character=self.character,
            task_assigned=task, current_energy=80, is_resting=False,
            deferral_time=0
        )

        response = self._post_start_day()
        data = response.json()
        char_data = self._get_char_data(data, char.id)

        char.refresh_from_db()
        self.assertEqual(char.deferral_time, 0)
        self.assertNotEqual(char_data['progress'], -10)

    def test_deferral_time_in_response(self):
        """Response should include deferral_time for each character"""
        self.client.login(username="user1", password="pass123")
        task = Task.objects.create(
            name="Task", time_to_complete=5, task_type=self.task_type,
            game_save=self.save, number_of_people_required=1
        )
        char = SaveCharacter.objects.create(
            game_save=self.save, character=self.character,
            task_assigned=task, current_energy=25, is_resting=False,
            deferral_time=2
        )
        char.current_energy = 25
        char.save()

        response = self._post_start_day()
        data = response.json()
        char_data = self._get_char_data(data, char.id)

        self.assertIn('deferral_time', char_data)
        self.assertEqual(char_data['deferral_time'], 3)

    def test_energy_at_boundary_30_triggers_deferral(self):
        """Character with exactly 30 energy should defer (energy <= 30)"""
        self.client.login(username="user1", password="pass123")
        task = Task.objects.create(
            name="Task", time_to_complete=5, task_type=self.task_type,
            game_save=self.save, number_of_people_required=1
        )
        char = SaveCharacter.objects.create(
            game_save=self.save, character=self.character,
            task_assigned=task, current_energy=30, is_resting=False,
            deferral_time=0
        )
        char.current_energy = 30
        char.save()

        response = self._post_start_day()
        char.refresh_from_db()

        self.assertEqual(char.deferral_time, 1)

    def test_energy_at_boundary_31_does_not_defer(self):
        """Character with 31 energy should NOT defer"""
        self.client.login(username="user1", password="pass123")
        task = Task.objects.create(
            name="Task", time_to_complete=5, task_type=self.task_type,
            game_save=self.save, number_of_people_required=1
        )
        char = SaveCharacter.objects.create(
            game_save=self.save, character=self.character,
            task_assigned=task, current_energy=31, is_resting=False,
            deferral_time=0
        )
        char.current_energy = 31
        char.save()

        response = self._post_start_day()
        char.refresh_from_db()

        self.assertEqual(char.deferral_time, 0)
