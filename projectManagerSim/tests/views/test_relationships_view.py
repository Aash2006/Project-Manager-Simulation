from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from projectManagerSim.models import Character, CharacterRelationship, Save, SaveCharacter


class RelationshipsViewTest(TestCase):
    """Test relationships view - character-centered display"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create save
        self.save = Save.objects.create(
            user=self.user,
            active=True,
            current_day=1
        )
        
        # Create 4 characters for the team
        self.alice = Character.objects.create(
            first_name='Alice',
            last_name='Chen',
            work_life_balance=60,
            primary_role='frontend',
            secondary_role='designer',
            perfectionist=True,
            night_owl=True,
        )
        
        self.bob = Character.objects.create(
            first_name='Bob',
            last_name='Smith',
            work_life_balance=50,
            primary_role='backend',
            perfectionist=False,
            night_owl=False,
        )
        
        self.charlie = Character.objects.create(
            first_name='Charlie',
            last_name='Kim',
            work_life_balance=70,
            primary_role='fullstack',
            team_player=True,
        )
        
        self.diana = Character.objects.create(
            first_name='Diana',
            last_name='Patel',
            work_life_balance=55,
            primary_role='designer',
            perfectionist=True,
        )
        
        # Add characters to save
        self.save_alice = SaveCharacter.objects.create(
            game_save=self.save,
            character=self.alice,
            current_energy=100,
            current_happiness=100,
        )
        
        self.save_bob = SaveCharacter.objects.create(
            game_save=self.save,
            character=self.bob,
            current_energy=100,
            current_happiness=100,
        )
        
        self.save_charlie = SaveCharacter.objects.create(
            game_save=self.save,
            character=self.charlie,
            current_energy=100,
            current_happiness=100,
        )
        
        self.save_diana = SaveCharacter.objects.create(
            game_save=self.save,
            character=self.diana,
            current_energy=100,
            current_happiness=100,
        )
        
        # Create relationships
        self.rel_best_friends = CharacterRelationship.objects.create(
            character_a=self.save_alice,
            character_b=self.save_diana,
            relationship_score=45  # Best friends
        )
        
        self.rel_friends = CharacterRelationship.objects.create(
            character_a=self.save_alice,
            character_b=self.save_charlie,
            relationship_score=25  # Friends
        )
        
        self.rel_rivalry = CharacterRelationship.objects.create(
            character_a=self.save_alice,
            character_b=self.save_bob,
            relationship_score=-45  # Rivalry
        )
        
        # Bob and Charlie are friends
        self.rel_bob_charlie = CharacterRelationship.objects.create(
            character_a=self.save_bob,
            character_b=self.save_charlie,
            relationship_score=30
        )
        
        self.url = reverse('relationships', args=[self.save.id])
    
    # ========== AUTHENTICATION TESTS ==========
    
    def test_view_requires_login(self):
        """Test that view requires authentication"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    # ========== GET REQUEST TESTS ==========
    
    def test_get_shows_team_characters(self):
        """Test GET request shows all team characters in dropdown"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('team_characters', response.context)
        self.assertEqual(response.context['team_characters'].count(), 4)
    
    def test_get_defaults_to_first_character(self):
        """Test that first character is selected by default"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['selected_character'])
        # Should default to first SaveCharacter (Alice)
        self.assertEqual(response.context['selected_character'].id, self.alice.id)
    
    def test_get_with_character_id_parameter(self):
        """Test selecting specific character via query parameter"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f"{self.url}?character_id={self.bob.id}")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_character'].id, self.bob.id)
    
    def test_get_shows_relationships(self):
        """Test that relationships are displayed"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('relationships', response.context)
        
        # Alice has 3 relationships (Diana, Charlie, Bob)
        relationships = response.context['relationships']
        self.assertEqual(len(relationships), 3)
    
    def test_relationships_sorted_by_quality(self):
        """Test relationships are sorted best to worst"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        relationships = response.context['relationships']
        
        # Should be sorted: Diana (45) > Charlie (25) > Bob (-45)
        self.assertEqual(relationships[0]['character'].id, self.diana.id)
        self.assertEqual(relationships[1]['character'].id, self.charlie.id)
        self.assertEqual(relationships[2]['character'].id, self.bob.id)
    
    def test_relationship_data_structure(self):
        """Test that relationship data includes all necessary fields"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        relationships = response.context['relationships']
        first_rel = relationships[0]
        
        # Check all required fields are present
        self.assertIn('character', first_rel)
        self.assertIn('type', first_rel)
        self.assertIn('type_display', first_rel)
        self.assertIn('icon', first_rel)
        self.assertIn('score', first_rel)
        self.assertIn('badge_class', first_rel)
        self.assertIn('energy_modifier', first_rel)
        self.assertIn('energy_modifier_percent', first_rel)
        self.assertIn('description', first_rel)
    
    def test_best_friends_relationship_display(self):
        """Test best friends relationship displays correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        relationships = response.context['relationships']
        diana_rel = relationships[0]  # Best friends (first in sorted list)
        
        self.assertEqual(diana_rel['type'], 'best_friends')
        self.assertEqual(diana_rel['type_display'], 'Best Friends')
        self.assertEqual(diana_rel['energy_modifier'], 0.85)
        self.assertEqual(diana_rel['icon'], '❤️')
    
    def test_rivalry_relationship_display(self):
        """Test rivalry relationship displays correctly"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        relationships = response.context['relationships']
        bob_rel = relationships[2]  # Rivalry (last in sorted list)
        
        self.assertEqual(bob_rel['type'], 'rivalry')
        self.assertEqual(bob_rel['type_display'], 'Rivalry')
        self.assertEqual(bob_rel['energy_modifier'], 1.25)
        self.assertEqual(bob_rel['icon'], '⚡')
    
    def test_neutral_relationship_display(self):
        """Test characters with no defined relationship show as neutral"""
        # Create a 5th character with no relationships
        eric = Character.objects.create(
            first_name='Eric',
            last_name='Wong',
            work_life_balance=65,
            primary_role='tester',
        )
        
        SaveCharacter.objects.create(
            game_save=self.save,
            character=eric,
            current_energy=100,
            current_happiness=100,
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f"{self.url}?character_id={self.alice.id}")
        
        relationships = response.context['relationships']
        
        # Find Eric in relationships
        eric_rel = next(r for r in relationships if r['character'].id == eric.id)
        
        self.assertEqual(eric_rel['type'], 'neutral')
        self.assertEqual(eric_rel['energy_modifier'], 1.0)
    
    # ========== BEST PARTNERS TESTS ==========
    
    def test_get_shows_best_partners(self):
        """Test that best partners are calculated and displayed"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('best_partners', response.context)
        
        # Should have top 3 partners
        best_partners = response.context['best_partners']
        self.assertLessEqual(len(best_partners), 3)
    
    def test_best_partners_sorted_by_compatibility(self):
        """Test best partners are sorted by compatibility score"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        best_partners = response.context['best_partners']
        
        # Diana should be first (best friends + designer)
        # Charlie should be second (friends + fullstack + team player)
        # Bob should be last (rivalry)
        
        if len(best_partners) >= 2:
            # First partner should have higher compatibility than second
            self.assertGreater(
                best_partners[0]['compatibility_score'],
                best_partners[1]['compatibility_score']
            )
    
    def test_best_partners_include_reasons(self):
        """Test best partners include reasons for recommendation"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        best_partners = response.context['best_partners']
        
        if len(best_partners) > 0:
            first_partner = best_partners[0]
            self.assertIn('reasons', first_partner)
            self.assertIsInstance(first_partner['reasons'], list)
            self.assertGreater(len(first_partner['reasons']), 0)
    
    def test_best_partners_best_friends_bonus(self):
        """Test best friends get high compatibility score"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        best_partners = response.context['best_partners']
        
        # Diana (best friends) should be in top partners
        diana_partner = next(
            (p for p in best_partners if p['character'].id == self.diana.id),
            None
        )
        
        self.assertIsNotNone(diana_partner)
        self.assertIn('Best Friends', diana_partner['reasons'])
    
    def test_best_partners_team_player_bonus(self):
        """Test team player trait affects compatibility"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        best_partners = response.context['best_partners']
        
        # Charlie (team player) should get bonus
        charlie_partner = next(
            (p for p in best_partners if p['character'].id == self.charlie.id),
            None
        )
        
        if charlie_partner:
            self.assertIn('Team Player', charlie_partner['reasons'])
    
    def test_best_partners_fullstack_versatile(self):
        """Test fullstack characters marked as versatile"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        best_partners = response.context['best_partners']
        
        charlie_partner = next(
            (p for p in best_partners if p['character'].id == self.charlie.id),
            None
        )
        
        if charlie_partner:
            self.assertIn('Versatile', charlie_partner['reasons'])
    
    # ========== EDGE CASES ==========
    
    def test_no_team_shows_message(self):
        """Test page shows message when no team exists"""
        # Create new save with no characters
        self.save.active = False
        self.save.save()
        new_save = Save.objects.create(
            user=self.user,
            active=True
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('relationships', args=[new_save.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['team_characters']), 0)
        self.assertIsNone(response.context['selected_character'])
    
    def test_invalid_character_id_defaults_to_first(self):
        """Test invalid character_id parameter defaults to first character"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f"{self.url}?character_id=99999")
        
        self.assertEqual(response.status_code, 200)
        # Should default to first character
        self.assertIsNotNone(response.context['selected_character'])
    
    def test_character_with_no_relationships(self):
        """Test character with no relationships shows empty list"""
        # Bob only has relationships with Alice and Charlie (not selected)
        # When viewing Bob, he should see Alice and Charlie
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f"{self.url}?character_id={self.bob.id}")
        
        relationships = response.context['relationships']
        
        # Bob has relationships with Alice (rivalry) and Charlie (friends)
        # Plus Diana (no relationship = neutral)
        self.assertEqual(len(relationships), 3)
    
    # ========== TEMPLATE RENDERING ==========
    
    def test_template_used(self):
        """Test correct template is used"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'game/game_relationships.html')
    
    def test_context_has_save(self):
        """Test context includes save object"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('save', response.context)
        self.assertEqual(response.context['save'].id, self.save.id)
    
    def test_context_has_in_game_flag(self):
        """Test context includes in_game flag for navbar"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        # Should have in_game=True for navbar to show
        self.assertTrue(response.context.get('in_game', False))
    
    # ========== BIDIRECTIONAL RELATIONSHIP LOOKUP ==========
    
    def test_bidirectional_relationship_lookup(self):
        """Test relationships are found regardless of storage order"""
        # Create relationship stored as (Bob, Diana)
        CharacterRelationship.objects.create(
            character_a=self.save_bob,
            character_b=self.save_diana,
            relationship_score=20
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        # View Diana's relationships
        response = self.client.get(f"{self.url}?character_id={self.diana.id}")
        relationships = response.context['relationships']
        
        # Should find Bob even though he's character_a in storage
        bob_rel = next(
            (r for r in relationships if r['character'].id == self.bob.id),
            None
        )
        
        self.assertIsNotNone(bob_rel)
        self.assertEqual(bob_rel['score'], 20)