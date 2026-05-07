from django.shortcuts import render
from django.views.generic import View
from projectManagerSim.decorators import GameViewMixin
from projectManagerSim.models.save_character import SaveCharacter
from projectManagerSim.services.game.character_relationship_service import CharacterRelationshipService

class GameCharacterListView(GameViewMixin, View):
    """display all characters"""
    
    def get(self, request):
        user = request.user

        save = self.engine.fetch('save')

        save_characters = save.characters.order_by('current_energy')
        team_characters = SaveCharacter.objects.filter(game_save=save).select_related('character')

        relationships = []
        
        for selected_save_char in save_characters:
            # Get all relationships for selected character
            relationship_service = CharacterRelationshipService(selected_save_char)
            relationships_data = relationship_service.get_character_relationships(team_characters)
            relationships.append([selected_save_char.id, relationships_data])
        
        context = {
            "current_user": user,
            "save": save,
            "characters": save_characters,
            "relationships": relationships,
            "save_characters_id_list" : list(save_characters.values_list('pk', flat=True)),
            "in_game" : True, 
            "tour_step": request.session.pop('tour_step', ''), 
        }
        return render(request, "game_characters.html", context)
