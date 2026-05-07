from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q

from projectManagerSim.models import Character, CharacterRelationship, SaveCharacter
from projectManagerSim.decorators import GameViewMixin
from django.views import View

from projectManagerSim.services.game.character_relationship_service import CharacterRelationshipService


class RelationshipsView(GameViewMixin, View):
    """
    Display team relationships in a character-centered view
    Shows relationships for selected character with energy cost info
    """
    
    def get(self, request, *args, **kwargs):
        save = self.save 
        
        # Get all characters in the current team
        team_characters = SaveCharacter.objects.filter(
            game_save=save
        ).select_related('character')
        
        # Get selected character (default to first)
        selected_char_id = request.GET.get('character_id')
        
        if selected_char_id:
            selected_save_char = team_characters.filter(
                character_id=selected_char_id
            ).first()
            if selected_save_char is None:
                selected_save_char = team_characters.first()
        else:
            selected_save_char = team_characters.first()
        
        if not selected_save_char:
            # No team yet
            return render(request, 'game/game_relationships.html', {
                'save': save,
                'team_characters': [],
                'selected_character': None,
                'relationships': [],
                'best_partners': [],
            })
        
        selected_char = selected_save_char.character
        
        # Get all relationships for selected character
        relationship_service = CharacterRelationshipService(selected_save_char)
        relationships_data = relationship_service.get_character_relationships(team_characters)
        
        # Get best task partners
        best_partners = relationship_service.get_best_partners(relationships_data)
        
        context = {
            'save': save,
            'in_game': True,
            'team_characters': team_characters,
            'selected_character': selected_char,
            'selected_save_char': selected_save_char,
            'relationships': relationships_data,
            'best_partners': best_partners,
            "tour_step": request.session.pop('tour_step', ''), 
        }
        
        return render(request, 'game/game_relationships.html', context)


@login_required
def relationships_view(request, save_id):
    """Wrapper for RelationshipsView"""
    view = RelationshipsView.as_view()
    return view(request, save_id=save_id)