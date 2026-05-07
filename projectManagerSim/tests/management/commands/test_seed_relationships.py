from django.core.management import call_command
from django.test import TestCase

from projectManagerSim.fixtures.character_descr import get_relationship_score
from projectManagerSim.models import (
    Character,
    CharacterRelationship,
    CharacterTemplateRelationship,
    Save,
    SaveCharacter,
)


class SeedRelationshipTests(TestCase):
    def test_seed_creates_canonical_characters_template_relationships_and_save_relationships(self):
        call_command("seed", verbosity=0)

        self.assertEqual(Character.objects.count(), 10)
        self.assertEqual(
            list(Character.objects.order_by("pk").values_list("pk", "first_name", "last_name")),
            [
                (1, "Bella", "Smith"),
                (2, "Lilly", "Evanson"),
                (3, "Anthony", "Sharp"),
                (4, "Bruce", "Barnes"),
                (5, "Jamie", "Howlett"),
                (6, "Reginald", "George"),
                (7, "Richard", "Robbs"),
                (8, "Amelia", "Hunt"),
                (9, "Victor", "Ruban"),
                (10, "James", "Lawson"),
            ],
        )

        self.assertEqual(CharacterTemplateRelationship.objects.count(), 40)

        saves = Save.objects.order_by("id")
        self.assertEqual(saves.count(), 9)
        self.assertEqual(SaveCharacter.objects.count(), 36)
        self.assertEqual(CharacterRelationship.objects.count(), 54)

        first_save = saves.first()
        save_characters = SaveCharacter.objects.filter(game_save=first_save).order_by("character_id")
        self.assertEqual(list(save_characters.values_list("character_id", flat=True)), [1, 2, 3, 4])

        bella = save_characters.get(character_id=1)
        lilly = save_characters.get(character_id=2)
        anthony = save_characters.get(character_id=3)
        bruce = save_characters.get(character_id=4)

        self.assertEqual(bella.current_energy, bella.character.initial_energy)
        self.assertEqual(lilly.current_dedication, lilly.character.initial_dedication)
        self.assertEqual(anthony.current_stress, anthony.character.initial_stress)
        self.assertEqual(bruce.current_irritability, bruce.character.initial_irritability)

        burnout_conscript = CharacterRelationship.get_relationship_between(bella, anthony)
        hothead_zealot = CharacterRelationship.get_relationship_between(lilly, bruce)
        burnout_conscript_template = CharacterTemplateRelationship.get_relationship_between(
            bella.character, anthony.character
        )
        hothead_zealot_template = CharacterTemplateRelationship.get_relationship_between(
            lilly.character, bruce.character
        )

        self.assertIsNotNone(burnout_conscript)
        self.assertIsNotNone(burnout_conscript_template)
        self.assertEqual(burnout_conscript.relationship_score, get_relationship_score(1, 3))
        self.assertEqual(burnout_conscript.relationship_score, burnout_conscript_template.relationship_score)
        self.assertEqual(hothead_zealot.relationship_score, get_relationship_score(2, 4))
        self.assertEqual(hothead_zealot.relationship_score, hothead_zealot_template.relationship_score)
