from django.test import TransactionTestCase
from unittest.mock import MagicMock, patch
from projectManagerSim.models import Decision, Save
from projectManagerSim.services.game.generate_decisions_service import *
from django.contrib.auth.models import User

class GenerateDecisionsTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass123")
        self.save = Save.objects.create(
            user=self.user, save_name="Test", active=True
        )
        
        self.d1 = Decision.objects.create(game_save=self.save, is_made=False, is_served=False)
        self.d2 = Decision.objects.create(game_save=self.save, is_made=False, is_served=False)
        self.d3 = Decision.objects.create(game_save=self.save, is_made=True, is_served=False)

    @patch('projectManagerSim.models.Decision.is_available')
    def test_returns_correct_count(self, mock_available):
        """Make sure the function respects the 'count' parameter."""
        mock_available.return_value = True
        
        results = generate_decisions(self.save, count=1)
        
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].is_served)

    @patch('projectManagerSim.models.Decision.is_available')
    def test_skips_unavailable_decisions(self, mock_available):
        """Test that decisions that are unavailable are ignored."""
        mock_available.side_effect = [False, True]
        
        results = generate_decisions(self.save, count=2)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.d2)

    @patch('projectManagerSim.models.Decision.is_available')
    def test_updates_is_served_status(self, mock_available):
        """Verify picked decisions have is_served set true"""
        mock_available.return_value = True
        
        generate_decisions(self.save, count=1)
        
        self.d1.refresh_from_db()
        self.assertTrue(self.d1.is_served)

    @patch('projectManagerSim.models.Decision.is_available')
    def test_already_served_decisions_are_skipped(self, mock_available):
        """Verify that if is_served is true, the decision isn't picked"""
        mock_available.return_value = True
        self.d1.is_served = True
        self.d1.save()
        
        results = generate_decisions(self.save, count=1)
        
        # Should skip d1 and pick d2
        self.assertEqual(results[0], self.d2)