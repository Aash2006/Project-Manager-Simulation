from django.test import TestCase
from django.contrib.auth.models import User
from projectManagerSim.models.save import Save
from projectManagerSim.models.character import Character
from projectManagerSim.models.save_character import SaveCharacter
from projectManagerSim.models.task import Task
from projectManagerSim.models.task_type import TaskType
from projectManagerSim.models.character_relationships import CharacterRelationship
from projectManagerSim.models.decisions.character_decision import CharacterDecision

class CharacterDecisionIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="pm_tester")
        self.game_save = Save.objects.create(
            user=self.user,
            save_name="Test Save",
            current_day=10,
            progress_percent=50
        )

        self.alice_tpl = Character.objects.create(
            first_name="Alice", 
            initial_energy=80, 
            initial_happiness=70
        )
        self.sc_alice = SaveCharacter.objects.create(
            game_save=self.game_save, 
            character=self.alice_tpl
        )
        self.bob_tpl = Character.objects.create(
            first_name="Bob", 
            initial_energy=80, 
            initial_happiness=70
        )
        self.sc_bob = SaveCharacter.objects.create(
            game_save=self.game_save, 
            character=self.bob_tpl
        )
        self.jake_tpl = Character.objects.create(
            first_name="Bob", 
            initial_energy=80, 
            initial_happiness=70
        )

        self.task_type = TaskType.objects.create(task_type_name="Development")
        self.main_task = Task.objects.create(
            name="Core Engine",
            game_save=self.game_save,
            task_type=self.task_type,
            time_to_complete=5,
            unlocks_at_percent=20,
            is_completed=False
        )

        self.decision = CharacterDecision.objects.create(
            game_save=self.game_save,
            title="Alice's Blah Blah Blah",
            day_requirement=5,
            is_locked=False
        )
        self.decision.required_characters_in_save.add(self.alice_tpl)

        self.not_our_char_decision = CharacterDecision.objects.create(
            game_save=self.game_save,
            title="Jake's Blah Blah Blah",
            is_locked=False
        )
        self.not_our_char_decision.required_characters_in_save.add(self.jake_tpl)

    def test_stat_requirement_comparison_logic(self):
        """Verify that JSON-based stat requirements parse and compare correctly."""
        self.decision.stat_requirement = [{
            'stat': 'energy', 
            'operator': '>', 
            'value': 70, 
            'character_pk': self.alice_tpl.pk
        }]
        self.decision.save()
        
        self.assertTrue(self.decision.is_stat_requirements_fulfilled())

        self.sc_alice.current_energy = 50
        self.sc_alice.save()
        self.assertFalse(self.decision.is_stat_requirements_fulfilled())


    def test_stat_requirement_invalid_operator(self):
        """Verify that invalid operators are automatically false"""
        self.decision.stat_requirement = [{
            'stat': 'energy', 
            'operator': 'sza', 
            'value': 0, 
            'character_pk': self.alice_tpl.pk
        }]
        self.decision.save()
        self.assertFalse(self.decision.is_stat_requirements_fulfilled())


    def test_stat_requirement_invalid_stat(self):
        """Verify that invalid stats are automatically false"""
        self.decision.stat_requirement = [{
            'stat': 'summer_walker', 
            'operator': '<', 
            'value': 0, 
            'character_pk': self.alice_tpl.pk
        }]
        self.decision.save()
        self.assertFalse(self.decision.is_stat_requirements_fulfilled())


    def test_stat_requirement_invalid_value(self):
        """Verify that invalid values are automatically false"""
        self.decision.stat_requirement = [{
            'stat': 'energy', 
            'operator': '<', 
            'value': 'kali_uchis', 
            'character_pk': self.alice_tpl.pk
        }]
        self.decision.save()
        self.assertFalse(self.decision.is_stat_requirements_fulfilled())


    def test_stat_requirement_invalid_pk(self):
        """Verify that invalid PKs are automatically false"""
        self.decision.stat_requirement = [{
            'stat': 'energy', 
            'operator': '<', 
            'value': 0, 
            'character_pk': 999999999
        }]
        self.decision.save()
        self.assertFalse(self.decision.is_stat_requirements_fulfilled())


    def test_stat_requirement_unfinished_dict(self):
        """Verify that dicts that don't have all the required keys fail"""
        self.decision.stat_requirement = [{
            'stat': 'energy'
        }]
        self.decision.save()
        self.assertFalse(self.decision.is_stat_requirements_fulfilled())
            

    def test_task_complete_requirement(self):
        """The decision should only be available if a specific task is finished."""
        self.decision.task_complete = self.main_task
        self.decision.save()

        self.assertFalse(self.decision.is_available())

        self.main_task.is_completed = True
        self.main_task.save()

        self.assertTrue(self.decision.is_available())

    def test_task_working_requirement(self):
        """Decision available only if character is currently working on any task."""
        self.decision.task_working = self.sc_alice
        self.decision.save()

        self.assertFalse(self.decision.is_available())

        self.sc_alice.task_assigned = self.main_task
        self.sc_alice.save()

        self.assertTrue(self.decision.is_available())

    def test_required_characters_constraint(self):
        """Verify M2M relationship check for specific characters in a save."""
        bob_tpl = Character.objects.create(first_name="Bob")
        self.decision.required_characters_in_save.add(bob_tpl)
        
        self.assertFalse(self.decision.is_available())

        SaveCharacter.objects.create(game_save=self.game_save, character=bob_tpl)
        self.assertTrue(self.decision.is_available())

    def test_relationship_type_requirement(self):
        """Verify that relationship status flags availability."""
        rel = CharacterRelationship.objects.create(
            character_a=self.sc_bob,
            character_b=self.sc_alice,
            relationship_score=-50
        )

        decision = CharacterDecision.objects.create(
            game_save=self.game_save,
            title="Alice's Blah Blah Blah",
            relationship=rel,
            relationship_score="best_friends"
        )

        self.assertFalse(decision.is_available())

        rel.relationship_score =  50
        rel.save()
        decision.refresh_from_db()
        self.assertTrue(decision.is_available())

    def test_unlock_with_database_refresh(self):
        """Ensure the unlock() method correctly syncs with the DB."""
        self.decision.is_locked = True
        self.decision.day_requirement = 0
        self.decision.save()

        self.decision.unlock(unlocking_delay=5)

        self.assertFalse(self.decision.is_locked)
        self.assertEqual(self.decision.day_requirement, 15)
    
    def test_unavailable_if_not_in_save(self):
        """Ensure that if a character isn't in a save they're not available"""

        self.assertFalse(self.not_our_char_decision.is_available())
    
    def test_task_available_requirement(self):
        """Makes sure that if a task isn't unlocked, it fails availability"""
        future_task = Task.objects.create(
            name="Future Task",
            game_save=self.game_save,
            task_type=self.task_type,
            unlocks_at_percent=90,
            time_to_complete=10
        )
        self.decision.task_available = future_task
        self.decision.save()

        self.assertFalse(self.decision.is_available())

        self.game_save.progress_percent = 95
        self.game_save.save()
        self.assertTrue(self.decision.is_available())

    def test_task_not_working_requirement(self):
        """Verify logic for when a character shouldn't be working."""
        self.decision.task_not_working = self.sc_alice
        self.decision.save()

        self.assertTrue(self.decision.is_available())

        self.sc_alice.task_assigned = self.main_task
        self.sc_alice.save()
        self.assertFalse(self.decision.is_available())
    
    def test_relationship_neutral_no_object(self):
        """Make sure when there's no relationship but the requirement is 'neutral', it accepts it"""
        self.decision.relationship = None
        self.decision.relationship_score = "neutral"
        self.decision.save()
        
        self.assertTrue(self.decision.is_available())

        self.decision.relationship_score = "enemies"
        self.decision.save()
        self.assertFalse(self.decision.is_available())