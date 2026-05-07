import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projectManagerSim.models import Character, Save, SaveCharacter, Task, TaskType


class TaskCompletionTestCase(TestCase):
    """Tests for task completion and days_worked progression"""
    
    def setUp(self):
        self.url = reverse("start_day")
        self.user = User.objects.create_user(username="test_user", password="test_pass123")
        
        self.character = Character.objects.create(
            first_name="Alice", last_name="Smith", work_life_balance=50
        )
        
        self.game_save = Save.objects.create(
            user=self.user, save_name="Test", active=True, current_day=1, total_days=15
        )
        
        self.task_type = TaskType.objects.create(task_type_name="Backend")
        

        self.task = Task.objects.create(
            name="Quick Task",
            time_to_complete=3,
            task_type=self.task_type,
            game_save=self.game_save,
            number_of_people_required=1,
            days_worked=0,
            is_completed=False
        )
        

        self.task2 = Task.objects.create(
            name="Second Task",
            time_to_complete=5,
            task_type=self.task_type,
            game_save=self.game_save,
            number_of_people_required=1,
            days_worked=0,
            is_completed=False
        )
        
        self.task3 = Task.objects.create(
            name="Third Task",
            time_to_complete=5,
            task_type=self.task_type,
            game_save=self.game_save,
            number_of_people_required=1,
            days_worked=0,
            is_completed=False
        )
        
        self.save_char = SaveCharacter.objects.create(
            game_save=self.game_save,
            character=self.character,
            task_assigned=self.task,
            current_energy=100,
            is_resting=False
        )
        
        self.client.login(username="test_user", password="test_pass123")

    def test_task_progresses_by_one_day(self):
        """Test that task days_worked increments by 1"""
        payload = {'save_id': self.game_save.id}
        self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 1)
        self.assertFalse(self.task.is_completed)

    def test_task_completes_after_sufficient_days(self):
        """Test that task completes when days_worked >= time_to_complete"""
        self.task.days_worked = 2
        self.task.save()
        
        payload = {'save_id': self.game_save.id}
        response = self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 3)
        self.assertTrue(self.task.is_completed)
        
        data = response.json()
        # Check completed_tasks exists and has content
        self.assertIn('completed_tasks', data)
        self.assertEqual(len(data['completed_tasks']), 1)
        self.assertEqual(data['completed_tasks'][0]['name'], 'Quick Task')

    def test_completed_task_auto_unassigns_worker(self):
        """Test that workers are auto-unassigned when task completes"""
        self.task.days_worked = 2
        self.task.save()
        
        payload = {'save_id': self.game_save.id}
        self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        self.save_char.refresh_from_db()
        self.assertIsNone(self.save_char.task_assigned)