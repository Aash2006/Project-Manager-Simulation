import json

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views import View

from projectManagerSim.decorators import GameViewMixin
from projectManagerSim.models import SaveCharacter
from projectManagerSim.models.task import Task


class GetLatestTaskView(GameViewMixin, View):
    """
    Handle getting current task for a SaveCharacter via AJAX POST.
    Returns HTML for the character card and task assign menu.
    """

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)

            save_character_id = data.get("save_character_id")

            if save_character_id is None:
                return self._error_response("Missing save_character_id", 400)
            
            save_character = self._get_save_character(save_character_id)
            if not save_character:
                return self._error_response("Character not found", 404)

            if save_character.game_save.user != request.user:
                return self._error_response("Not our character", 403)
            

            return JsonResponse({
                "success": True,
                **self._render_partials(request, save_character)
            })

        except json.JSONDecodeError:
            return self._error_response("Invalid JSON", 400)
        except Exception as e:
            return self._error_response(str(e), 500)

    def _get_save_character(self, sc_id):
        """Gets Save Character by ID"""
        return SaveCharacter.objects.select_related("game_save").filter(id=sc_id).first()

    def _error_response(self, message, status):
        """Returns the error response for JSON"""
        return JsonResponse({"success": False, "message": message}, status=status)

    def _render_partials(self, request, save_character):
        """Creates Partials for SaveCharacter"""

        return {
            "character_card_html": render_to_string(
                "partials/teammate_card.html", 
                {"sc": save_character}, 
                request=request
            ),
        }