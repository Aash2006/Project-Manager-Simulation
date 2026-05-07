from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from projectManagerSim.models import Save, Task, TaskType


class SaveModelTestCase(TestCase):
    """Test suite for Save model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.task_type = TaskType.objects.create(task_type_name="Testing")
        self.task = Task.objects.create(
            name="Write Tests",
            time_to_complete=8,
            task_type=self.task_type,
            unlocks_at_percent=0,
        )
        self.save = Save.objects.create(
            user=self.user,
            save_name="Test Save",
            progress_percent=50,
            current_day=10,
            score=85
        )

    def test_save_creation(self):
        """Test save is created correctly"""
        self.assertEqual(self.save.save_name, "Test Save")
        self.assertEqual(self.save.progress_percent, 50)
        self.assertEqual(self.save.current_day, 10)
        self.assertEqual(self.save.score, 85)

    def test_save_str_method_returns_save_name_and_username(self):
        """Test __str__ returns correct format"""
        self.assertEqual(str(self.save), "Test Save - testuser")

    def test_status_defaults_to_ongoing(self):
        """Test status defaults to ONGOING"""
        save = Save.objects.create(user=self.user, save_name="New Save")
        self.assertEqual(save.status, Save.Status.ONGOING)

    def test_status_can_be_set_to_completed(self):
        """Test status can be set to COMPLETED"""
        self.save.status = Save.Status.COMPLETED
        self.save.save()
        self.assertEqual(self.save.status, Save.Status.COMPLETED)

    def test_progress_percent_defaults_to_zero(self):
        """Test progress_percent defaults to 0"""
        save = Save.objects.create(user=self.user, save_name="New")
        self.assertEqual(save.progress_percent, 0)

    def test_progress_percent_cannot_be_negative(self):
        """Test progress_percent minimum is 0"""
        save = Save(user=self.user, save_name="Invalid", progress_percent=-1)
        with self.assertRaises(ValidationError):
            save.full_clean()

    def test_progress_percent_cannot_exceed_100(self):
        """Test progress_percent maximum is 100"""
        save = Save(user=self.user, save_name="Invalid", progress_percent=101)
        with self.assertRaises(ValidationError):
            save.full_clean()

    def test_current_day_defaults_to_one(self):
        """Test current_day defaults to 1"""
        save = Save.objects.create(user=self.user, save_name="New")
        self.assertEqual(save.current_day, 1)

    def test_current_day_cannot_be_negative(self):
        """Test current_day minimum is 0"""
        save = Save(user=self.user, save_name="Invalid", current_day=-1)
        with self.assertRaises(ValidationError):
            save.full_clean()

    def test_score_defaults_to_zero(self):
        """Test score defaults to 0"""
        save = Save.objects.create(user=self.user, save_name="New")
        self.assertEqual(save.score, 0)


    def test_started_at_is_set_automatically(self):
        """Test started_at is automatically set on creation"""
        self.assertIsNotNone(self.save.started_at)

    def test_last_used_is_not_updated_automatically(self):
        """Test last_used is not modified by model save — it is only set explicitly via the game dashboard"""
        self.save.progress_percent = 60
        self.save.save()
        self.assertIsNone(self.save.last_used)

    def test_different_users_can_have_same_save_name(self):
        """Test different users can use the same save name"""
        user2 = User.objects.create_user(username="user2", password="pass")
        save2 = Save.objects.create(user=user2, save_name="Test Save")
        self.assertEqual(save2.save_name, self.save.save_name)

    def test_saves_are_ordered_by_last_used_descending(self):
        """Test saves are ordered by last_used in descending order"""
        save2 = Save.objects.create(user=self.user, save_name="Older Save")

        self.save.progress_percent = 60
        self.save.save()

        saves = list(Save.objects.all())
        self.assertEqual(saves[0], self.save)
        self.assertEqual(saves[1], save2)

    def test_save_is_deleted_when_user_is_deleted(self):
        """Test save is deleted when user is deleted (CASCADE)"""
        save_id = self.save.id
        self.user.delete()
        self.assertFalse(Save.objects.filter(id=save_id).exists())
