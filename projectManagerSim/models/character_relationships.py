from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from projectManagerSim.models.save_character import SaveCharacter


class CharacterRelationship(models.Model):
    """
    Defines the relationship between two characters.
    Affects energy costs and productivity when working together.
    
    RELATIONSHIP SCORE RANGES:
    +40 to +50  = Best Friends (strong positive chemistry)
    +15 to +39  = Friends (positive chemistry)
    -14 to +14  = Neutral (no special chemistry)
    -15 to -39  = Tension (negative chemistry)
    -40 to -50  = Rivalry (strong negative chemistry)
    
    ENERGY EFFECTS WHEN WORKING TOGETHER:
    Best Friends: -15% energy cost each
    Friends:      -10% energy cost each
    Neutral:       No effect
    Tension:      +10% energy cost each
    Rivalry:      +25% energy cost each
    """
    
    character_a = models.ForeignKey(
        SaveCharacter,
        on_delete=models.CASCADE,
        related_name='relationships_from',
        help_text="First character in the relationship"
    )
    
    character_b = models.ForeignKey(
        SaveCharacter,
        on_delete=models.CASCADE,
        related_name='relationships_to',
        help_text="Second character in the relationship"
    )
    
    relationship_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(-50), MaxValueValidator(50)],
        help_text="Relationship strength: -50 (rivalry) to +50 (best friends)"
    )
    
    class Meta:
        # Ensure each pair of characters only has one relationship
        unique_together = ['character_a', 'character_b']
        ordering = ['character_a__character__first_name', 'character_b__character__first_name']
        verbose_name = "Character Relationship"
        verbose_name_plural = "Character Relationships"
    
    def __str__(self):
        return f"{self.character_a.character.get_full_name()} ↔ {self.character_b.character.get_full_name()} ({self.relationship_type_display})"
    
    # ========== RELATIONSHIP TYPE PROPERTIES ==========
    
    @property
    def relationship_type(self):
        """Returns the relationship type based on score"""
        if self.relationship_score >= 40:
            return 'best_friends'
        elif self.relationship_score >= 15:
            return 'friends'
        elif self.relationship_score >= -14:
            return 'neutral'
        elif self.relationship_score >= -39:
            return 'tension'
        else:
            return 'rivalry'
    
    @property
    def relationship_type_display(self):
        """Returns human-readable relationship type"""
        type_map = {
            'best_friends': 'Best Friends',
            'friends': 'Friends',
            'neutral': 'Neutral',
            'tension': 'Tension',
            'rivalry': 'Rivalry'
        }
        return type_map.get(self.relationship_type, 'Unknown')
    
    @property
    def energy_modifier(self):
        """
        Returns the energy cost modifier when these characters work together.
        
        Returns:
            float: Multiplier for energy cost (0.85 = -15%, 1.25 = +25%)
        """
        modifier_map = {
            'best_friends': 0.85,  # -15% energy cost
            'friends': 0.90,       # -10% energy cost
            'neutral': 1.00,       # No change
            'tension': 1.10,       # +10% energy cost
            'rivalry': 1.25        # +25% energy cost
        }
        return modifier_map.get(self.relationship_type, 1.00)
    
    @property
    def energy_modifier_percent(self):
        """Returns energy modifier as percentage string for display"""
        modifier = self.energy_modifier
        if modifier < 1.0:
            percent = round((1.0 - modifier) * 100)
            return f"-{percent}%"
        elif modifier > 1.0:
            percent = round((modifier - 1.0) * 100)
            return f"+{percent}%"
        else:
            return "0%"
    
    # ========== HELPER METHODS ==========
    
    def get_icon(self):
        """Returns emoji/icon for relationship type"""
        icon_map = {
            'best_friends': '❤️',
            'friends': '😊',
            'neutral': '😐',
            'tension': '😬',
            'rivalry': '⚡'
        }
        return icon_map.get(self.relationship_type, '❓')
    
    def get_badge_class(self):
        """Returns CSS class for relationship badge"""
        class_map = {
            'best_friends': 'badge-success',
            'friends': 'badge-primary',
            'neutral': 'badge-secondary',
            'tension': 'badge-warning',
            'rivalry': 'badge-danger'
        }
        return class_map.get(self.relationship_type, 'badge-secondary')
    
    def get_description(self):
        """Returns description of relationship"""
        desc_map = {
            'best_friends': 'Work exceptionally well together',
            'friends': 'Enjoy working together',
            'neutral': 'Professional relationship',
            'tension': 'Some friction when working together',
            'rivalry': 'Clash frequently - avoid pairing'
        }
        return desc_map.get(self.relationship_type, '')
    
    # ========== RELATIONSHIP EVOLUTION (for future dynamic relationships) ==========
    
    def improve_relationship(self, amount=5):
        """
        Improve relationship score (successful collaboration, positive events)
        
        Args:
            amount (int): How much to improve (default: 5)
        """
        self.relationship_score = min(50, self.relationship_score + amount)
        self.save()
    
    def worsen_relationship(self, amount=5):
        """
        Worsen relationship score (failed tasks, negative events)
        
        Args:
            amount (int): How much to worsen (default: 5)
        """
        self.relationship_score = max(-50, self.relationship_score - amount)
        self.save()


    @staticmethod
    def get_relationship_between(char_a, char_b):
        """
        Get relationship between two characters (bidirectional lookup).
        
        Args:
            char_a (Character): First character
            char_b (Character): Second character
        
        Returns:
            CharacterRelationship or None: The relationship if it exists
        """
        # Check both directions since relationship can be stored either way
        try:
            return CharacterRelationship.objects.get(
                character_a=char_a,
                character_b=char_b
            )
        except CharacterRelationship.DoesNotExist:
            try:
                return CharacterRelationship.objects.get(
                    character_a=char_b,
                    character_b=char_a
                )
            except CharacterRelationship.DoesNotExist:
                return None
    
    @staticmethod
    def get_energy_modifier_between(char_a, char_b):
        """
        Get energy modifier between two characters.
        
        Args:
            char_a (Character): First character
            char_b (Character): Second character
        
        Returns:
            float: Energy modifier (1.0 if no relationship exists)
        """
        relationship = CharacterRelationship.get_relationship_between(char_a, char_b)
        if relationship:
            return relationship.energy_modifier
        return 1.0  # Neutral if no relationship defined
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure character_a and character_b are not the same
        and to maintain consistent ordering (prevent duplicate relationships)
        """
        if self.character_a == self.character_b:
            raise ValueError("A character cannot have a relationship with themselves")
        
        # Always store relationships in consistent order (lower ID first)
        # This prevents duplicates like (Alice, Bob) and (Bob, Alice)
        if self.character_a.id and self.character_b.id:
            if self.character_a.id > self.character_b.id:
                self.character_a, self.character_b = self.character_b, self.character_a
        
        super().save(*args, **kwargs)


#
# # Get relationship between two characters:
# relationship = CharacterRelationship.get_relationship_between(alice, bob)
# print(relationship.relationship_type_display)  # "Rivalry"
# print(relationship.energy_modifier)  # 1.25 (25% more energy cost)
#
# # Get all relationships for a character:
# alice_relationships = CharacterRelationship.objects.filter(
#     models.Q(character_a=alice) | models.Q(character_b=alice)
# )
#
# # Calculate energy cost when Alice and Bob work together:
# base_energy = 10
# modifier = CharacterRelationship.get_energy_modifier_between(alice, bob)
# actual_energy = base_energy * modifier  # 10 * 1.25 = 12.5
#
# # Improve relationship after successful task:
# relationship.improve_relationship(5)  # +5 to relationship score
#
# # Check if characters are friends:
# if relationship.relationship_type in ['best_friends', 'friends']:
#     print("They work well together!")
#