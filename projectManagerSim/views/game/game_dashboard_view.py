from django.utils import timezone
from django.views.generic import TemplateView

from projectManagerSim.decorators import GameViewMixin
from projectManagerSim.models import Save, SaveCharacter


class GameDashboardView(GameViewMixin, TemplateView):
    """Main gameplay dashboard view"""

    template_name = "game_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        user = request.user
        save, tasks = self.engine.fetch(
            "save",
            "tasks",
        )
        save_characters = SaveCharacter.objects.filter(game_save=save).select_related("character")
        working_characters = save_characters.filter(is_resting=False)
        resting_characters = save_characters.filter(is_resting=True)
        working_no_task = working_characters.filter(task_assigned=None)
        low_energy = working_characters.filter(current_energy__lte=20)
        max_energy = resting_characters.filter(current_energy=100)
        
        # Tour step logic
        tour_step = request.session.get('tour_step', '')
        show_tour = False
        
        # Check for query param to start/show tour
        if request.GET.get('tour') in ['start', 'true']:
            show_tour = True
            if not tour_step:
                tour_step = 'dashboard'
                request.session['tour_step'] = 'dashboard'
        
        # Check for new_game query param
        elif request.GET.get('new_game') == 'true':
            tour_step = 'prompt'
            request.session['tour_step'] = 'prompt'
            request.session['tour_complete'] = False
            show_tour = True
        
        # If already on prompt step, transition to dashboard
        elif tour_step == 'prompt':
            tour_step = 'dashboard'
            request.session['tour_step'] = 'dashboard'
            show_tour = True
        
        # If tour_step is set to 'dashboard', show the tour
        elif tour_step == 'dashboard':
            show_tour = True
        
        context.update(
            {
                "current_user": user,
                "save": save,
                "save_characters": save_characters,
                "working_characters": working_characters,
                "resting_characters": resting_characters,
                "working_no_task": working_no_task,
                "low_energy": low_energy,
                "max_energy": max_energy,
                "tasks": tasks,
                "save_characters_id_list": list(
                    save_characters.values_list("pk", flat=True)
                ),
                "tour_step": tour_step,
                "show_tour": show_tour,
            }
        )
        return context