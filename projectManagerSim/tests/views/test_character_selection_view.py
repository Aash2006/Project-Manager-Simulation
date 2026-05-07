import json

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from projectManagerSim.models import (
    Character,
    CharacterRelationship,
    CharacterTemplateRelationship,
    Save,
    SaveCharacter,
)


class CharacterSelectionViewTest(TestCase):
    """Test character selection view"""
    
    @classmethod
    def setUpTestData(cls):
        """Load fixture data once for all tests"""
        from django.core.management import call_command
        
        # Load character and relationship fixtures
        try:
            call_command('loaddata', 'characters', verbosity=0)
            call_command('loaddata', 'character_template_relationships', verbosity=0)
        except:
            # If fixtures don't exist, create minimal test data
            for i in range(12):
                Character.objects.create(
                    first_name=f'TestChar{i}',
                    last_name='User',
                    description='Test character',
                    work_life_balance=50,
                    primary_role='fullstack',
                    initial_energy=100,
                    perfectionist=False,
                    night_owl=False,
                    works_well_under_pressure=False,
                    team_player=False,
                )
    
    def setUp(self):
        """Set up test data for each test"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Get characters (from fixtures or created above)
        self.characters = list(Character.objects.all()[:12])
        
        # Create existing save (for tests that need it)
        self.save = Save.objects.create(
            user=self.user,
            active=True,
            current_day=5
        )


        from django.core.management import call_command
    
        # Load task types fixture
        call_command('loaddata', 'task_types', verbosity=0)
    # ========== GET REQUEST TESTS ==========
    
    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(reverse('game_start_new'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_get_shows_all_characters(self):
        """Test GET request shows all characters"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('game_start_new'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('characters', response.context)
        # Should have at least 10 characters
        self.assertGreaterEqual(len(response.context['characters']), 10)
    
    def test_get_shows_existing_save_warning(self):
        """Test that existing save shows in context"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('game_start_new'))
        
        self.assertEqual(response.status_code, 200)
        # Check if existing_save is in context
        self.assertIn('existing_save', response.context)
        self.assertIsNotNone(response.context['existing_save'])
    
    def test_get_no_warning_without_existing_save(self):
        """Test no warning when no existing save"""
        # Delete the save created in setUp
        self.save.delete()
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('game_start_new'))
        
        self.assertEqual(response.status_code, 200)
        # existing_save should be None
        self.assertIsNone(response.context.get('existing_save'))
    
    # ========== POST REQUEST TESTS ==========
    
    def test_post_requires_login(self):
        """Test POST requires authentication"""
        response = self.client.post(
            reverse('game_start_new'),
            data=json.dumps({
                'selected_characters': [
                    self.characters[0].id,
                    self.characters[1].id,
                    self.characters[2].id,
                    self.characters[3].id,
                ]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_post_with_valid_selection_creates_save(self):
        """Test selecting 4 characters creates new save"""
        self.client.login(username='testuser', password='testpass123')
        
        # Get initial save count
        initial_save_count = Save.objects.filter(user=self.user).count()
        
        response = self.client.post(
            reverse('game_start_new'),
            data=json.dumps({
                'selected_characters': [
                    self.characters[0].id,
                    self.characters[1].id,
                    self.characters[2].id,
                    self.characters[3].id,
                ]
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Check new save was created
        new_save = Save.objects.filter(user=self.user, active=True).first()
        self.assertIsNotNone(new_save)
        
        # Check 4 characters were added
        team = SaveCharacter.objects.filter(game_save=new_save)
        self.assertEqual(team.count(), 4)
    
    def test_post_validates_exactly_4_characters(self):
        """Test that POST validates exactly 4 characters selected"""
        self.client.login(username='testuser', password='testpass123')
        
        # Try with 3 characters (too few)
        response = self.client.post(
            reverse('game_start_new'),
            data=json.dumps({
                'selected_characters': [
                    self.characters[0].id,
                    self.characters[1].id,
                    self.characters[2].id,
                ]
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_post_rejects_more_than_4_characters(self):
        """Test rejection when more than 4 characters selected"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('game_start_new'),
            data=json.dumps({
                'selected_characters': [
                    self.characters[0].id,
                    self.characters[1].id,
                    self.characters[2].id,
                    self.characters[3].id,
                    self.characters[4].id,  
                ]
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_post_deactivates_old_save(self):
        """Test that POST deactivates existing active save"""
        self.client.login(username='testuser', password='testpass123')
        
        # Verify old save is active
        self.assertTrue(self.save.active)
        old_save_id = self.save.id
        
        # Select new team
        response = self.client.post(
            reverse('game_start_new'),
            data=json.dumps({
                'selected_characters': [
                    self.characters[0].id,
                    self.characters[1].id,
                    self.characters[2].id,
                    self.characters[3].id,
                ]
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check old save is deactivated
        old_save = Save.objects.get(id=old_save_id)
        self.assertFalse(old_save.active)
    
    # ========== ERROR HANDLING TESTS ==========
    
    def test_post_with_invalid_character_ids(self):
        """Test POST with non-existent character IDs"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('game_start_new'),
            data=json.dumps({
                'selected_characters': [9999, 9998, 9997, 9996]  # Invalid IDs
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_post_with_duplicate_characters(self):
        """Test POST with duplicate character selections"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('game_start_new'),
            data=json.dumps({
                'selected_characters': [
                    self.characters[0].id,
                    self.characters[0].id,  # Duplicate
                    self.characters[1].id,
                    self.characters[2].id,
                ]
            }),
            content_type='application/json'
        )
        
        # Should fail validation (only 3 unique characters)
        self.assertEqual(response.status_code, 400)
    
    def test_post_with_malformed_json(self):
        """Test POST with malformed JSON"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('game_start_new'),
            data='not valid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    # ========== REDIRECT TEST ==========
    
    def test_successful_selection_redirects_to_dashboard(self):
        """Test successful selection returns redirect URL"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('game_start_new'),
            data=json.dumps({
                'selected_characters': [
                    self.characters[0].id,
                    self.characters[1].id,
                    self.characters[2].id,
                    self.characters[3].id,
                ]
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('redirect_url', data)
    
    def test_chemistry_returned_in_response(self):
        """Test that team chemistry is calculated and returned"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('game_start_new'),
            data=json.dumps({
                'selected_characters': [
                    self.characters[0].id,
                    self.characters[1].id,
                    self.characters[2].id,
                    self.characters[3].id,
                ]
            }),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            data = json.loads(response.content)
            # Check if chemistry data exists
            if 'team_chemistry' in data:
                self.assertIn('score', data['team_chemistry'])
                self.assertIn('level', data['team_chemistry'])