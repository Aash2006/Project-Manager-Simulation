from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from projectManagerSim.services import game


@login_required
def game_start(request):
    """Show Continue or New Game options"""

    game_save = game.get_save_or_none(request.user)
    
    return render(request, "game_start.html", {'game_save' : game_save})
