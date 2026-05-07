import time

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from projectManagerSim.models import Character, Save, SaveCharacter, Task, TaskType


class SaveCharacterHappinessEnergyTests(TestCase):
    """Test happiness-energy functionality in SaveCharacter model"""

    def setUp(self):
        """Set up test data for happiness-energy tests"""
        self.user = User.objects.create_user(
            username="happinessuser", email="happiness@test.com", password="testpass123"
        )

        self.character = Character.objects.create(
            first_name="Happy",
            last_name="Tester",
            primary_role="Developer",
            description="Test character for happiness-energy functionality",
        )

        self.save = Save.objects.create(
            user=self.user,
            save_name="Happiness Test Save",
            progress_percent=50,
            total_days=30,
            active=True,
            status="ONGOING",
        )

        self.task_type = TaskType.objects.create(task_type_name="Backend Development")

        self.task = Task.objects.create(
            name="Test Task",
            time_to_complete=4,
            task_type=self.task_type,
            energy_cost=25,
        )

    def create_save_character(self, energy=100, happiness=100):
        """Helper to create SaveCharacter with specified stats"""
        character = Character.objects.create(
            first_name="Happy",
            last_name="Tester",
            primary_role="Developer",
            description="Test character for happiness-energy functionality",
        )
        obj = SaveCharacter.objects.create(
            game_save=self.save,
            character=character,
            current_energy=energy,
            current_happiness=happiness,
            current_effective_productivity=100,
        )
        obj.current_energy = energy 
        obj.current_happiness = happiness
        obj.save()
        return obj

    def test_happiness_calculation_critical_energy(self):
        """Test happiness calculation for critical energy levels (< 10%)"""
        save_char = self.create_save_character(energy=5, happiness=80)

        change = save_char.calculate_happiness_change_for_energy(5)

        self.assertLess(
            change, -10, "Critical energy should cause major happiness decrease"
        )
        self.assertGreaterEqual(change, -30, "Change should not be excessive")

    def test_happiness_calculation_low_energy(self):
        """Test happiness calculation for low energy levels (10-30%)"""
        save_char = self.create_save_character(energy=25, happiness=70)

        change = save_char.calculate_happiness_change_for_energy(25)

        self.assertLess(change, 0, "Low energy should decrease happiness")
        self.assertGreater(change, -15, "Low energy shouldn't be as severe as critical")

    def test_happiness_calculation_medium_energy(self):
        """Test happiness calculation for medium energy levels (30-70%)"""
        save_char = self.create_save_character(energy=50, happiness=60)

        change = save_char.calculate_happiness_change_for_energy(50)

        self.assertEqual(change, 0, "Medium energy should have no happiness impact")

    def test_happiness_calculation_high_energy(self):
        """Test happiness calculation for high energy levels (70-85%)"""
        save_char = self.create_save_character(energy=80, happiness=60)

        change = save_char.calculate_happiness_change_for_energy(80)

        self.assertGreater(change, 0, "High energy should increase happiness")
        self.assertLessEqual(change, 10, "High energy bonus should be reasonable")

    def test_happiness_calculation_very_high_energy(self):
        """Test happiness calculation for very high energy levels (> 85%)"""
        save_char = self.create_save_character(energy=95, happiness=70)

        change = save_char.calculate_happiness_change_for_energy(95)

        self.assertGreater(change, 5, "Very high energy should give significant bonus")
        self.assertLessEqual(
            change, 15, "Very high energy bonus should not be excessive"
        )

    def test_apply_task_happiness_effect(self):
        """Test applying happiness effects when completing tasks"""
        save_char = self.create_save_character(energy=20, happiness=70)  # Low energy
        initial_happiness = save_char.current_happiness

        result = save_char.apply_task_happiness_effect("Test Task")

        # Refresh from database
        save_char.refresh_from_db()

        # Should have decreased happiness due to low energy
        self.assertLess(save_char.current_happiness, initial_happiness)

        # Check result structure
        required_keys = [
            "old_happiness",
            "new_happiness",
            "happiness_change",
            "energy_level",
            "message",
            "energy_category",
        ]
        for key in required_keys:
            self.assertIn(key, result, f"Missing key in result: {key}")

        # Verify values
        self.assertEqual(result["old_happiness"], initial_happiness)
        self.assertEqual(result["new_happiness"], save_char.current_happiness)
        self.assertLess(
            result["happiness_change"], 0
        )  # Should be negative for low energy

    def test_happiness_bounds_enforcement(self):
        """Test that happiness stays within 0-100 bounds"""
        # Test lower bound (can't go below 0)
        save_char = self.create_save_character(energy=5, happiness=5)
        save_char.apply_task_happiness_effect("Stress Task")

        self.assertGreaterEqual(
            save_char.current_happiness, 0, "Happiness should not go below 0"
        )

        # Test upper bound (can't go above 100)
        save_char2 = self.create_save_character(energy=95, happiness=95)
        save_char2.apply_task_happiness_effect("Joy Task")

        self.assertLessEqual(
            save_char2.current_happiness, 100, "Happiness should not exceed 100"
        )

    def test_get_energy_category(self):
        """Test energy categorization"""
        save_char = self.create_save_character()

        test_cases = [
            (5, "critical"),
            (25, "low"),
            (50, "medium"),
            (80, "high"),
            (95, "very_high"),
        ]

        for energy, expected_category in test_cases:
            with self.subTest(energy=energy):
                category = save_char.get_energy_category(energy)
                self.assertEqual(category, expected_category)

    def test_get_happiness_preview(self):
        """Test happiness change preview functionality"""
        save_char = self.create_save_character(energy=30, happiness=60)

        preview = save_char.get_happiness_preview()

        # Check structure
        required_keys = [
            "energy",
            "happiness",
            "predicted_change",
            "predicted_happiness",
            "energy_category",
        ]
        for key in required_keys:
            self.assertIn(key, preview, f"Missing key in preview: {key}")

        # Check values
        self.assertEqual(preview["energy"], 30)
        self.assertEqual(preview["happiness"], 60)
        self.assertEqual(preview["energy_category"], "medium")
        self.assertEqual(preview["predicted_change"], 0)  # Medium energy = no change
        self.assertEqual(preview["predicted_happiness"], 60)  # Should remain same

    def test_energy_assessment_methods(self):
        """Test energy level assessment methods"""
        save_char = self.create_save_character()

        # Test good energy threshold (> 70%)
        save_char.current_energy = 80
        self.assertTrue(save_char.is_energy_good_for_happiness())

        save_char.current_energy = 60
        self.assertFalse(save_char.is_energy_good_for_happiness())

        # Test bad energy threshold (< 30%)
        save_char.current_energy = 20
        self.assertTrue(save_char.is_energy_bad_for_happiness())

        save_char.current_energy = 40
        self.assertFalse(save_char.is_energy_bad_for_happiness())

    def test_get_mood_status(self):
        """Test mood status categorization"""
        save_char = self.create_save_character()

        mood_test_cases = [
            (15, "very_unhappy", "😢", "red"),
            (35, "unhappy", "😔", "orange"),
            (50, "neutral", "😐", "yellow"),
            (70, "happy", "😊", "light_green"),
            (90, "very_happy", "😄", "green"),
        ]

        for (
            happiness,
            expected_status,
            expected_emoji,
            expected_color,
        ) in mood_test_cases:
            with self.subTest(happiness=happiness):
                save_char.current_happiness = happiness
                mood = save_char.get_mood_status()

                self.assertEqual(mood["status"], expected_status)
                self.assertEqual(mood["emoji"], expected_emoji)
                self.assertEqual(mood["color"], expected_color)

    def test_generate_happiness_message(self):
        """Test happiness change message generation"""
        save_char = self.create_save_character()

        message_test_cases = [
            (5, -12, "😰", "severely hurt"),
            (25, -6, "😔", "decreased"),
            (50, 0, "😊", "maintained"),
            (80, 7, "😄", "boosted"),
            (95, 12, "🎉", "greatly improved"),
        ]

        for energy, change, expected_emoji, expected_keyword in message_test_cases:
            with self.subTest(energy=energy, change=change):
                message = save_char.generate_happiness_message(
                    energy, change, 60, 60 + change, "Test Task"
                )

                self.assertIn(expected_emoji, message)
                self.assertIn(expected_keyword, message)
                self.assertIn("Test Task", message)

    def test_realistic_gameplay_scenarios(self):
        """Test realistic gameplay scenarios"""

        # Scenario 1: Tired character works and becomes unhappy
        tired_char = self.create_save_character(energy=15, happiness=60)
        initial_happiness = tired_char.current_happiness

        tired_char.apply_task_happiness_effect("Bug Fix")

        self.assertLess(
            tired_char.current_happiness,
            initial_happiness,
            "Tired character should lose happiness when working",
        )

        # Scenario 2: Energized character works and becomes happier
        energized_char = self.create_save_character(energy=85, happiness=60)
        initial_happiness = energized_char.current_happiness

        energized_char.apply_task_happiness_effect("Feature Development")

        self.assertGreater(
            energized_char.current_happiness,
            initial_happiness,
            "Energized character should gain happiness when working",
        )

    def test_extreme_values_handling(self):
        """Test handling of extreme energy values"""
        save_char = self.create_save_character()

        # Test extreme values
        extreme_test_cases = [0, -10, 100, 150]

        for extreme_energy in extreme_test_cases:
            with self.subTest(energy=extreme_energy):
                # Should not crash or raise exceptions
                change = save_char.calculate_happiness_change_for_energy(extreme_energy)
                self.assertIsInstance(
                    change,
                    int,
                    f"Should handle extreme energy {extreme_energy} gracefully",
                )

    def test_happiness_field_validation(self):
        """Test SaveCharacter field validation for happiness"""
        save_char = SaveCharacter(
            game_save=self.save,
            character=self.character,
            current_energy=50,
            current_happiness=50,
            current_effective_productivity=80,
        )

        # Valid values should pass
        save_char.full_clean()
        save_char.save()

        # Invalid happiness values should fail validation
        invalid_happiness_values = [-10, -1, 101, 150]

        for invalid_happiness in invalid_happiness_values:
            with self.subTest(happiness=invalid_happiness):
                save_char.current_happiness = invalid_happiness
                with self.assertRaises(
                    ValidationError,
                    msg=f"Should reject invalid happiness: {invalid_happiness}",
                ):
                    save_char.full_clean()

        # Reset to valid value
        save_char.current_happiness = 50
        save_char.full_clean()  # Should pass again


