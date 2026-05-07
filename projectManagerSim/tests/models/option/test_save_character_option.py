from django.test import TestCase
from django.contrib.auth.models import User
from projectManagerSim.models.save import Save
from projectManagerSim.models.character import Character
from projectManagerSim.models.save_character import SaveCharacter
from projectManagerSim.models.task import Task
from projectManagerSim.models.task_type import TaskType
from projectManagerSim.models.decisions.decision import Decision
from projectManagerSim.models.decisions.save_character_option import SaveCharacterOption

class SaveCharacterOptionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="pookie")
        self.game_save = Save.objects.create(user=self.user, save_name="W Save")
        
        self.char_alice = Character.objects.create(first_name="Alice", initial_energy=100, initial_happiness=50)
        self.sc_alice = SaveCharacter.objects.create(game_save=self.game_save, character=self.char_alice)
        
        self.char_bob = Character.objects.create(first_name="Bob", initial_energy=100)
        self.sc_bob = SaveCharacter.objects.create(game_save=self.game_save, character=self.char_bob)

        self.decision = Decision.objects.create(game_save=self.game_save, title="Alice's Thingy")
        self.task_type = TaskType.objects.create(task_type_name="Bugfixing")
        self.special_task = Task.objects.create(
            name="Very Important Patch", 
            game_save=self.game_save, 
            task_type=self.task_type, 
            time_to_complete=2
        )

    def test_apply_affects_only_target_character(self):
        """Verify that multipliers only apply to the specific save_character linked."""
        option = SaveCharacterOption.objects.create(
            decision=self.decision,
            save_character=self.sc_alice,
            energy_effect=0.5,
            happiness_effect=1.4
        )

        option.apply()
        
        self.sc_alice.refresh_from_db()
        self.sc_bob.refresh_from_db()

        self.assertEqual(self.sc_alice.current_energy, 50)
        self.assertEqual(self.sc_alice.current_happiness, 70)
        
        self.assertEqual(self.sc_bob.current_energy, 100)

    def test_task_assignment_by_id(self):
        """Verify that task_assign_result correctly links a Task to the character."""
        option = SaveCharacterOption.objects.create(
            decision=self.decision,
            save_character=self.sc_alice,
            task_assign_result=self.special_task.pk
        )

        self.assertIsNone(self.sc_alice.task_assigned)
        
        option.apply()
        self.sc_alice.refresh_from_db()

        self.assertEqual(self.sc_alice.task_assigned, self.special_task)
        self.assertFalse(self.sc_alice.is_resting)

        self.assertTrue(getattr(self.sc_alice, 'lock_task', False))

    def test_unassign_and_rest_logic(self):
        """Verify that unassigning a task and setting rest works correctly."""
        self.sc_alice.task_assigned = self.special_task
        self.sc_alice.save()

        option = SaveCharacterOption.objects.create(
            decision=self.decision,
            save_character=self.sc_alice,
            unassign_task=True,
            set_rest=True
        )

        option.apply()
        self.sc_alice.refresh_from_db()

        self.assertIsNone(self.sc_alice.task_assigned)
        self.assertTrue(self.sc_alice.is_resting)

    def test_stat_clamping_individual(self):
        """Ensure individual stat multipliers still respect the 0-100 clamp."""
        option = SaveCharacterOption.objects.create(
            decision=self.decision,
            save_character=self.sc_alice,
            happiness_effect=5.0
        )

        option.apply()
        self.sc_alice.refresh_from_db()
        self.assertEqual(self.sc_alice.current_happiness, 100)

    def test_invalid_task_id_handling(self):
        """If task_assign_result ID doesn't exist, it should fail gracefully (do nothing)."""
        option = SaveCharacterOption.objects.create(
            decision=self.decision,
            save_character=self.sc_alice,
            task_assign_result=99999
        )

        option.apply()
        self.sc_alice.refresh_from_db()
        self.assertIsNone(self.sc_alice.task_assigned)