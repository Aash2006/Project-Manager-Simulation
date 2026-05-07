import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projectManagerSim.models import Character, Save, SaveCharacter, Task, TaskType


class ProgressCalculationTestCase(TestCase):
    """Tests for task-based progress bar"""
    
    def setUp(self):
        self.url = reverse("start_day")
        self.user = User.objects.create_user(username="test_user", password="test_pass123")
        
        self.game_save = Save.objects.create(
            user=self.user, save_name="Test", active=True, 
            current_day=1, total_days=15, progress_percent=0
        )
        
        self.task_type = TaskType.objects.create(task_type_name="Backend")
        
        # Create 10 tasks
        self.tasks = []
        for i in range(10):
            task = Task.objects.create(
                name=f"Task {i+1}",
                time_to_complete=1,
                task_type=self.task_type,
                game_save=self.game_save,
                number_of_people_required=1,
                days_worked=0
            )
            self.tasks.append(task)
        
        self.char = Character.objects.create(
            first_name="Alice", last_name="Test", work_life_balance=50
        )
        
        self.save_char = SaveCharacter.objects.create(
            game_save=self.game_save,
            character=self.char,
            task_assigned=self.tasks[0],
            current_energy=100,
            is_resting=False
        )
        
        self.client.login(username="test_user", password="test_pass123")

    def test_progress_starts_at_zero(self):
        """Test that progress is 0% with no completed tasks"""
        self.game_save.refresh_from_db()
        self.assertEqual(self.game_save.progress_percent, 0)

    def test_progress_after_one_completion(self):
        """Test that completing 1/10 tasks = 10% progress"""
        payload = {'save_id': self.game_save.id}
        self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        self.game_save.refresh_from_db()
        self.assertEqual(self.game_save.progress_percent, 10)

    def test_progress_at_50_percent(self):
        """Test that completing 5/10 tasks = 50% progress"""
        for task in self.tasks[:5]:
            task.is_completed = True
            task.save()
        
        payload = {'save_id': self.game_save.id}
        self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        self.game_save.refresh_from_db()
        self.assertEqual(self.game_save.progress_percent, 50)

    def test_progress_at_100_percent(self):
        """Test that completing all tasks = 100% progress"""
        for task in self.tasks:
            task.is_completed = True
            task.save()
        
        payload = {'save_id': self.game_save.id}
        response = self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        self.game_save.refresh_from_db()
        self.assertEqual(self.game_save.progress_percent, 100)