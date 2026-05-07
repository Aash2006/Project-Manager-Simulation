from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from projectManagerSim.models import Save, SaveCharacter, Character


@login_required
def new_game(request):
    """Start a new game - wipes existing save"""
    user = request.user
    existing_save = Save.objects.filter(user=user).first()
    
    # If no save exists, just create new game directly
    if not existing_save:
        new_save = Save.objects.create(
            user=user,
            save_name=f"{user.username}'s Game",
            status=Save.Status.ONGOING,
            progress_percent=0,
            current_day=0,
        )
    
        # Initialize characters
        for character in Character.objects.all():
            SaveCharacter.objects.create(
                game_save=new_save,
                character=character,
                task_assigned=None,
                time_remaining_on_task=0,
                current_happiness=100,
                current_energy=100,
                current_effective_productivity=100
            )
        
        messages.success(request, "New game started!")
        return redirect('game_dashboard')
    
    # Save exists - show confirmation page
    if request.method == 'POST':
        if request.POST.get('confirm'):
            existing_save.delete()
            
            new_save = Save.objects.create(
                user=user,
                save_name=f"{user.username}'s Game",
                status=Save.Status.ONGOING,
                progress_percent=0,
                current_day=0,
            )
            
            for character in Character.objects.all():
                SaveCharacter.objects.create(
                    game_save=new_save,
                    character=character,
                    task_assigned=None,
                    time_remaining_on_task=0,
                    current_happiness=100,
                    current_energy=100,
                    current_effective_productivity=100
                )
            
            messages.success(request, "New game started!")
            return redirect('game_dashboard')
    
    # Show confirmation page
    return render(request, 'user/new_game_confirm.html', {
        'existing_save': existing_save
    })