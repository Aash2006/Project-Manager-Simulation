from django.test import TestCase

from projectManagerSim.models import Character, CharacterTemplateRelationship


class CharacterTemplateRelationshipModelTests(TestCase):
    def setUp(self):
        self.char_a = Character.objects.create(first_name="Alice", last_name="Able", description="A")
        self.char_b = Character.objects.create(first_name="Bob", last_name="Baker", description="B")

    def test_save_normalises_character_order(self):
        """Test that it normalises the character order based on ID"""
        relationship = CharacterTemplateRelationship.objects.create(
            character_a=self.char_b,
            character_b=self.char_a,
            relationship_score=18,
        )

        self.assertEqual(relationship.character_a, self.char_a)
        self.assertEqual(relationship.character_b, self.char_b)

    def test_bidirectional_lookup_finds_template_relationship(self):
        """Test that looking up in either order finds the relationship"""
        relationship = CharacterTemplateRelationship.objects.create(
            character_a=self.char_a,
            character_b=self.char_b,
            relationship_score=-22,
        )

        self.assertEqual(
            CharacterTemplateRelationship.get_relationship_between(self.char_a, self.char_b),
            relationship,
        )
        self.assertEqual(
            CharacterTemplateRelationship.get_relationship_between(self.char_b, self.char_a),
            relationship,
        )
    def test_relationship_score_mapping(self):
        """Make sure that specific scores return the correct types and modifiers"""
        test_cases = [
            (45, 'best_friends', 0.85, "-15%"),
            (25, 'friends', 0.90, "-10%"),
            (0, 'neutral', 1.00, "0%"),
            (-20, 'tension', 1.10, "+10%"),
            (-45, 'rivalry', 1.25, "+25%"),
        ]

        for score, expected_type, expected_mod, expected_str in test_cases:
            with self.subTest(score=score):
                rel = CharacterTemplateRelationship(
                    character_a=self.char_a, 
                    character_b=self.char_b, 
                    relationship_score=score
                )
                self.assertEqual(rel.relationship_type, expected_type)
                self.assertEqual(rel.energy_modifier, expected_mod)
                self.assertEqual(rel.energy_modifier_percent, expected_str)

    def test_prevent_self_relationship(self):
        """Test that a character cannot have a relationship with themselves"""
        rel = CharacterTemplateRelationship(character_a=self.char_a, character_b=self.char_a)
        with self.assertRaises(ValueError):
            rel.save()

    def test_ui_helpers(self):
        """Test icons and badge classes for the frontend"""
        rel = CharacterTemplateRelationship(
            character_a=self.char_a,
            character_b=self.char_b,
            relationship_score=50
        )
        self.assertEqual(rel.get_icon(), '❤️')
        self.assertEqual(rel.get_badge_class(), 'badge-success')
        
        rel.relationship_score = -50
        self.assertEqual(rel.get_icon(), '⚡')
        self.assertEqual(rel.get_badge_class(), 'badge-danger')
