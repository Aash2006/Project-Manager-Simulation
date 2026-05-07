import json
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views import View
from projectManagerSim.decorators import GameViewMixin
from projectManagerSim.models import SaveCharacter, Task
from projectManagerSim.services.game.character_relationship_service import CharacterRelationshipService

class RemoveTaskView(GameViewMixin, View):
    """
    Removes a Task from a SaveCharacter via AJAX POST.
    Returns updated HTML for the character card and task assign menu.
    """

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            save_character_id = data.get("save_character_id")

            if not save_character_id:
                return self._error_response("Missing save_character_id", 400)

            save_character = self._get_save_character(save_character_id)

            if not save_character:
                return self._error_response("Character not found", 404)

            if save_character.game_save.user != request.user:
                return self._error_response("Not allowed to remove this task", 403)
            
            task = save_character.task_assigned
            if not task:
                return self._error_response("No task to remove", 400)
            
            self._remove_task(save_character)

            return JsonResponse({
                "success": True,
                **self._render_partials(request, save_character, task)
            })

        except json.JSONDecodeError:
            return self._error_response("Invalid JSON", 400)
        except Exception as e:
            print(f"Exception: {str(e)}")
            return self._error_response(str(e), 500)



    def _get_save_character(self, sc_id):
        """Gets Save Character by ID"""
        return SaveCharacter.objects.select_related("game_save").filter(id=sc_id).first()

    def _remove_task(self, sc):
        """Removes SaveCharacter's Assigned Task"""
        sc.task_assigned = None
        sc.save()

    def _error_response(self, message, status):
        """Returns the error response for JSON"""
        return JsonResponse({"success": False, "message": message}, status=status)

    def _render_partials(self, request, save_character, task):
        """Creates Partials for SaveCharacter"""
        save = self.engine.fetch("save")
        all_save_chars = SaveCharacter.objects.filter(game_save=save)
        
        tasks = (Task.objects.filter(game_save=save, is_completed=False)
                 .filter(unlocks_at_percent__lte=save.progress_percent))
        team_characters = SaveCharacter.objects.filter(
            game_save=save
        ).select_related('character')
        relationship_service = CharacterRelationshipService(save_character)
        relationships_data = relationship_service.get_character_relationships(team_characters)
        return {
            "character_card_html": render_to_string(
                "partials/teammate_card.html", 
                {"sc": save_character, "relationships": [[save_character.id, relationships_data]]}, 
                request=request
            ),
            "task_assign_menu_html": render_to_string(
                "partials/task_assign_menu.html",
                {"save_characters": all_save_chars},
                request=request,
            ),
            "task_page_html": render_to_string(
                "partials/task_page.html",
                {
                    "current_user": request.user,
                    "save": save,
                    "tasks": tasks,
                    "save_characters": all_save_chars,
                    "save_characters_id_list": list(all_save_chars.values_list("pk", flat=True)),
                    "in_game": True,
                    "curr_task": task,
                },
                request=request,
            ),
        }