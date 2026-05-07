import json

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View

from projectManagerSim.decorators import GameViewMixin
from projectManagerSim.models import Save, SaveCharacter, Task, Decision
from projectManagerSim.services.game import DayProgressService


class StartDayView(GameViewMixin, View):
    """
    Handles the progression of a game day.
    Orchestrates character work, task progress, and overall project completion.
    """

    def post(self, request, *args, **kwargs):
        try:
            print("===Start Day View===")
            save_id = self._validate_request(request)
            day_progress_service = DayProgressService(self.save, request, self.engine)

            return day_progress_service.progress_day()
            
        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
        except ValueError as e:
            print(e)
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
        except PermissionError as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=403)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    def _validate_request(self, request):
        """Validate request and return save_id"""
        data = json.loads(request.body)
        save_id = data.get('save_id')
        
        if save_id is None:
            raise ValueError('Missing save_id')
        
        save = self.save  # From GameViewMixin
        
        # Type mismatch check
        if str(save.id) != str(save_id):
            raise ValueError('Mismatched save_id')
        
        if save.user != request.user:
            raise PermissionError('Not allowed to start this day')
        
        return save_id
    
    