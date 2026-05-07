from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User
from projectManagerSim.models import Character, Save, SaveCharacter, CharacterRelationship, Task, TaskType
from projectManagerSim.services import CharacterWorkService, WorkResult

class CharacterWorkServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="workeruser", password="password")
        self.game_save = Save.objects.create(
            user=self.user, 
            save_name="Work Save", 
            total_days=30, 
            current_day=1
        )
        
        # Create a generic character template
        self.char_template = Character.objects.create(
            first_name="Bob", 
            primary_role="Developer",
            work_life_balance=50  # Factor 0.0
        )
        
        self.save_char = SaveCharacter.objects.create(
            game_save=self.game_save,
            character=self.char_template,
            current_energy=50,
            current_happiness=50
        )
        self.save_char.current_energy=50
        self.save_char.current_happiness=50
        self.save_char.save()
        
        self.service = CharacterWorkService(self.save_char)
        
        # Setup a dummy task
        self.task_type = TaskType.objects.create(task_type_name="Coding")
        self.task = Task.objects.create(
            name="Test Task",
            time_to_complete=4,
            task_type=self.task_type,
            energy_cost=1,
        )

    ## --- RESTING TESTS ---

    def test_process_resting_basic(self):
        """Standard recovery: 50 + 20 = 70 energy"""
        self.save_char.current_energy = 50
        self.service.process_resting()
        
        self.save_char.refresh_from_db()
        self.assertEqual(self.save_char.current_energy, 70)
        self.assertEqual(self.save_char.current_happiness, 60)

    def test_night_owl_recovery(self):
        """Night owls should recover 35 base instead of 20"""
        self.char_template.night_owl = True
        self.char_template.save()
        
        self.save_char.current_energy = 50
        self.service.process_resting()
        
        self.save_char.refresh_from_db()
        self.assertEqual(self.save_char.current_energy, 85)

    ## --- IDLE TESTS ---

    def test_process_idle_penalties(self):
        """Idle state should penalize energy and happiness"""
        self.service.process_idle()
        self.save_char.refresh_from_db()
        
        self.assertEqual(self.save_char.current_energy, 40)
        self.assertEqual(self.save_char.current_happiness, 45)

    ## --- WORKING & RELATIONSHIP TESTS ---

    def test_calculate_energy_multiplier_with_rival(self):
        """Test that energy costs spike when working with a rival"""
        rival_template = Character.objects.create(first_name="Rival")
        rival_save_char = SaveCharacter.objects.create(game_save=self.game_save, character=rival_template)
        
        CharacterRelationship.objects.create(
            character_a=self.save_char,
            character_b=rival_save_char,
            relationship_score=-50
        )
        
        task_workers = [self.save_char, rival_save_char]
        
        multiplier = self.service._calculate_total_energy_multiplier(
            self.task, team_size=2, required_size=2, task_workers=task_workers
        )
        
        self.assertAlmostEqual(multiplier, 1.625)

    def test_role_matching_efficiency(self):
        """Energy cost should be lower (0.75) if primary role matches task"""
        # Set task requirement
        self.task_type.required_role = "Developer"
        self.task_type.save()
        
        # Character is a Developer
        modifier = self.service._get_role_modifier(self.task)
        self.assertEqual(modifier, 0.75)
    ## --- RANDOM TESTS ---

    @patch('random.random')
    def test_work_low_energy_failure(self, mock_random):
        """Force a failure outcome when working on low energy"""
        mock_random.return_value = 0.9

        self.save_char.current_energy = 30
        self.save_char.save()
        result = self.service.process_working(self.task, 1, 1)
        
        self.assertEqual(result.progress_points, -30)
        self.assertIn("failed due to low energy", result.warning)

    @patch('random.random')
    def test_work_low_energy_success(self, mock_random):
        """Force a success outcome even on low energy"""
        mock_random.return_value = 0.1 
        
        self.save_char.current_energy = 30
        self.save_char.save()
        result = self.service.process_working(self.task, 1, 1)
        
        self.assertEqual(result.progress_points, 20)
        self.assertIn("working on low energy", result.warning)

    def test_understaffed_penalty(self):
        """Progress should be negative if not enough people are on the task"""
        # Required 2, only 1 assigned
        self.save_char.current_energy = 90
        self.save_char.save()
        result = self.service.process_working(self.task, team_size=1, required_size=2)
        
        self.assertIn("understaffed", result.warning)
        self.assertEqual(result.progress_points, -20)

    def test_overstaffed_penalty_applied(self):
        """Overstaffed task should apply 1.20 energy multiplier"""
        self.save_char.current_energy = 90
        self.save_char.save()
        result = self.service.process_working(self.task, team_size=3, required_size=2)
        
        # Should still make progress but energy cost was higher
        self.assertEqual(result.progress_points, 25)

    def test_team_player_no_overstaffing_penalty(self):
        """Team player trait should negate the overstaffing energy penalty"""
        self.char_template.team_player = True
        self.char_template.save()
        
        normal_service = CharacterWorkService(self.save_char)
        team_player_service = CharacterWorkService(self.save_char)
        
        # Both overstaffed, but team player should cost less energy
        self.save_char.current_energy = 90
        self.save_char.save()
        team_player_service.process_working(self.task, team_size=3, required_size=2)
        self.save_char.refresh_from_db()
        team_player_energy = self.save_char.current_energy
        
        self.char_template.team_player = False
        self.char_template.save()
        self.save_char.current_energy = 90
        self.save_char.save()
        normal_service.process_working(self.task, team_size=3, required_size=2)
        self.save_char.refresh_from_db()
        normal_energy = self.save_char.current_energy
        
        # Team player should have more energy remaining (paid less)
        self.assertGreater(team_player_energy, normal_energy)