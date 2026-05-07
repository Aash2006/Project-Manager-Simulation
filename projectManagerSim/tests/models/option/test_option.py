from django.test import TestCase
from django.contrib.auth.models import User
from projectManagerSim.models.save import Save
from projectManagerSim.models.character import Character
from projectManagerSim.models.save_character import SaveCharacter
from projectManagerSim.models.task import Task
from projectManagerSim.models.task_type import TaskType
from projectManagerSim.models.decisions.decision import Decision
from projectManagerSim.models.decisions.option import Option

class OptionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test_pm")
        self.game_save = Save.objects.create(
            user=self.user, 
            save_name="Option Test Save",
            score=10
        )
        
        self.decision = Decision.objects.create(
            game_save=self.game_save,
            title="A Crucial Choice",
            is_locked=False
        )
        
        self.char_template = Character.objects.create(first_name="John", last_name="Dev")
        self.sc = SaveCharacter.objects.create(
            game_save=self.game_save, 
            character=self.char_template
        )

        self.task_type = TaskType.objects.create(task_type_name="Coding")

    def test_apply_score_effect(self):
        """Verify that applying an option updates the game save score."""
        option = Option.objects.create(
            decision=self.decision,
            score_effect=2,
            text="+2 Score Option"
        )
        
        option.apply()
        self.game_save.refresh_from_db()
        self.assertEqual(self.game_save.score, 12)

    def test_apply_unlocks_chained_decision(self):
        """Option should be able to unlock a future locked decision."""
        next_decision = Decision.objects.create(
            game_save=self.game_save,
            title="Follow-up Event",
            is_locked=True,
            day_requirement=0
        )

        unlocking_option = Option.objects.create(
            decision=self.decision,
            text="Unlock Next",
            unlocking_decision=next_decision,
            unlocking_day_delay=3
        )

        self.game_save.current_day = 5
        self.game_save.save()

        unlocking_option.apply()
        
        next_decision.refresh_from_db()
        self.assertFalse(next_decision.is_locked)
        # 5 (current day) + 3 (delay) = 8
        self.assertEqual(next_decision.day_requirement, 8)

    def test_apply_creates_tasks_from_json(self):
        """Verify that JSON task definitions are converted into real Task objects."""
        task_data = [{
            'name': 'New Feature',
            'task_type': self.task_type.pk,
            'time_to_complete': 5,
            'unlocks_at_percent': 0,
            'number_of_people_required': 1,
            'energy_cost': 20,
            'difficulty': 3
        }]
        
        option = Option.objects.create(
            decision=self.decision,
            text="Start Development",
            create_tasks=task_data
        )

        option.apply()

        created_task = Task.objects.filter(game_save=self.game_save, name__contains="New Feature").first()
        self.assertIsNotNone(created_task)
        self.assertEqual(created_task.difficulty, 3)
        self.assertEqual(created_task.task_type, self.task_type)

    def test_apply_removes_character_from_team(self):
        """Setting leave_team should flag the character as leaving."""
        option = Option.objects.create(
            decision=self.decision,
            text="Fire John",
            leave_team=self.char_template.pk
        )

        self.assertFalse(self.sc.leaving)
        option.apply()
        
        self.sc.refresh_from_db()
        self.assertTrue(self.sc.leaving)

    def test_apply_handles_complex_consequences(self):
        """Ensure multiple effects (score and tasks) can happen simultaneously."""
        option = Option.objects.create(
            decision=self.decision,
            score_effect=-1,
            create_tasks=[{'name': 'Bugfix', 'task_type': self.task_type.pk, 'time_to_complete': 1, 
                           'unlocks_at_percent': 0, 'number_of_people_required': 1, 
                           'energy_cost': 5, 'difficulty': 1}]
        )

        option.apply()
        self.game_save.refresh_from_db()
        
        self.assertEqual(self.game_save.score, 9) # 10 - 1
        self.assertTrue(Task.objects.filter(game_save=self.game_save, name__contains="Bugfix").exists())