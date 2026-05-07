from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from projectManagerSim.models import Character, Save, SaveCharacter, CharacterRelationship

class CharacterRelationshipTestCase(TestCase):
    def setUp(self):
        # 1. Setup Basic requirements
        self.user = User.objects.create_user(username="testuser", password="password")
        self.game_save = Save.objects.create(
            user=self.user, 
            save_name="Test Save",
            total_days=30
        )
        
        # 2. Create Characters
        self.char_template1 = Character.objects.create(first_name="Template", last_name="Char")
        self.char_template2 = Character.objects.create(first_name="Template", last_name="Char")
        self.char_template3 = Character.objects.create(first_name="Template", last_name="Char")
        
        # 3. Create SaveCharacters (The instances used in relationships)
        self.char_a = SaveCharacter.objects.create(game_save=self.game_save, character=self.char_template1)
        self.char_b = SaveCharacter.objects.create(game_save=self.game_save, character=self.char_template2)
        self.char_c = SaveCharacter.objects.create(game_save=self.game_save, character=self.char_template3)

    def test_relationship_score_mapping(self):
        """Verify that specific scores return the correct types and modifiers"""
        test_cases = [
            (45, 'best_friends', 0.85, "-15%"),
            (25, 'friends', 0.90, "-10%"),
            (0, 'neutral', 1.00, "0%"),
            (-20, 'tension', 1.10, "+10%"),
            (-45, 'rivalry', 1.25, "+25%"),
        ]

        for score, expected_type, expected_mod, expected_str in test_cases:
            with self.subTest(score=score):
                rel = CharacterRelationship(
                    character_a=self.char_a, 
                    character_b=self.char_b, 
                    relationship_score=score
                )
                self.assertEqual(rel.relationship_type, expected_type)
                self.assertEqual(rel.energy_modifier, expected_mod)
                self.assertEqual(rel.energy_modifier_percent, expected_str)

    def test_bidirectional_lookup(self):
        """Test that get_relationship_between finds the relationship regardless of order"""
        rel = CharacterRelationship.objects.create(
            character_a=self.char_a,
            character_b=self.char_b,
            relationship_score=40
        )

        # Lookup A -> B
        found_1 = CharacterRelationship.get_relationship_between(self.char_a, self.char_b)
        # Lookup B -> A
        found_2 = CharacterRelationship.get_relationship_between(self.char_b, self.char_a)

        self.assertEqual(found_1, rel)
        self.assertEqual(found_2, rel)
        self.assertEqual(found_1, found_2)

    def test_prevent_self_relationship(self):
        """Ensure a character cannot have a relationship with themselves"""
        rel = CharacterRelationship(character_a=self.char_a, character_b=self.char_a)
        with self.assertRaises(ValueError):
            rel.save()

    def test_evolution_methods(self):
        """Test improve_relationship and worsen_relationship logic and bounds"""
        rel = CharacterRelationship.objects.create(
            character_a=self.char_a,
            character_b=self.char_b,
            relationship_score=48
        )

        # Test improvement capped at 50
        rel.improve_relationship(5)
        self.assertEqual(rel.relationship_score, 50)

        # Test worsening
        rel.worsen_relationship(20)
        self.assertEqual(rel.relationship_score, 30)

        # Test worsening capped at -50
        rel.worsen_relationship(100)
        self.assertEqual(rel.relationship_score, -50)

    def test_energy_modifier_static_method(self):
        """Test the static helper returns 1.0 if no relationship exists"""
        # No relationship created yet
        modifier = CharacterRelationship.get_energy_modifier_between(self.char_a, self.char_c)
        self.assertEqual(modifier, 1.0)

        # Create relationship
        CharacterRelationship.objects.create(
            character_a=self.char_a,
            character_b=self.char_c,
            relationship_score=-50
        )
        modifier = CharacterRelationship.get_energy_modifier_between(self.char_a, self.char_c)
        self.assertEqual(modifier, 1.25)

    def test_ui_helpers(self):
        """Test icons and badge classes for the frontend"""
        rel = CharacterRelationship(
            character_a=self.char_a,
            character_b=self.char_b,
            relationship_score=50
        )
        self.assertEqual(rel.get_icon(), '❤️')
        self.assertEqual(rel.get_badge_class(), 'badge-success')
        
        rel.relationship_score = -50
        self.assertEqual(rel.get_icon(), '⚡')
        self.assertEqual(rel.get_badge_class(), 'badge-danger')