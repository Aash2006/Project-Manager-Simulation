import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from projectManagerSim.models import Character, Save, SaveCharacter, Task, TaskType


class EdgeCasesTestCase(TestCase):
    """Tests for edge cases and error paths to reach 100% coverage"""
    
    def setUp(self):
        self.url = reverse("start_day")
        
        # User 1
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.save1 = Save.objects.create(
            user=self.user1, save_name="User1 Save", active=True, current_day=1, total_days=15
        )
        
        # User 2 (for permission tests)
        self.user2 = User.objects.create_user(username="user2", password="pass123")
        self.save2 = Save.objects.create(
            user=self.user2, save_name="User2 Save", active=True, current_day=1, total_days=15
        )
        
        self.task_type = TaskType.objects.create(task_type_name="Backend")
        
        self.character = Character.objects.create(
            first_name="Alice", last_name="Test", work_life_balance=50
        )

    def test_wrong_user_permission_error(self):
        """Test that user cannot start day for another user's save"""
        self.client.login(username="user1", password="pass123")
        
        # Try to start day for user2's save
        # GameViewMixin checks for active save first, so this returns 400 (mismatched)
        # not 403 (permission denied) because user1 doesn't have save2 as their active save
        payload = {'save_id': self.save2.id}
        response = self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Mismatched', response.json()['message'])

    def test_mismatched_save_id(self):
        """Test that mismatched save_id returns 400"""
        self.client.login(username="user1", password="pass123")
        
        # Send wrong save_id
        payload = {'save_id': 99999}
        response = self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('Mismatched', response.json()['message'])

    def test_deferral_system_low_energy(self):
        """Test that character with energy ≤30 defers work"""
        self.client.login(username="user1", password="pass123")
        
        task = Task.objects.create(
            name="Test Task", time_to_complete=5, task_type=self.task_type,
            game_save=self.save1, number_of_people_required=1
        )
        
        char = SaveCharacter.objects.create(
            game_save=self.save1, character=self.character,
            task_assigned=task, current_energy=25, is_resting=False
        )
        char.current_energy = 25
        char.save()
        payload = {'save_id': self.save1.id}
        response = self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        data = response.json()
        char_data = next(c for c in data['updated_save_characters'] if c['save_character_id'] == char.id)
        
        char.refresh_from_db()

        self.assertEqual(char_data['progress'], -10)  # Deferral penalty
        self.assertIn('deferred', char_data['warning'])
        self.assertEqual(char.deferral_time, 1)
        

    def test_deferral_reset_after_5_days(self):
        """Test that after 5 days of deferral, energy resets to 50"""
        self.client.login(username="user1", password="pass123")
        
        task = Task.objects.create(
            name="Test Task", time_to_complete=5, task_type=self.task_type,
            game_save=self.save1, number_of_people_required=1
        )
        
        char = SaveCharacter.objects.create(
            game_save=self.save1, character=self.character,
            task_assigned=task, current_energy=20, 
            deferral_time=5, is_resting=False  # Already deferred 5 times
        )
        char.current_energy = 20
        char.save()
        payload = {'save_id': self.save1.id}
        response = self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        char.refresh_from_db()
        self.assertEqual(char.deferral_time, 0)    # Deferral counter reset
        self.assertEqual(char.current_energy, 50)  # Energy reset

    def test_game_ends_at_100_percent_progress(self):
        """Test that game ends when progress reaches 100%"""
        self.client.login(username="user1", password="pass123")
        
        # Create task that will complete and reach 100%
        task = Task.objects.create(
            name="Final Task", time_to_complete=1, task_type=self.task_type,
            game_save=self.save1, number_of_people_required=1,
            days_worked=0, is_completed=False
        )
        
        char = SaveCharacter.objects.create(
            game_save=self.save1, character=self.character,
            task_assigned=task, current_energy=100, is_resting=False
        )
        
        # Set progress to 90% and score high
        self.save1.progress_percent = 90
        self.save1.score = 4000
        self.save1.save()
        
        payload = {'save_id': self.save1.id}
        response = self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        data = response.json()
        
        # Game should end
        self.assertTrue(data['run_finished'])
        self.assertIn('redirect', data)
        response = self.client.get(data['redirect'])
        
        # Save should be completed
        self.save1.refresh_from_db()
        self.assertEqual(self.save1.status, Save.Status.COMPLETED)
        self.assertFalse(self.save1.active)

    def test_resting_character_with_deferral_time(self):
        """Test that resting character's deferral_time decrements"""
        self.client.login(username="user1", password="pass123")
        
        char = SaveCharacter.objects.create(
            game_save=self.save1, character=self.character,
            current_energy=50, is_resting=True, deferral_time=3
        )
        
        payload = {'save_id': self.save1.id}
        response = self.client.post(self.url, json.dumps(payload), content_type='application/json')
        
        char.refresh_from_db()
        self.assertEqual(char.deferral_time, 2)  # Decremented from 3 to 2