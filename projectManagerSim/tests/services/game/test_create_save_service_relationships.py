from django.contrib.auth.models import User
from django.test import TestCase

from projectManagerSim.models import (
    Character,
    CharacterRelationship,
    CharacterTemplateRelationship,
    Save,
)
from projectManagerSim.services.game.create_save_service import populate_characters


class PopulateCharactersTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass123")
        self.save = Save.objects.create(user=self.user, save_name="Test Save", active=True)

        self.characters = [
            Character.objects.create(
                first_name="Bella",
                last_name="Smith",
                description="The Conscript",
                initial_energy=68,
                initial_happiness=72,
                initial_confidence=95,
                initial_dedication=55,
                initial_stress=100,
                initial_irritability=105,
                initial_skill_level=85,
                initial_communication_skills=85,
                initial_reliability=65,
                initial_teachability=90,
            ),
            Character.objects.create(
                first_name="Anthony",
                last_name="Sharp",
                description="The Burnout",
                initial_energy=42,
                initial_happiness=58,
                initial_confidence=88,
                initial_dedication=92,
                initial_stress=170,
                initial_irritability=110,
                initial_skill_level=95,
                initial_communication_skills=100,
                initial_reliability=85,
                initial_teachability=100,
            ),
            Character.objects.create(
                first_name="Victor",
                last_name="Ruban",
                description="The Narcissist",
                initial_energy=74,
                initial_happiness=74,
                initial_confidence=165,
                initial_dedication=88,
                initial_stress=104,
                initial_irritability=118,
                initial_skill_level=60,
                initial_communication_skills=96,
                initial_reliability=78,
                initial_teachability=60,
            ),
        ]

        CharacterTemplateRelationship.objects.create(
            character_a=self.characters[0],
            character_b=self.characters[1],
            relationship_score=21,
        )
        CharacterTemplateRelationship.objects.create(
            character_a=self.characters[0],
            character_b=self.characters[2],
            relationship_score=-17,
        )
        CharacterTemplateRelationship.objects.create(
            character_a=self.characters[1],
            character_b=self.characters[2],
            relationship_score=-9,
        )

    def test_populate_characters_copies_character_initial_stats_to_save_characters(self):
        save_characters = populate_characters(self.save, self.characters)

        bella = save_characters[0]
        anthony = save_characters[1]
        victor = save_characters[2]

        self.assertEqual(bella.current_energy, 68)
        self.assertEqual(bella.current_happiness, 72)
        self.assertEqual(bella.current_confidence, 95)
        self.assertEqual(anthony.current_stress, 170)
        self.assertEqual(anthony.current_reliability, 85)
        self.assertEqual(victor.current_skill_level, 60)
        self.assertEqual(victor.current_teachability, 60)

    def test_populate_characters_creates_unique_per_save_relationships_for_each_pair(self):
        save_characters = populate_characters(self.save, self.characters)

        relationships = CharacterRelationship.objects.filter(character_a__game_save=self.save)

        self.assertEqual(len(save_characters), 3)
        self.assertEqual(relationships.count(), 3)

        seen_pairs = set()
        expected_scores = {
            tuple(sorted((self.characters[0].id, self.characters[1].id))): 21,
            tuple(sorted((self.characters[0].id, self.characters[2].id))): -17,
            tuple(sorted((self.characters[1].id, self.characters[2].id))): -9,
        }

        for relationship in relationships:
            pair = tuple(sorted([relationship.character_a.character_id, relationship.character_b.character_id]))
            self.assertNotIn(pair, seen_pairs)
            seen_pairs.add(pair)
            self.assertNotEqual(relationship.character_a_id, relationship.character_b_id)
            self.assertEqual(relationship.relationship_score, expected_scores[pair])

    def test_populate_characters_copies_scores_from_template_relationships(self):
        save_characters = populate_characters(self.save, self.characters)

        bella = next(sc for sc in save_characters if sc.character == self.characters[0])
        anthony = next(sc for sc in save_characters if sc.character == self.characters[1])
        victor = next(sc for sc in save_characters if sc.character == self.characters[2])

        self.assertEqual(
            CharacterRelationship.get_relationship_between(bella, anthony).relationship_score,
            CharacterTemplateRelationship.get_relationship_between(self.characters[0], self.characters[1]).relationship_score,
        )
        self.assertEqual(
            CharacterRelationship.get_relationship_between(bella, victor).relationship_score,
            CharacterTemplateRelationship.get_relationship_between(self.characters[0], self.characters[2]).relationship_score,
        )
