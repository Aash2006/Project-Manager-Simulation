from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from projectManagerSim.models import Save, SaveCharacter
from projectManagerSim.decorators import GameViewMixin


class SavePrecheckView(GameViewMixin, View):
    """
    Class-based view for prechecking warnings (low energy, low happiness, etc.)
    before applying a day. Scales easily for additional stats.
    There is no HTML view for this. This method is purely functional.
    
    #*
    """
    def get(self, request, save_id, *args, **kwargs):
        
        # mixin handles these checks for us
        try:
            save = Save.objects.get(id=save_id)
        except Save.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Save not found'}, status=404)

        if save.user != request.user:
            return JsonResponse({'success': False, 'message': 'Not allowed'}, status=403)
        

        character_warnings = []


        # Loop over characters and collect any character warnings (e.g. low energy)
        for save_character in self.engine.characters:
            if save_character.current_energy < 20 and not save_character.is_resting:
                character_warnings.append({
                    "type": "low_energy",
                    "first_name": save_character.character.first_name,
                    "last_name": save_character.character.last_name,
                    "current_energy": save_character.current_energy
                })

            if not save_character.is_resting and not save_character.task_assigned:
                character_warnings.append({
                    "type": "unassigned_task",
                    "first_name": save_character.character.first_name,
                    "last_name": save_character.character.last_name,
                })

        return JsonResponse({
            "success": True,
            "character_warnings": character_warnings
        })
