from django.shortcuts import render
from django.views.generic import View
from projectManagerSim.models import SaveCharacter, Save, Task
from projectManagerSim.decorators import GameViewMixin
from projectManagerSim.services import game

class GameTaskListView(GameViewMixin, View):
    """display all characters"""
    
    def get(self, request):
        print(self.engine.tasks)
        user = request.user

        save, tasks, save_characters = self.engine.fetch('save', 't_ongoing', 'characters')

        print(save_characters)
        context = {
                "current_user": user,
                "save": save,
                "tasks": tasks,
                "save_characters": save_characters,
                "save_characters_id_list" : list(save_characters.values_list('pk', flat=True)),
                "in_game" : True,
                "curr_task" : tasks.first(),
                "tour_step": request.session.pop('tour_step', ''),
        }
        return render(request, "game_tasks.html", context)