class SaveCharacterHappinessPerformanceTests(TestCase):
    """Test performance of happiness-energy calculations in SaveCharacter"""

    def setUp(self):
        """Set up performance test data"""
        self.user = User.objects.create_user(username="perfuser", password="perf123")
        self.character = Character.objects.create(
            first_name="Perf",
            last_name="Test",
            primary_role="backend",
            description="Test",
        )
        self.save = Save.objects.create(
            user=self.user,
            save_name="Performance Test",
            active=True,
            status="ONGOING",
            progress_percent=40,
            total_days=25
        )

    def test_happiness_calculation_performance(self):
        """Test performance of happiness calculations"""
        save_char = SaveCharacter.objects.create(
            game_save=self.save,
            character=self.character,
            current_energy=60,
            current_happiness=60,
        )


        # Time many happiness calculations
        start_time = time.time()

        for i in range(1000):  # 1000 calculations
            energy_level = 20 + (i % 80)  # Varied energy 20-99
            change = save_char.calculate_happiness_change_for_energy(energy_level)
            self.assertIsInstance(change, int)

        end_time = time.time()
        calculation_time = end_time - start_time

        # Should be very fast (< 0.1 seconds for 1000 calculations)
        self.assertLess(
            calculation_time,
            0.1,
            f"Happiness calculations too slow: {calculation_time:.3f}s for 1000 calculations",
        )

    def test_bulk_happiness_updates(self):
        """Test performance of multiple happiness updates"""

        # Create multiple characters
        characters = []
        for i in range(50):  # 50 characters
            new_character = Character.objects.create(
                first_name=f"Perf{i}",
                last_name="Test",
                primary_role="backend",
                description="Performance test character",
            )
            save_character = SaveCharacter.objects.create(
                game_save=self.save,
                character=new_character,
                current_energy=30 + (i % 60),  # Varied energy
                current_happiness=40 + (i % 50),  # Varied happiness
            )
            characters.append(save_character)

        # Time bulk updates
        start_time = time.time()

        for char in characters:
            char.apply_task_happiness_effect("Performance Test")

        end_time = time.time()
        bulk_time = end_time - start_time

        # Should complete reasonably fast (< 1 second for 50 characters)
        self.assertLess(
            bulk_time,
            1.0,
            f"Bulk happiness updates too slow: {bulk_time:.3f}s for 50 characters",
        )

    def test_string_representation(self):
        """Test __str__ method returns correct representation"""
        save_char = SaveCharacter.objects.create(
            game_save=self.save,
            character=self.character,
            current_energy=50,
            current_happiness=50,
        )

        expected_string = f"{self.character} in {self.save.save_name}"
        self.assertEqual(str(save_char), expected_string)