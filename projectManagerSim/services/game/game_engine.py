from django.db.models import Prefetch
from django.http import Http404

from projectManagerSim.models import *


class GameEngine:
    """
    Wrapper for the active save instance and related data for easy access
    in the views

    Auto-passed into all views with GameViewMixin as self.engine, or if using 
    @game_view you must recieve it in the function header after request and any
    additional *args

    We could have this handles all game logic (modifying the active save,
    calculating how much to update the game save, validating player 
    actions aka enforcing game rules, and event listening and handling)
    so that it's decoupled from the views

    returns exception if you return a render() in fbv; return TemplateResponse
    instead instead or skip the decorator

    """

    def __init__(self, save):
        """Save data - add to as needed"""
        #finish adding query optimisation
        self.save = save
        self.user = save.user

        self.characters = save.characters.prefetch_related('character')
        self.c_working = self.characters.filter(is_resting=False)
        self.c_resting = self.characters.filter(is_resting=True)
             
        self.tasks = save.tasks.filter(unlocks_at_percent__lte=save.progress_percent).select_related('task_type')
        self.all_tasks = save.tasks.all().select_related('task_type')
        self.t_ongoing = self.tasks.filter(is_completed=False)
        self.t_completed = self.tasks.filter(is_completed=True)
        
        self.decisions = save.decisions.prefetch_related('options')
        self.all_decisions = save.decisions.prefetch_related('options')

        # this data is always passed into the template by the decorator/mixin
        self.context = {
            'save' : self.save,
        }

    def fetch(self, *keys):
        """
        returns model instances using their attribute names
        they'll be auto passed into the view as well
       
        can chain as many as you like in one fetch() call, in any order

        avoids repeated statements in every view

        + optimise into one query?
        """
    
        context = {}
        values = []
        for key in keys:
            key = str(key).lower()

            value = getattr(self, key, None)

            if value is None: 
                raise Http404(f"KeyError: {key} - No such fetch key exists") #this error for dev only
            if callable(value): 
                value = value()

            context[key]= value
            values.append(value)

        self.context.update(context)

        if len(values) == 1: return values[0]
        else: return tuple(values)