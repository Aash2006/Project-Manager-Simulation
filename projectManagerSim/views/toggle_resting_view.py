import json
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views import View
from projectManagerSim.decorators import GameViewMixin
from projectManagerSim.models import SaveCharacter, Task
from projectManagerSim.services.game.character_relationship_service import CharacterRelationshipService

class ToggleRestingView(GameViewMixin, View):
    """
    Toggles resting of a SaveCharacter via AJAX POST.
    Returns updated HTML for the character card.
    """

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            save_character_id = data.get("save_character_id")
            is_resting = data.get("is_resting")

            if save_character_id is None or is_resting is None:
                return self._error_response("Missing save_character_id or is_resting", 400)

            save_character = self._get_save_character(save_character_id)

            if not save_character:
                return self._error_response("Character not found", 404)

            if save_character.game_save.user != request.user:
                return self._error_response("Not allowed to toggle rest", 403)
            
            
            self._toggle_rest(save_character, is_resting)

            return JsonResponse({
                "success": True,
                **self._render_partials(request, save_character)
            })

        except json.JSONDecodeError:
            return self._error_response("Invalid JSON", 400)
        except Exception as e:
            print(f"Exception: {str(e)}")
            return self._error_response(str(e), 500)



    def _get_save_character(self, sc_id):
        """Gets Save Character by ID"""
        return SaveCharacter.objects.select_related("game_save").filter(id=sc_id).first()

    def _toggle_rest(self, sc, is_resting):
        """Toggles rest of given SaveCharacter"""
        if not is_resting:
            sc.is_resting = False
            sc.save()
            return
        
        sc.task_assigned = None
        sc.is_resting = True
        sc.save()

    def _error_response(self, message, status):
        """Returns the error response for JSON"""
        return JsonResponse({"success": False, "message": message}, status=status)

    def _render_partials(self, request, save_character):
        """Creates Partials for SaveCharacter"""
        team_characters = SaveCharacter.objects.filter(
            game_save=self.engine.fetch('save')
        ).select_related('character')
        relationship_service = CharacterRelationshipService(save_character)
        relationships_data = relationship_service.get_character_relationships(team_characters)
        return {
            "character_card_html": render_to_string(
                "partials/teammate_card.html", 
                {"sc": save_character, "relationships": [[save_character.id, relationships_data]]},  
                request=request
            ),
        }