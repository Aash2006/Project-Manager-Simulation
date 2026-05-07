from django.test import TestCase
from projectManagerSim.models import Character


class CharacterModelTest(TestCase):
    """Test Character model with roles, traits, and personality types"""
    
    def setUp(self):
        """Create test characters"""
        self.frontend_char = Character.objects.create(
            first_name='Alice',
            last_name='Chen',
            description='Frontend developer',
            work_life_balance=60,
            primary_role='frontend',
            secondary_role='designer',
            personality_type='perfectionist_type',
            perfectionist=True,
            night_owl=True,
            works_well_under_pressure=False,
            team_player=False,
        )
        
        self.backend_char = Character.objects.create(
            first_name='Marcus',
            last_name='Johnson',
            description='Backend developer',
            work_life_balance=45,
            primary_role='backend',
            secondary_role=None,
            personality_type='speedster_type',
            perfectionist=False,
            night_owl=False,
            works_well_under_pressure=True,
            team_player=False,
        )
        
        self.fullstack_char = Character.objects.create(
            first_name='Charlie',
            last_name='Kim',
            description='Full-stack developer',
            work_life_balance=70,
            primary_role='fullstack',
            secondary_role=None,
            personality_type='team_player_type',
            perfectionist=False,
            night_owl=False,
            works_well_under_pressure=False,
            team_player=True,
        )
    
    # ========== ROLE TESTS ==========
    
    def test_primary_role_choices(self):
        """Test that primary role is from valid choices"""
        valid_roles = ['frontend', 'backend', 'fullstack', 'designer', 'tester']
        self.assertIn(self.frontend_char.primary_role, valid_roles)
        self.assertIn(self.backend_char.primary_role, valid_roles)
        self.assertIn(self.fullstack_char.primary_role, valid_roles)
    
    def test_secondary_role_optional(self):
        """Test that secondary role can be None"""
        self.assertEqual(self.frontend_char.secondary_role, 'designer')
        self.assertIsNone(self.backend_char.secondary_role)
        self.assertIsNone(self.fullstack_char.secondary_role)
    
    def test_get_full_name(self):
        """Test get_full_name() helper method"""
        self.assertEqual(self.frontend_char.get_full_name(), 'Alice Chen')
        self.assertEqual(self.backend_char.get_full_name(), 'Marcus Johnson')
    
    def test_get_role_display_full(self):
        """Test role display with primary and secondary"""
        # Character with secondary role
        alice_display = self.frontend_char.get_role_display_full()
        self.assertIn('Frontend Developer', alice_display)
        self.assertIn('UI/UX Designer', alice_display)
        
        # Character without secondary role
        marcus_display = self.backend_char.get_role_display_full()
        self.assertEqual(marcus_display, 'Backend Developer')
    
    # ========== TRAIT TESTS ==========
    
    def test_trait_booleans(self):
        """Test that traits are properly set"""
        # Alice has perfectionist and night_owl
        self.assertTrue(self.frontend_char.perfectionist)
        self.assertTrue(self.frontend_char.night_owl)
        self.assertFalse(self.frontend_char.works_well_under_pressure)
        self.assertFalse(self.frontend_char.team_player)
        
        # Marcus has works_well_under_pressure
        self.assertFalse(self.backend_char.perfectionist)
        self.assertTrue(self.backend_char.works_well_under_pressure)
        
        # Charlie has team_player
        self.assertTrue(self.fullstack_char.team_player)
    
    def test_get_traits_list(self):
        """Test get_traits_list() returns active traits"""
        alice_traits = self.frontend_char.get_traits_list()
        self.assertIn('Perfectionist', alice_traits)
        self.assertIn('Night Owl', alice_traits)
        self.assertEqual(len(alice_traits), 2)
        
        marcus_traits = self.backend_char.get_traits_list()
        self.assertIn('Works Well Under Pressure', marcus_traits)
        self.assertEqual(len(marcus_traits), 1)
        
        charlie_traits = self.fullstack_char.get_traits_list()
        self.assertIn('Team Player', charlie_traits)
        self.assertEqual(len(charlie_traits), 1)
    
    def test_get_traits_display(self):
        """Test get_traits_display() returns formatted string"""
        alice_display = self.frontend_char.get_traits_display()
        self.assertIn('Perfectionist', alice_display)
        self.assertIn('Night Owl', alice_display)
        
        # Character with no traits
        no_trait_char = Character.objects.create(
            first_name='Test',
            last_name='User',
            work_life_balance=50,
            primary_role='fullstack',
            perfectionist=False,
            night_owl=False,
            works_well_under_pressure=False,
            team_player=False,
        )
        self.assertEqual(no_trait_char.get_traits_display(), 'No special traits')
    
    # ========== PERSONALITY TYPE TESTS ==========
    
    def test_personality_type_choices(self):
        """Test that personality type is from valid choices"""
        valid_types = [
            'perfectionist_type',
            'speedster_type',
            'team_player_type',
            'solo_expert_type',
            'creative_type',
        ]
        self.assertIn(self.frontend_char.personality_type, valid_types)
        self.assertIn(self.backend_char.personality_type, valid_types)
        self.assertIn(self.fullstack_char.personality_type, valid_types)
    
    def test_get_personality_type_icon(self):
        """Test get_personality_type_icon() returns emoji"""
        alice_icon = self.frontend_char.get_personality_type_icon()
        self.assertIsInstance(alice_icon, str)
        self.assertGreater(len(alice_icon), 0)
    
    # ========== WORK LIFE BALANCE TESTS ==========
    
    def test_work_life_balance_range(self):
        """Test that WLB is within valid range"""
        self.assertGreaterEqual(self.frontend_char.work_life_balance, 0)
        self.assertLessEqual(self.frontend_char.work_life_balance, 100)
        
        self.assertGreaterEqual(self.backend_char.work_life_balance, 0)
        self.assertLessEqual(self.backend_char.work_life_balance, 100)
    
    # ========== STRING REPRESENTATION ==========
    
    def test_str_method(self):
        """Test __str__ method returns full name"""
        self.assertEqual(str(self.frontend_char), 'Alice Chen')
        self.assertEqual(str(self.backend_char), 'Marcus Johnson')
    
    # ========== EDGE CASES ==========
    
    def test_character_with_all_traits(self):
        """Test character with all traits enabled"""
        super_char = Character.objects.create(
            first_name='Super',
            last_name='Dev',
            work_life_balance=50,
            primary_role='fullstack',
            perfectionist=True,
            night_owl=True,
            works_well_under_pressure=True,
            team_player=True,
        )
        
        traits = super_char.get_traits_list()
        self.assertEqual(len(traits), 4)
        self.assertIn('Perfectionist', traits)
        self.assertIn('Night Owl', traits)
        self.assertIn('Works Well Under Pressure', traits)
        self.assertIn('Team Player', traits)
    
    def test_character_creation_defaults(self):
        """Test that character can be created with minimal fields"""
        minimal_char = Character.objects.create(
            first_name='Min',
            last_name='Char',
            work_life_balance=50,
        )
        
        # Should have default values
        self.assertEqual(minimal_char.primary_role, 'fullstack')
        self.assertEqual(minimal_char.personality_type, 'team_player_type')
        self.assertFalse(minimal_char.perfectionist)
        self.assertFalse(minimal_char.night_owl)
        self.assertFalse(minimal_char.works_well_under_pressure)
        self.assertFalse(minimal_char.team_player)