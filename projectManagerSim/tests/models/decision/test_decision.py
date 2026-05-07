from django.test import TestCase
from unittest.mock import MagicMock, patch
from projectManagerSim.models import Decision, Save, Character, SaveCharacter

class DecisionLogicTests(TestCase):
    def setUp(self):
        # 1. Setup User and Save
        from django.contrib.auth.models import User
        self.user = User.objects.create(username="testplayer")
        self.game_save = Save.objects.create(
            user=self.user,
            save_name="Test Slot",
            current_day=10  # Start at Day 10
        )

        # 2. Setup a Decision
        self.decision = Decision.objects.create(
            game_save=self.game_save,
            title="Emergency Meeting",
            day_requirement=10,
            deadline=3,
            is_locked=False
        )

    ## --- Availability & Day Logic ---

    def test_is_available_respects_day_requirement(self):
        """Decision should be unavailable if the game hasn't reached the required day."""
        self.decision.day_requirement = 15
        self.decision.save()
        # Current day is 10, requirement is 15
        self.assertFalse(self.decision.is_available())

    def test_is_available_returns_false_if_made(self):
        """Once is_made is True, it should no longer be available."""
        self.decision.is_made = True
        self.decision.save()
        self.assertFalse(self.decision.is_available())

    ## --- Unlocking & Delays ---

    def test_unlock_with_relative_delay(self):
        """unlock() with a delay should set the requirement relative to the current_day."""
        # Current day is 10. Delay of 5 means requirement becomes 15.
        self.decision.is_locked = True
        self.decision.save()
        
        self.decision.unlock(unlocking_delay=5)
        
        self.assertFalse(self.decision.is_locked)
        self.assertEqual(self.decision.day_requirement, 15)

    ## --- Deadline & Option Execution ---

    def test_update_deadline_decrements_value(self):
        """Each call to update_deadline should reduce the counter by 1."""
        self.decision.update_deadline()
        self.assertEqual(self.decision.deadline, 2)

    @patch('projectManagerSim.models.decision.Decision.options')
    def test_deadline_expiry_auto_applies_first_option(self, mock_options_rel):
        """When deadline reaches 0, the first option must be applied automatically."""
        # Setup: Deadline is 1, so one update triggers expiry
        self.decision.deadline = 1
        self.decision.save()

        # Mock the related 'options' manager and the first option object
        mock_option = MagicMock()
        mock_options_rel.all().order_by.return_value.first.return_value = mock_option

        self.decision.update_deadline()

        # Check if the logic executed
        self.assertTrue(self.decision.is_made)
        mock_option.apply.assert_called_once()

    ## --- Character Integration (Simulation) ---

    def test_decision_linked_to_save_characters(self):
        """Verify the decision can access characters through the game_save relationship."""
        # Create a SaveCharacter
        char_template = Character.objects.create(first_name="Alice", last_name="Dev")
        SaveCharacter.objects.create(game_save=self.game_save, character=char_template)

        # Access characters via the foreign key on decision
        characters = self.decision.game_save.characters.all()
        self.assertEqual(characters.count(), 1)
        self.assertEqual(characters.first().character.first_name, "Alice")