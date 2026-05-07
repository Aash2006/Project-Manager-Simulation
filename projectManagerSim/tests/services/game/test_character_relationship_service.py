from django.test import TestCase
from unittest.mock import MagicMock, patch


def make_save_char(char_id=1, primary_role='backend', team_player=False):
    """Helper to build a mock save_character"""
    save_char = MagicMock()
    save_char.id = char_id
    save_char.character.primary_role = primary_role
    save_char.character.team_player = team_player
    return save_char


def make_rel(rel_type='friends', score=50, energy_modifier=1.0):
    """Helper to build a mock CharacterRelationship"""
    rel = MagicMock()
    rel.relationship_type = rel_type
    rel.relationship_type_display = rel_type.replace('_', ' ').title()
    rel.relationship_score = score
    rel.energy_modifier = energy_modifier
    rel.energy_modifier_percent = f"{int((energy_modifier - 1) * 100)}%"
    rel.get_icon.return_value = '😊'
    rel.get_badge_class.return_value = 'badge-success'
    rel.get_description.return_value = 'Good relationship'
    return rel


class TestGetCharacterRelationships(TestCase):

    def setUp(self):
        from projectManagerSim.services.game.character_relationship_service import CharacterRelationshipService
        self.sc = make_save_char(char_id=99)
        self.service = CharacterRelationshipService(self.sc)

    @patch('projectManagerSim.models.character_relationships.CharacterRelationship.get_relationship_between')
    def test_skips_self(self, mock_get_rel):
        """Self should never appear in the returned relationships"""
        result = self.service.get_character_relationships([self.sc])
        self.assertEqual(result, [])
        mock_get_rel.assert_not_called()

    @patch('projectManagerSim.models.character_relationships.CharacterRelationship.get_relationship_between')
    def test_returns_relationship_data_when_rel_exists(self, mock_get_rel):
        """Should return a populated dict when a relationship exists"""
        teammate = make_save_char(char_id=2)
        rel = make_rel(rel_type='friends', score=50)
        mock_get_rel.return_value = rel

        result = self.service.get_character_relationships([teammate])

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry['type'], 'friends')
        self.assertEqual(entry['score'], 50)
        self.assertEqual(entry['save_character'], teammate)

    @patch('projectManagerSim.models.character_relationships.CharacterRelationship.get_relationship_between')
    def test_returns_neutral_data_when_no_rel(self, mock_get_rel):
        """Should return neutral defaults when no relationship is defined"""
        teammate = make_save_char(char_id=3)
        mock_get_rel.return_value = None

        result = self.service.get_character_relationships([teammate])

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry['type'], 'neutral')
        self.assertEqual(entry['score'], 0)
        self.assertEqual(entry['energy_modifier'], 1.0)
        self.assertEqual(entry['icon'], '😐')

    @patch('projectManagerSim.models.character_relationships.CharacterRelationship.get_relationship_between')
    def test_sorted_best_first(self, mock_get_rel):
        """Results should be sorted by score descending"""
        teammate_a = make_save_char(char_id=2)
        teammate_b = make_save_char(char_id=3)

        def side_effect(sc, teammate):
            if teammate.id == 2:
                return make_rel(score=10)
            return make_rel(score=90)

        mock_get_rel.side_effect = side_effect

        result = self.service.get_character_relationships([teammate_a, teammate_b])

        self.assertGreaterEqual(result[0]['score'], result[1]['score'])

    @patch('projectManagerSim.models.character_relationships.CharacterRelationship.get_relationship_between')
    def test_excludes_self_among_multiple(self, mock_get_rel):
        """Self should be filtered out even when mixed in with other teammates"""
        mock_get_rel.return_value = make_rel()
        teammates = [make_save_char(char_id=i) for i in [1, 99, 2]]  # 99 = self

        result = self.service.get_character_relationships(teammates)

        ids = [r['save_character'].id for r in result]
        self.assertNotIn(99, ids)
        self.assertEqual(len(result), 2)


class TestGetBestPartners(TestCase):

    def setUp(self):
        from projectManagerSim.services.game.character_relationship_service import CharacterRelationshipService
        self.sc = make_save_char(char_id=99)
        self.service = CharacterRelationshipService(self.sc)

    def _make_rel_data(self, char_id=1, rel_type='neutral', score=0,
                       energy_modifier=1.0, primary_role='backend', team_player=False):
        character = MagicMock()
        character.primary_role = primary_role
        character.team_player = team_player
        character.id = char_id
        return {
            'character': character,
            'type': rel_type,
            'type_display': rel_type.replace('_', ' ').title(),
            'score': score,
            'energy_modifier': energy_modifier,
            'energy_modifier_percent': f"{int((energy_modifier - 1) * 100)}%",
        }

    def test_best_friends_scores_highest(self):
        """best_friends should produce a higher compatibility score than friends"""
        best_friend = self._make_rel_data(char_id=1, rel_type='best_friends')
        friend = self._make_rel_data(char_id=2, rel_type='friends')

        result = self.service.get_best_partners([best_friend, friend])

        self.assertEqual(result[0]['character'].id, 1)

    def test_rivalry_scores_lowest(self):
        """rivalry should produce a lower compatibility score than tension"""
        rival = self._make_rel_data(char_id=1, rel_type='rivalry')
        tension = self._make_rel_data(char_id=2, rel_type='tension')

        result = self.service.get_best_partners([rival, tension])

        self.assertEqual(result[0]['character'].id, 2)

    def test_capped_at_three(self):
        """Should return at most 3 partners regardless of input size"""
        rels = [self._make_rel_data(char_id=i) for i in range(10)]
        result = self.service.get_best_partners(rels)
        self.assertLessEqual(len(result), 3)

    def test_fullstack_bonus_applied(self):
        """Fullstack role should increase compatibility score"""
        fullstack = self._make_rel_data(char_id=1, primary_role='fullstack')
        backend = self._make_rel_data(char_id=2, primary_role='backend')

        result = self.service.get_best_partners([fullstack, backend])

        self.assertEqual(result[0]['character'].id, 1)

    def test_team_player_bonus_applied(self):
        """team_player flag should add to compatibility score"""
        team_player = self._make_rel_data(char_id=1, team_player=True)
        solo = self._make_rel_data(char_id=2, team_player=False)

        result = self.service.get_best_partners([team_player, solo])

        self.assertEqual(result[0]['character'].id, 1)

    def test_energy_modifier_reason_included(self):
        """Efficient energy modifier should appear in reasons"""
        efficient = self._make_rel_data(char_id=1, energy_modifier=0.8)
        result = self.service.get_best_partners([efficient])
        reasons = result[0]['reasons']
        self.assertTrue(any('Efficient' in r for r in reasons))

    def test_costly_energy_modifier_reason_included(self):
        """Costly energy modifier should appear in reasons with warning"""
        costly = self._make_rel_data(char_id=1, energy_modifier=1.3)
        result = self.service.get_best_partners([costly])
        reasons = result[0]['reasons']
        self.assertTrue(any('Costly' in r for r in reasons))

    def test_empty_input_returns_empty(self):
        """Empty relationships list should return empty partners list"""
        result = self.service.get_best_partners([])
        self.assertEqual(result, [])