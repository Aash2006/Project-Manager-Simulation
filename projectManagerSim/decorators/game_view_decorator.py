from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from projectManagerSim.models import Save
from projectManagerSim.services.game import GameEngine

"""
Should verify user is logged in- 
if not redirect to login url
(if admin, will have no save, but admins should be able to see the game!
use a default admin save ig )

Veryify we are in an active save- if not redirect to start url 
and send a 'next_url' parameter !!
"""


def game_view(view_function):
    """
    Ensures the active Save instance always availible in view
    """
    @login_required
    @wraps(view_function)
    def wrapped_view(request, *args, **kwargs):
        try: 
            save = Save.objects.get(user=request.user, active=True)
        except Save.DoesNotExist:
            return redirect('game_start')
        
        engine = GameEngine(save)
        
        response = view_function(request, *args, engine=engine, **kwargs)
        
        if isinstance(response, TemplateResponse):
            response.context_data = response.context_data or {}
            response.context_data.update(engine.context)

        return response
    return wrapped_view


class GameViewMixin(LoginRequiredMixin):
    """
    Ensures the active Save instance always availible in view

    Could add in 'next' parameters
    """
    def dispatch(self, request, *args, **kwargs):
        """This method runs before any HTTP method (get, post, etc)."""
        if request.user.is_anonymous: return redirect('log_in')
        
        try: 
            self.save = Save.objects.get(user=request.user, active=True)
        except Save.DoesNotExist:
            return redirect('game_start')
        
        self.engine = GameEngine(self.save)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.engine.context)

        # Add navbar flag
        context["in_game"] = True

        return context