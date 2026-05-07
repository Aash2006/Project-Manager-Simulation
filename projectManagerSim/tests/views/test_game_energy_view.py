from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from projectManagerSim.models import (
    Save, SaveCharacter, Character, Task, TaskType,
    CharacterRelationship, CharacterTemplateRelationship
)


def create_character(first_name='Test', last_name='Character', primary_role='backend'):
    return Character.objects.create(
        first_name=first_name,
        last_name=last_name,
        primary_role=primary_role,
        description='Test character',
        work_life_balance=50,
    )


def create_task_type():
    return TaskType.objects.create(
        task_type_name='Backend Development',
        required_role='backend'
    )


def create_save(user):
    return Save.objects.create(
        user=user,
        active=True
    )


def create_save_character(save, character, current_energy=100):
    return SaveCharacter.objects.create(
        game_save=save,
        character=character,
        current_energy=current_energy,
        current_happiness=80,
    )




class RelationshipEnergyModifierTests(TestCase):
    """Test that relationship energy modifiers work correctly during gameplay"""
    
    def setUp(self):
        """Set up test data with characters and relationships"""
        self.client = Client()
        self.user = User.objects.create_user('testuser', password='pass')
        self.client.login(username='testuser', password='pass')
        
        # Create characters
        self.char_a = create_character('Alice', 'Test', 'backend')
        self.char_b = create_character('Bob', 'Test', 'backend')
        self.char_c = create_character('Charlie', 'Test', 'backend')
        self.char_d = create_character('Diana', 'Test', 'backend')
        
        # Create save
        self.save = create_save(self.user)
        
        # Create SaveCharacters
        self.save_char_a = create_save_character(self.save, self.char_a, 100)
        self.save_char_b = create_save_character(self.save, self.char_b, 100)
        self.save_char_c = create_save_character(self.save, self.char_c, 100)
        self.save_char_d = create_save_character(self.save, self.char_d, 100)
        
        # Create relationships (per-save)
        CharacterRelationship.objects.create(
            character_a=self.save_char_a,
            character_b=self.save_char_b,
            relationship_score=45  # Best friends
        )
        
        CharacterRelationship.objects.create(
            character_a=self.save_char_c,
            character_b=self.save_char_d,
            relationship_score=-45  # Rivals
        )
    
    def test_best_friends_reduce_energy_cost(self):
        """Test that best friends working together use less energy"""
        from projectManagerSim.services.game.character_work_service import CharacterWorkService
        
        # Create task
        task_type = create_task_type()
        task = Task.objects.create(
            name='Test Task',
            game_save=self.save,
            task_type=task_type,
            time_to_complete=2,
        )
        
        # Work Alice and Bob together (best friends)
        service = CharacterWorkService(self.save_char_a)
        task_workers = [self.save_char_a, self.save_char_b]
        
        # Get relationship modifier
        modifier = service._get_relationship_modifier(task_workers)
        
        # Best friends should have 0.85 modifier (15% discount)
        self.assertAlmostEqual(modifier, 0.85, places=2)
    
    def test_rivals_increase_energy_cost(self):
        """Test that rivals working together use more energy"""
        from projectManagerSim.services.game.character_work_service import CharacterWorkService
        
        # Work Charlie and Diana together (rivals)
        service = CharacterWorkService(self.save_char_c)
        task_workers = [self.save_char_c, self.save_char_d]
        
        # Get relationship modifier
        modifier = service._get_relationship_modifier(task_workers)
        
        # Rivals should have 1.25 modifier (25% penalty)
        self.assertAlmostEqual(modifier, 1.25, places=2)
    
    def test_neutral_characters_no_modifier(self):
        """Test that characters with no relationship have neutral modifier"""
        from projectManagerSim.services.game.character_work_service import CharacterWorkService
        
        # Work Alice and Charlie together (no relationship)
        service = CharacterWorkService(self.save_char_a)
        task_workers = [self.save_char_a, self.save_char_c]
        
        # Get relationship modifier
        modifier = service._get_relationship_modifier(task_workers)
        
        # Neutral should have 1.0 modifier (no change)
        self.assertAlmostEqual(modifier, 1.0, places=2)
    
    def test_working_alone_no_modifier(self):
        """Test that working alone has no relationship modifier"""
        from projectManagerSim.services.game.character_work_service import CharacterWorkService
        
        # Work alone
        service = CharacterWorkService(self.save_char_a)
        task_workers = [self.save_char_a]
        
        # Get relationship modifier
        modifier = service._get_relationship_modifier(task_workers)
        
        # Should be 1.0 (no modifier when alone)
        self.assertEqual(modifier, 1.0)
    
    def test_energy_modifier_applied_during_work(self):
        """Integration test: verify energy modifiers apply during actual work"""
        from projectManagerSim.services.game.character_work_service import CharacterWorkService
        
        # Create task
        task_type = create_task_type()
        task = Task.objects.create(
            name='Test Task',
            game_save=self.save,
            task_type=task_type,
            time_to_complete=2,
        )
        
        # Set initial energy
        self.save_char_a.current_energy = 100
        self.save_char_a.save()
        
        self.save_char_b.current_energy = 100
        self.save_char_b.save()
        
        # Work Alice and Bob together (best friends)
        service_a = CharacterWorkService(self.save_char_a)
        result_a = service_a.process_working(
            task=task,
            team_size=2,
            required_size=2,
            task_workers=[self.save_char_a, self.save_char_b]
        )
        
        # Alice should use less energy due to best friend bonus
        # Base energy: 10, best friends modifier: 0.85, role match: 0.75
        # Total multiplier ≈ 0.85 * 0.75 * 1.0 (WLB) = 0.6375
        # Energy cost: 10 * 0.6375 ≈ 6-7
        # Expected remaining: 100 - 6-7 = 93-94
        self.save_char_a.refresh_from_db()
        self.assertGreater(self.save_char_a.current_energy, 90)
        self.assertLess(self.save_char_a.current_energy, 100)
    
    def test_rival_energy_penalty_during_work(self):
        """Test that rivals working together actually consume more energy"""
        from projectManagerSim.services.game.character_work_service import CharacterWorkService
        
        # Create task
        task_type = create_task_type()
        task = Task.objects.create(
            name='Test Task',
            game_save=self.save,
            task_type=task_type,
            time_to_complete=2,
        )
        
        # Set initial energy
        self.save_char_c.current_energy = 100
        self.save_char_c.save()
        
        self.save_char_d.current_energy = 100
        self.save_char_d.save()
        
        # Work Charlie and Diana together (rivals)
        service_c = CharacterWorkService(self.save_char_c)
        result_c = service_c.process_working(
            task=task,
            team_size=2,
            required_size=2,
            task_workers=[self.save_char_c, self.save_char_d]
        )
        
        # Charlie should use MORE energy due to rivalry penalty
        # Base energy: 10, rivals modifier: 1.25, role match: 0.75
        # Total multiplier ≈ 1.25 * 0.75 * 1.0 = 0.9375
        # Energy cost: 10 * 0.9375 ≈ 9-10
        # Expected remaining: 100 - 9-10 = 90-91
        self.save_char_c.refresh_from_db()
        self.assertLess(self.save_char_c.current_energy, 92)
        self.assertGreater(self.save_char_c.current_energy, 88)