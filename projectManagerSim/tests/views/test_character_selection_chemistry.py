import json

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from projectManagerSim.models import (
    Character,
    CharacterTemplateRelationship,
    Save,
)


def make_user(username='testuser', password='testpass123'):
    return User.objects.create_user(username=username, password=password)


def make_character(first_name='Alice', last_name='Test', role='backend', **kwargs):
    defaults = dict(
        first_name=first_name,
        last_name=last_name,
        primary_role=role,
        initial_energy=75,
        initial_happiness=100,
        work_life_balance=50,
    )
    defaults.update(kwargs)
    return Character.objects.create(**defaults)


class PreviewTeamChemistryViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='testpass123')
        from django.core.management import call_command
        call_command('loaddata', 'characters', verbosity=0)
        call_command('loaddata', 'task_types', verbosity=0)
        self.characters = list(Character.objects.all()[:5])
        self.url = reverse('preview_chemistry')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(
            self.url,
            data=json.dumps({'selected_characters': [c.id for c in self.characters[:4]]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)

    def test_valid_selection_returns_chemistry(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'selected_characters': [c.id for c in self.characters[:4]]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('team_chemistry', data)

    def test_chemistry_response_has_required_keys(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'selected_characters': [c.id for c in self.characters[:4]]}),
            content_type='application/json'
        )
        chemistry = response.json()['team_chemistry']
        for key in ['score', 'level', 'message', 'best_friends', 'friends', 'tensions', 'rivalries']:
            self.assertIn(key, chemistry, msg=f"Missing key: {key}")

    def test_wrong_number_of_characters_returns_400(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'selected_characters': [self.characters[0].id, self.characters[1].id]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])

    def test_invalid_character_ids_returns_400(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'selected_characters': [9999, 9998, 9997, 9996]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])

    def test_malformed_json_returns_400(self):
        response = self.client.post(
            self.url,
            data='not valid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])

    def test_only_accepts_post(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


class AnalyzeTeamChemistryTest(TestCase):
    """Tests for the analyze_team_chemistry function covering all chemistry levels."""

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='testpass123')
        from django.core.management import call_command
        call_command('loaddata', 'characters', verbosity=0)
        call_command('loaddata', 'task_types', verbosity=0)
        self.characters = list(Character.objects.all()[:4])
        self.url = reverse('preview_chemistry')

    def _post_chemistry(self, char_ids):
        response = self.client.post(
            self.url,
            data=json.dumps({'selected_characters': char_ids}),
            content_type='application/json'
        )
        return response.json()['team_chemistry']

    def _create_relationship(self, char_a, char_b, score):
        # Ensure consistent ordering
        if char_a.id > char_b.id:
            char_a, char_b = char_b, char_a
        CharacterTemplateRelationship.objects.get_or_create(
            character_a=char_a,
            character_b=char_b,
            defaults={'relationship_score': score}
        )

    def test_excellent_chemistry(self):
        """score >= 4 → excellent"""
        chars = [make_character(f'Char{i}', 'Test') for i in range(4)]
        # Create 2 best_friends pairs (score=45 each) → chemistry score = 2*2 = 4
        self._create_relationship(chars[0], chars[1], 45)
        self._create_relationship(chars[2], chars[3], 45)
        chemistry = self._post_chemistry([c.id for c in chars])
        self.assertEqual(chemistry['level'], 'excellent')

    def test_good_chemistry(self):
        """score >= 1 → good"""
        chars = [make_character(f'GoodChar{i}', 'Test') for i in range(4)]
        # 1 friends pair → score = 1
        self._create_relationship(chars[0], chars[1], 20)
        chemistry = self._post_chemistry([c.id for c in chars])
        self.assertEqual(chemistry['level'], 'good')

    def test_mixed_chemistry(self):
        """score >= -2 → mixed"""
        chars = [make_character(f'MixedChar{i}', 'Test') for i in range(4)]
        # 1 tension pair → score = -1
        self._create_relationship(chars[0], chars[1], -20)
        chemistry = self._post_chemistry([c.id for c in chars])
        self.assertEqual(chemistry['level'], 'mixed')

    def test_poor_chemistry(self):
        """score >= -5 → poor"""
        chars = [make_character(f'PoorChar{i}', 'Test') for i in range(4)]
        # 1 rivalry pair → score = -3
        self._create_relationship(chars[0], chars[1], -45)
        chemistry = self._post_chemistry([c.id for c in chars])
        self.assertEqual(chemistry['level'], 'poor')

    def test_toxic_chemistry(self):
        """score < -5 → toxic"""
        chars = [make_character(f'ToxicChar{i}', 'Test') for i in range(4)]
        # 2 rivalry pairs → score = -6
        self._create_relationship(chars[0], chars[1], -45)
        self._create_relationship(chars[2], chars[3], -45)
        chemistry = self._post_chemistry([c.id for c in chars])
        self.assertEqual(chemistry['level'], 'toxic')

    def test_no_relationships_is_mixed(self):
        """No relationships → score = 0 → mixed"""
        chars = [make_character(f'NeutralChar{i}', 'Test') for i in range(4)]
        chemistry = self._post_chemistry([c.id for c in chars])
        self.assertEqual(chemistry['level'], 'mixed')
        self.assertEqual(chemistry['score'], 0)


class CharacterSelectionNoDataTest(TestCase):
    """Test the ValueError branch when no characters exist in the DB."""

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='testpass123')

    def test_post_with_no_characters_in_db_returns_500(self):
        # No fixture loaded — Character table is empty
        response = self.client.post(
            reverse('game_start_new'),
            data=json.dumps({'selected_characters': [1, 2, 3, 4]}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.json()['success'])