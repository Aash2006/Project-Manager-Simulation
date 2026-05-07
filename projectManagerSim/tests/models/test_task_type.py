from django.test import TestCase
from django.db import IntegrityError
from projectManagerSim.models import TaskType


class TaskTypeModelTestCase(TestCase):
    """Test suite for TaskType model"""
    
    def setUp(self):
        """Set up test data"""
        self.task_type = TaskType.objects.create(
            task_type_name="Backend Development"
        )
    
    def test_task_type_creation(self):
        """Test task type is created correctly"""
        self.assertEqual(self.task_type.task_type_name, "Backend Development")
    
    def test_task_type_str_method_returns_task_type_name(self):
        """Test __str__ returns task type name"""
        self.assertEqual(str(self.task_type), "Backend Development")
    
    def test_task_type_name_has_max_length_of_50(self):
        """Test task_type_name max length is 50"""
        max_length = self.task_type._meta.get_field('task_type_name').max_length
        self.assertEqual(max_length, 50)
    
    def test_task_type_name_must_be_unique(self):
        """Test task_type_name must be unique"""
        with self.assertRaises(IntegrityError):
            TaskType.objects.create(task_type_name="Backend Development")