from django.test import TestCase
from django.contrib.auth.models import User
from projectManagerSim.models.save import Save
from projectManagerSim.models.character import Character
from projectManagerSim.models.save_character import SaveCharacter
from projectManagerSim.models.character_relationships import CharacterRelationship
from projectManagerSim.models.decisions.decision import Decision
from projectManagerSim.models.decisions.save_character_relation_option import SaveCharacterRelationOption

class SaveCharacterRelationOptionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="relationship_mgr")
        self.game_save = Save.objects.create(user=self.user, save_name="Relationship Test")
        
        self.char_1 = Character.objects.create(first_name="Alice", initial_energy=100)
        self.char_2 = Character.objects.create(first_name="Bob", initial_energy=100)
        
        self.sc_1 = SaveCharacter.objects.create(game_save=self.game_save, character=self.char_1)
        self.sc_2 = SaveCharacter.objects.create(game_save=self.game_save, character=self.char_2)

        self.decision = Decision.objects.create(game_save=self.game_save, title="Interpersonal Conflict")

    def test_apply_updates_both_characters(self):
        """Verify that Character 1 (parent field) and Character 2 (this model) both get stat updates."""
        option = SaveCharacterRelationOption.objects.create(
            decision=self.decision,
            save_character=self.sc_1,  
            save_character_2=self.sc_2,
            energy_effect=0.8,       
            energy_effect_2=0.5 
        )

        option.apply()
        
        self.sc_1.refresh_from_db()
        self.sc_2.refresh_from_db()

        self.assertEqual(self.sc_1.current_energy, 80)
        self.assertEqual(self.sc_2.current_energy, 50)

    def test_relationship_creation_and_update(self):
        """Verify that a relationship is created if it doesn't exist and score is applied."""

        self.assertFalse(CharacterRelationship.objects.filter(
            character_a=self.sc_1, character_b=self.sc_2
        ).exists())

        option = SaveCharacterRelationOption.objects.create(
            decision=self.decision,
            save_character=self.sc_1,
            save_character_2=self.sc_2,
            relation_change=15
        )

        option.apply()

        relation = CharacterRelationship.objects.get(
            character_a=self.sc_1, 
            character_b=self.sc_2
        )
        self.assertIsNotNone(relation)

    def test_set_rest_and_lock_on_character_2(self):
        """Verify the 'rest' and 'lock' logic specifically for the second character."""
        option = SaveCharacterRelationOption.objects.create(
            decision=self.decision,
            save_character=self.sc_1,
            save_character_2=self.sc_2,
            set_rest_2=True
        )

        option.apply()
        self.sc_2.refresh_from_db()

        self.assertTrue(self.sc_2.is_resting)
        self.assertTrue(getattr(self.sc_2, 'lock_rest', False))
        self.assertIsNone(self.sc_2.task_assigned)

    def test_inheritance_chain_execution(self):
        """Ensure super().apply() is called, triggering base Option effects (like score)."""
        option = SaveCharacterRelationOption.objects.create(
            decision=self.decision,
            save_character=self.sc_1,
            save_character_2=self.sc_2,
            score_effect=5 
        )

        self.game_save.score = 10
        self.game_save.save()

        option.apply()
        self.game_save.refresh_from_db()

        self.assertEqual(self.game_save.score, 15)