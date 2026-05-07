from django.contrib.auth.models import User
from django.test import TestCase

from projectManagerSim.models import Character, Save, SaveCharacter, Task, TaskType
from projectManagerSim.services.game.task_progress_service import TaskProgressService, TaskCompletion


class TaskProgressServiceTestCase(TestCase):
    """Unit tests for TaskProgressService business logic"""
    
    def setUp(self):
        # Create minimal database objects
        self.user = User.objects.create_user(username="testuser", password="pass123")
        self.save = Save.objects.create(
            user=self.user, save_name="Test", active=True
        )
        self.task_type = TaskType.objects.create(task_type_name="Backend")
        self.task = Task.objects.create(
            name="Test Task",
            time_to_complete=5,
            task_type=self.task_type,
            game_save=self.save,
            number_of_people_required=2,
            days_worked=0,
            is_completed=False
        )
        
        # Create workers
        self.workers = []
        for i in range(3):
            char = Character.objects.create(
                first_name=f"Worker{i}", last_name="Test", work_life_balance=50
            )
            worker = SaveCharacter.objects.create(
                game_save=self.save, character=char,
                task_assigned=self.task, current_energy=100
            )
            self.workers.append(worker)
        
        self.task_workers = self.workers
    
    # ========== Correctly Staffed Tests ==========
    
    def test_advance_task_correctly_staffed_high_energy(self):
        """Test advancing task with correct team size and high energy"""
        service = TaskProgressService(self.task, team_size=2, required_size=2, task_workers=self.task_workers)
        
        is_complete, completion = service.advance_task(is_first_worker=True, high_energy=True)
        
        self.assertFalse(is_complete)
        self.assertIsNone(completion)
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 1.0)
        self.assertFalse(self.task.is_completed)
    
    def test_advance_task_correctly_staffed_low_energy(self):
        """Test advancing task with correct team size and low energy - rounds to int"""
        service = TaskProgressService(self.task, team_size=2, required_size=2, task_workers=self.task_workers)
        
        is_complete, completion = service.advance_task(is_first_worker=True, high_energy=False)
        
        self.task.refresh_from_db()
        # 0.5 rounds down to 0 (IntegerField)
        self.assertEqual(self.task.days_worked, 0)
    
    def test_advance_task_not_first_worker(self):
        """Test that non-first worker doesn't advance task"""
        service = TaskProgressService(self.task, team_size=2, required_size=2, task_workers=self.task_workers)
        
        is_complete, completion = service.advance_task(is_first_worker=False, high_energy=True)
        
        self.assertFalse(is_complete)
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 0)  # No change
    
    # ========== Understaffed Tests ==========
    
    def test_advance_task_understaffed_no_progress(self):
        """Test that understaffed task makes no progress"""
        service = TaskProgressService(self.task, team_size=1, required_size=2, task_workers=self.task_workers)
        
        is_complete, completion = service.advance_task(is_first_worker=True, high_energy=True)
        
        self.assertFalse(is_complete)
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 0)
    
    # ========== Overstaffed Tests ==========
    
    def test_advance_task_overstaffed_by_one(self):
        """Test overstaffing by 1 worker - rounds to int"""
        service = TaskProgressService(self.task, team_size=3, required_size=2, task_workers=self.task_workers)
        
        is_complete, completion = service.advance_task(is_first_worker=True, high_energy=True)
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 2)
    
    def test_advance_task_overstaffed_by_two(self):
        """Test overstaffing by 2 workers - capped at 3x speed"""
        service = TaskProgressService(self.task, team_size=4, required_size=2, task_workers=self.task_workers)
        
        is_complete, completion = service.advance_task(is_first_worker=True, high_energy=True)
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 3)
    
    def test_advance_task_overstaffed_extreme(self):
        """Test extreme overstaffing"""
        service = TaskProgressService(self.task, team_size=20, required_size=2, task_workers=self.task_workers)
        
        is_complete, completion = service.advance_task(is_first_worker=True, high_energy=True)
        
        self.task.refresh_from_db()

        self.assertEqual(self.task.days_worked, 3.0)
    
    def test_advance_task_overstaffed_low_energy(self):
        """Test overstaffing with low energy"""
        service = TaskProgressService(self.task, team_size=3, required_size=2, task_workers=self.task_workers)
        
        is_complete, completion = service.advance_task(is_first_worker=True, high_energy=False)
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 1)
    
    def test_advance_task_overstaffed_low_energy_extreme(self):
        """Test extreme overstaffing with low energy"""
        service = TaskProgressService(self.task, team_size=20, required_size=2, task_workers=self.task_workers)
        
        is_complete, completion = service.advance_task(is_first_worker=True, high_energy=False)
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 2)
    
    # ========== Task Completion Tests ==========
    
    def test_advance_task_completes_exactly(self):
        """Test task completes when days_worked reaches time_to_complete"""
        self.task.days_worked = 4.0
        self.task.save()
        
        service = TaskProgressService(self.task, team_size=2, required_size=2, task_workers=self.task_workers)
        
        is_complete, completion = service.advance_task(is_first_worker=True, high_energy=True)
        
        self.assertTrue(is_complete)
        self.assertIsNotNone(completion)
        self.assertIsInstance(completion, TaskCompletion)
        self.assertEqual(completion.name, "Test Task")
        self.assertEqual(completion.character, "Team of 2")
        self.assertEqual(completion.days_taken, 5.0)
        
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)
        self.assertEqual(self.task.days_worked, 5.0)
    
    def test_advance_task_completes_exceeds(self):
        """Test task completes when days_worked exceeds time_to_complete"""
        self.task.days_worked = 3
        self.task.time_to_complete = 5
        self.task.save()
        
        service = TaskProgressService(self.task, team_size=10, required_size=2, task_workers=self.task_workers)
        is_complete, completion = service.advance_task(is_first_worker=True, high_energy=True)
        
        self.assertTrue(is_complete)
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 6)
        self.assertTrue(self.task.is_completed)
    
    def test_task_completion_auto_unassigns_workers(self):
        """Test that all workers are unassigned when task completes"""
        self.task.days_worked = 4.0
        self.task.save()
        
        # Verify all workers are assigned
        for worker in self.workers:
            self.assertEqual(worker.task_assigned, self.task)
        
        service = TaskProgressService(self.task, team_size=2, required_size=2, task_workers=self.task_workers)
        is_complete, completion = service.advance_task(is_first_worker=True, high_energy=True)
        
        self.assertTrue(is_complete)
        
        # Verify all workers are unassigned
        for worker in self.workers:
            worker.refresh_from_db()
            self.assertIsNone(worker.task_assigned)
    
    def test_task_completion_info_correct(self):
        """Test that TaskCompletion contains correct information"""
        self.task.days_worked = 4.5
        self.task.save()
        
        service = TaskProgressService(self.task, team_size=3, required_size=2, task_workers=self.task_workers)
        is_complete, completion = service.advance_task(is_first_worker=True, high_energy=True)
        
        self.assertTrue(is_complete)
        self.assertEqual(completion.name, "Test Task")
        self.assertEqual(completion.character, "Team of 3")
        self.assertEqual(completion.days_taken, 6.5)
    
    # ========== Calculate Days Increment Tests ==========
    
    def test_calculate_days_increment_correctly_staffed_high_energy(self):
        """Test days increment calculation for correctly staffed, high energy"""
        service = TaskProgressService(self.task, team_size=2, required_size=2, task_workers=self.task_workers)
        
        increment = service._calculate_days_increment(high_energy=True)
        
        self.assertEqual(increment, 1.0)
    
    def test_calculate_days_increment_correctly_staffed_low_energy(self):
        """Test days increment calculation for correctly staffed, low energy"""
        service = TaskProgressService(self.task, team_size=2, required_size=2, task_workers=self.task_workers)
        
        increment = service._calculate_days_increment(high_energy=False)
        
        self.assertEqual(increment, 0)
    
    def test_calculate_days_increment_overstaffed_diminishing_returns(self):
        """Test that overstaffing has diminishing returns (0.5 per worker)"""
        # 1 extra worker
        service = TaskProgressService(self.task, team_size=3, required_size=2, task_workers=self.task_workers)
        self.assertEqual(service._calculate_days_increment(high_energy=True), 2)

        # 2 extra workers
        service = TaskProgressService(self.task, team_size=4, required_size=2, task_workers=self.task_workers)
        self.assertEqual(service._calculate_days_increment(high_energy=True), 3)

        # 2+ extra workers
        service = TaskProgressService(self.task, team_size=5, required_size=2, task_workers=self.task_workers)
        self.assertEqual(service._calculate_days_increment(high_energy=True), 3)
    
    def test_calculate_days_increment_low_energy_caps_at_2x(self):
        """Test that low energy overstaffing caps at 2x speed"""
        # Extreme overstaffing with low energy
        service = TaskProgressService(self.task, team_size=10, required_size=2, task_workers=self.task_workers)
        
        increment = service._calculate_days_increment(high_energy=False)
        
        self.assertEqual(increment, 2)
    
    # ========== Edge Cases ==========
    
    def test_advance_task_multiple_times(self):
        """Test advancing task multiple times accumulates correctly"""
        service = TaskProgressService(self.task, team_size=2, required_size=2, task_workers=self.task_workers)
        
        # First advance
        service.advance_task(is_first_worker=True, high_energy=True)
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 1.0)
        
        # Second advance (need new service instance after refresh)
        service = TaskProgressService(self.task, team_size=2, required_size=2, task_workers=self.task_workers)
        service.advance_task(is_first_worker=True, high_energy=True)
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 2.0)
    
    def test_advance_task_with_fractional_time_to_complete(self):
        """Test task with integer-only days_worked"""
        self.task.time_to_complete = 3
        self.task.days_worked = 1
        self.task.save()
        
        service = TaskProgressService(self.task, team_size=3, required_size=2, task_workers=self.task_workers)
        is_complete, completion = service.advance_task(is_first_worker=True, high_energy=True)
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.days_worked, 3)