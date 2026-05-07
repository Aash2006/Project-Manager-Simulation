from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from projectManagerSim.models import Task, TaskType, Save


class TaskModelTestCase(TestCase):
    """Test suite for Task model"""
    
    def setUp(self):
        """Set up test data"""
        user = User.objects.create(username='user', password='password')
        save = Save.objects.create(user=user)
        
        self.task_type = TaskType.objects.create(task_type_name="Frontend")
        self.task = Task.objects.create(
            name="Create Login Page",
            game_save = save,
            time_to_complete=5,
            task_type=self.task_type,
            unlocks_at_percent=0,
            number_of_people_required=2
        )
    
    def test_task_creation(self):
        """Test task is created correctly"""
        self.assertEqual(self.task.name, "Create Login Page")
        self.assertEqual(self.task.time_to_complete, 5)
        self.assertEqual(self.task.task_type, self.task_type)
        self.assertEqual(self.task.unlocks_at_percent, 0)
        self.assertEqual(self.task.number_of_people_required, 2)
    
    def test_task_str_method_returns_name(self):
        """Test __str__ returns task name"""
        self.assertEqual(str(self.task), "Create Login Page")
    
    def test_name_has_max_length_of_100(self):
        """Test name max length is 100"""
        max_length = self.task._meta.get_field('name').max_length
        self.assertEqual(max_length, 100)
    
    def test_time_to_complete_cannot_be_less_than_one(self):
        """Test time_to_complete must be at least 1"""
        task = Task(
            name="Invalid Task",
            time_to_complete=0,
            task_type=self.task_type,
            unlocks_at_percent=3,
        )
        with self.assertRaises(ValidationError):
            task.full_clean()
    
    def test_unlocks_at_percent_cannot_be_negative(self):
        """Test unlocks_at_percent minimum is 0"""
        task = Task(
            name="Invalid Task",
            time_to_complete=5,
            task_type=self.task_type,
            unlocks_at_percent=-1,
        )
        with self.assertRaises(ValidationError):
            task.full_clean()
    
    def test_unlocks_at_percent_cannot_exceed_total_days(self):
        """Test unlocks_at_percent maximum is 100"""
        task = Task(
            name="Invalid Task",
            time_to_complete=5,
            task_type=self.task_type,
            unlocks_at_percent= 101,
        )
        with self.assertRaises(ValidationError):
            task.full_clean()
    
    def test_number_of_people_required_defaults_to_one(self):
        """Test number_of_people_required defaults to 1"""
        task = Task.objects.create(
            name="Solo Task",
            time_to_complete=3,
            task_type=self.task_type,
            unlocks_at_percent=2,
        )
        self.assertEqual(task.number_of_people_required, 1)
    
    def test_number_of_people_required_cannot_be_less_than_one(self):
        """Test number_of_people_required minimum is 1"""
        task = Task(
            name="Invalid Task",
            time_to_complete=5,
            task_type=self.task_type,
            unlocks_at_percent=3,
            number_of_people_required=0,
        )
        with self.assertRaises(ValidationError):
            task.full_clean()
    
    def test_number_of_people_required_cannot_exceed_three(self):
        """Test number_of_people_required maximum is 3"""
        task = Task(
            name="Invalid Task",
            time_to_complete=5,
            task_type=self.task_type,
            unlocks_at_percent=3,
            number_of_people_required=4,
        )
        with self.assertRaises(ValidationError):
            task.full_clean()
    
    def test_task_is_deleted_when_task_type_is_deleted(self):
        """Test task is deleted when task_type is deleted (CASCADE)"""
        task_type_id = self.task_type.id
        self.task_type.delete()
        self.assertFalse(Task.objects.filter(task_type_id=task_type_id).exists())