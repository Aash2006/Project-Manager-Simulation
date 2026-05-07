from projectManagerSim.models.character_relationships import CharacterRelationship

class CharacterRelationshipService:
    """Handles getting relationships between characters"""
    def __init__(self, sc):
        self.sc = sc


    def _build_rel_data(self, save_char, rel):
        if rel:
            return {
                'character': save_char.character,
                'save_character': save_char,
                'type': rel.relationship_type,
                'type_display': rel.relationship_type_display,
                'icon': rel.get_icon(),
                'score': rel.relationship_score,
                'badge_class': rel.get_badge_class(),
                'energy_modifier': rel.energy_modifier,
                'energy_modifier_percent': rel.energy_modifier_percent,
                'description': rel.get_description(),
            }
        return {
            'character': save_char.character,
            'save_character': save_char,
            'type': 'neutral',
            'type_display': 'Neutral',
            'icon': '😐',
            'score': 0,
            'badge_class': 'badge-secondary',
            'energy_modifier': 1.0,
            'energy_modifier_percent': '0%',
            'description': 'Professional relationship',
        }

    def get_character_relationships(self, team_characters):
            """
            Get all relationships for a character with their teammates
            
            Returns:
                list: Relationship data with energy modifiers and descriptions
            """
            relationships = []
            
            for save_char in team_characters:
                teammate = save_char
                
                # Skip self
                if teammate.id == self.sc.id:
                    continue
                
                # Get relationship
                rel = CharacterRelationship.get_relationship_between(self.sc, teammate)
                
                rel_data = self._build_rel_data(save_char, rel)
                
                relationships.append(rel_data)
            
            # Sort by relationship quality (best first)
            relationships.sort(key=lambda x: x['score'], reverse=True)
            
            return relationships
        
    def get_best_partners(self, relationships_data):
            """
            Determine best task partners based on relationships and roles
            
            Returns:
                list: Top 3 partners with reasons
            """
            partners = []
            
            for rel in relationships_data:
                teammate = rel['character']
                
                # Calculate compatibility score
                compatibility_score = 0
                reasons = []
                
                # Relationship bonus/penalty
                if rel['type'] == 'best_friends':
                    compatibility_score += 100
                    reasons.append('Best Friends')
                elif rel['type'] == 'friends':
                    compatibility_score += 50
                    reasons.append('Friends')
                elif rel['type'] == 'tension':
                    compatibility_score -= 50
                    reasons.append('⚠️ Tension')
                elif rel['type'] == 'rivalry':
                    compatibility_score -= 100
                    reasons.append('⚠️ Rivalry')
                
                # Role complementarity
                if teammate.primary_role == 'fullstack':
                    compatibility_score += 20
                    reasons.append('Versatile')
                
                if teammate.team_player:
                    compatibility_score += 10
                    reasons.append('Team Player')
                
                # Energy efficiency
                if rel['energy_modifier'] < 1.0:
                    reasons.append(f"Efficient ({rel['energy_modifier_percent']} energy)")
                elif rel['energy_modifier'] > 1.0:
                    reasons.append(f"⚠️ Costly ({rel['energy_modifier_percent']} energy)")
                
                partners.append({
                    'character': teammate,
                    'compatibility_score': compatibility_score,
                    'reasons': reasons,
                    'relationship': rel,
                })
            
            # Sort by compatibility
            partners.sort(key=lambda x: x['compatibility_score'], reverse=True)
            
            # Return top 3
            return partners[:3]