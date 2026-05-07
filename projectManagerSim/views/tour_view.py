from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.contrib.auth.decorators import login_required

@login_required 
@require_POST
def complete_tour(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}
    
    next_step = data.get('next_step')
    
    if next_step:
        request.session['tour_step'] = next_step
    else:
        request.session['tour_step'] = None
        request.session['tour_complete'] = True
    
    return JsonResponse({'success': True})
