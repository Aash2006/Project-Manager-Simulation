from django.test import TestCase
from django.contrib.auth.models import User
from projectManagerSim.models.save import Save
from projectManagerSim.models.character import Character
from projectManagerSim.models.save_character import SaveCharacter
from projectManagerSim.models.decisions.decision import Decision
from projectManagerSim.models.decisions.project_option import ProjectOption
from projectManagerSim.models.task import Task
from projectManagerSim.models.task_type import TaskType

class ProjectOptionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="project_mgr")
        self.game_save = Save.objects.create(
            user=self.user, 
            save_name="Team Effects Test",
            score=50
        )
        
        self.char_a = Character.objects.create(first_name="Alice", initial_energy=100, initial_happiness=50)
        self.char_b = Character.objects.create(first_name="Bob", initial_energy=50, initial_happiness=80)
        
        self.sc_a = SaveCharacter.objects.create(game_save=self.game_save, character=self.char_a)
        self.sc_b = SaveCharacter.objects.create(game_save=self.game_save, character=self.char_b)

        self.decision = Decision.objects.create(game_save=self.game_save, title="Team Building Event")

    def test_apply_multiplicative_stat_effects(self):
        """Verify that floating point multipliers apply to all characters in the save."""
        project_option = ProjectOption.objects.create(
            decision=self.decision,
            text="Pizza Party",
            happiness_effect=1.2,
            energy_effect=0.5
        )

        project_option.apply()
        
        self.sc_a.refresh_from_db()
        self.sc_b.refresh_from_db()

        self.assertEqual(self.sc_a.current_happiness, 60)
        self.assertEqual(self.sc_a.current_energy, 50)

        self.assertEqual(self.sc_b.current_happiness, 96)
        self.assertEqual(self.sc_b.current_energy, 25)

    def test_stat_clamping(self):
        """Ensure stats do not exceed 100 or drop below 0 due to multipliers."""
        project_option = ProjectOption.objects.create(
            decision=self.decision,
            happiness_effect=5.0,
            energy_effect=-1.0
        )

        project_option.apply()
        self.sc_a.refresh_from_db()

        self.assertEqual(self.sc_a.current_happiness, 100)
        self.assertEqual(self.sc_a.current_energy, 0)

    def test_set_rest_and_unassign_logic(self):
        """Verify that the option can force the entire team to rest and clear tasks."""
        task_type = TaskType.objects.create(task_type_name="Admin")
        dummy_task = Task.objects.create(name="Paperwork", game_save=self.game_save, task_type=task_type, time_to_complete=1)
        
        self.sc_a.task_assigned = dummy_task
        self.sc_a.save()

        project_option = ProjectOption.objects.create(
            decision=self.decision,
            unassign_task=True,
            set_rest=True
        )

        project_option.apply()
        self.sc_a.refresh_from_db()

        self.assertIsNone(self.sc_a.task_assigned)
        self.assertTrue(self.sc_a.is_resting)

    def test_inheritance_of_base_option_effects(self):
        """Ensure ProjectOption still triggers base Option logic like score_effect."""
        project_option = ProjectOption.objects.create(
            decision=self.decision,
            score_effect=10,
            happiness_effect=1.0
        )

        project_option.apply()
        self.game_save.refresh_from_db()

        self.assertEqual(self.game_save.score, 60)

    def test_isolation_between_saves(self):
        """Ensure stat changes only affect characters within the same game_save."""
        other_save = Save.objects.create(user=self.user, save_name="Other Save")
        sc_other = SaveCharacter.objects.create(game_save=other_save, character=self.char_a)
        
        project_option = ProjectOption.objects.create(
            decision=self.decision,
            energy_effect=0.1
        )

        project_option.apply()
        
        sc_other.refresh_from_db()
        self.assertEqual(sc_other.current_energy, 100)