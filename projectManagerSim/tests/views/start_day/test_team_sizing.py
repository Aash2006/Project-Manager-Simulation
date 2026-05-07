import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projectManagerSim.models import Character, Save, SaveCharacter, Task, TaskType


class TeamSizingTestCase(TestCase):
    """Tests for team size requirements (understaffed/correctly staffed/overstaffed)"""
    
    def setUp(self):
        self.url = reverse("start_day")
        self.user = User.objects.create_user(username="test_user", password="test_pass123")
        
        self.game_save = Save.objects.create(
            user=self.user, save_name="Test", active=True, current_day=1, total_days=15
        )
        
        self.task_type = TaskType.objects.create(task_type_name="Backend")
        
        # Task requiring 2 people
        self.task = Task.objects.create(
            name="Team Task",
            time_to_complete=10,
            task_type=self.task_type,
            game_save=self.game_save,
            number_of_people_required=2,
            days_worked=0
        )
        
        self.client.login(username="test_user", password="test_pass123")

    def create_worker(self, name, energy=100):
        """Helper to create a worker character"""
        char = Character.objects.create(
            first_name=name, last_name="Test", work_life_balance=50, initial_energy=energy
        )
        return SaveCharacter.objects.create(
            game_save=self.game_save,
            character=char,
            task_assigned=self.task,
            current_energy=energy,
            is_resting=False
        )

    def test_understaffed_no_progress(self):
        """Test that understaffed task makes no progress"""
        self.create_worker("Alice")
        
        payload = {'save_id': self.game_save.id}
        response = self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 0)
        
        data = response.json()
        char_data = data['updated_save_characters'][0]
        self.assertIn('understaffed', char_data['warning'].lower())

    def test_correctly_staffed_normal_progress(self):
        """Test that correctly staffed task progresses normally"""
        self.create_worker("Alice")
        self.create_worker("Bob")
        
        payload = {'save_id': self.game_save.id}
        self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 1)

    def test_overstaffed_accelerated_progress(self):
        """Test that overstaffing accelerates progress with diminishing returns"""
        self.create_worker("Alice")
        self.create_worker("Bob")
        self.create_worker("Charlie")
        
        payload = {'save_id': self.game_save.id}
        self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        self.task.refresh_from_db()

        self.assertGreaterEqual(self.task.days_worked, 1.0)
        self.assertLessEqual(self.task.days_worked, 3.0)

    def test_overstaffed_capped_at_3x_speed(self):
        """Test that overstaffing bonus is capped at 3× speed"""
        for i in range(10):
            self.create_worker(f"Worker{i}")
        
        payload = {'save_id': self.game_save.id}    
        self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 3.0)

    def test_overstaffed_higher_energy_cost(self):
        """Test that overstaffing increases energy drain"""
        worker1 = self.create_worker("Alice", energy=100)
        self.create_worker("Bob", energy=100)
        self.create_worker("Charlie", energy=100)
        
        payload = {'save_id': self.game_save.id}
        self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        worker1.refresh_from_db()
        
        self.assertEqual(worker1.current_energy, 80)