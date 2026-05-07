import time

from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth.models import User
from io import StringIO
from projectManagerSim.models import (
    Save, Character, Task, TaskType, 
    SaveCharacter, Decision, Option, CharacterRelationship
)

class SeedDbCommandTest(TestCase):
    """
    Exhaustive test suite for the seed management command.
    Note: TestCase wraps tests in a transaction, but the command 
    itself also uses @transaction.atomic.
    """

    def setUp(self):
        self.out = StringIO()

    def test_command_execution_completes(self):
        """Verify the command runs to completion and outputs the success footer."""
        call_command('seed', stdout=self.out)
        output = self.out.getvalue()
        self.assertIn("SEEDING COMPLETE", output)
        self.assertIn("Users:", output)
        self.assertIn("Characters:", output)

    def test_data_purging(self):
        """Verify the command deletes existing non-superuser data before seeding."""
        User.objects.create(username="obsolete_user", is_superuser=False)
        TaskType.objects.create(task_type_name="OldType")
        
        call_command('seed', stdout=self.out)
        
        self.assertFalse(User.objects.filter(username="obsolete_user").exists())
        self.assertFalse(TaskType.objects.filter(task_type_name="OldType").exists())

    def test_user_privileges(self):
        """Verify that admin and player users have correct permission flags."""
        call_command('seed', stdout=self.out)
        
        admin = User.objects.get(username="admin")
        player1 = User.objects.get(username="player1")
        
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertFalse(player1.is_superuser)
        self.assertFalse(player1.is_staff)

    def test_save_state_distribution(self):
        """
        Verify that each seeded user gets 1 active 
        and 2 inactive saves.
        """
        call_command('seed', stdout=self.out)
        
        p1 = User.objects.get(username="player1")
        p1_saves = Save.objects.filter(user=p1)
        
        self.assertEqual(p1_saves.count(), 3)
        self.assertEqual(p1_saves.filter(active=True).count(), 1)
        self.assertEqual(p1_saves.filter(active=False).count(), 2)

    def test_game_logic_population(self):
        """
        Check that the 'game' service functions (populate_tasks, etc.) 
        actually created related records for the saves.
        """
        call_command('seed', stdout=self.out)
        
        first_save = Save.objects.first()
        print(Decision.objects.filter(game_save=first_save).count())
        self.assertGreater(SaveCharacter.objects.filter(game_save=first_save).count(), 0)
        self.assertGreater(Task.objects.filter(game_save=first_save).count(), 0)

    def test_fixture_loading_integrity(self):
        """
        Make sure the command successfully calls loaddata. 
        """
        call_command('seed', stdout=self.out)
        
        self.assertGreater(Character.objects.count(), 0)
        self.assertGreater(TaskType.objects.count(), 0)