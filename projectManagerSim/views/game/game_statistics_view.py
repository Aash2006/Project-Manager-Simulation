from django.views.generic import TemplateView
from projectManagerSim.decorators import GameViewMixin
import json


class GameStatisticsView(GameViewMixin, TemplateView):
    """Display game statistics"""
    
    template_name = "game/game_statistics.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        save = self.save
        
        # Calculate statistics
        total_days_played = save.current_day - 1
        if total_days_played > 0:
            avg_progress_per_day = save.progress_percent / total_days_played
        else:
            avg_progress_per_day = 0
        
        projection = self.calculate_projected_finish(save, avg_progress_per_day)

        # Get SaveCharacter objects (the team)
        from projectManagerSim.models import SaveCharacter
        team_characters = SaveCharacter.objects.filter(game_save=save).select_related('character')
        
        # Character statistics
        character_stats = []
        for save_char in team_characters:
            character_stats.append({
                'name': save_char.character.get_full_name(),
                'current_energy': save_char.current_energy,
                'current_happiness': save_char.current_happiness,
            })
        
        context.update({
            'save': save,
            'team_characters': team_characters,  # ← ADD THIS LINE
            'total_days_played': total_days_played,
            'avg_progress_per_day': round(avg_progress_per_day, 1),
            'tasks_completed': save.total_tasks_completed,
            'highest_daily_progress': save.highest_daily_progress,
            'character_stats': character_stats,
            'daily_stats_json': json.dumps(save.daily_stats or []),
            'projection': projection,
        })

        return context
    
    def calculate_projected_finish(self, save, avg_progress_per_day):
        """
        Project the day the player will hit 100% progress based on current pace.

        Returns a dict with:
            projected_day   - int or None (None if no progress yet)
            days_remaining  - int, days left in the game
            status          - 'on_track' | 'tight' | 'wont_finish' | 'unknown'
            status_label    - human-readable label
            status_class    - Bootstrap colour class (success / warning / danger / secondary)
            message         - short sentence for the UI
        """
        total_days = save.total_days
        current_day = save.current_day
        days_remaining = total_days - current_day
        progress_remaining = 100 - save.progress_percent

        if current_day <= 5:
            return {
                'projected_day': None,
                'days_remaining': days_remaining,
                'status': 'unknown',
                'status_label': 'Not enough data',
                'status_class': 'secondary',
                'message': 'Projection available after day 5.',
            }

        if avg_progress_per_day <= 0 or save.progress_percent >= 100:
            return {
                'projected_day': None,
                'days_remaining': days_remaining,
                'status': 'unknown',
                'status_label': 'Not enough data',
                'status_class': 'secondary',
                'message': 'Make more progress to see a projection.',
            }

        days_needed = progress_remaining / avg_progress_per_day
        projected_day = current_day + round(days_needed)

        buffer = total_days - projected_day  # positive = ahead of schedule

        if buffer >= 3:
            status = 'on_track'
            status_label = 'On Track'
            status_class = 'success'
            message = f'At your current pace you will finish around day {projected_day}, with {buffer} days to spare.'
        elif buffer >= 0:
            status = 'tight'
            status_label = 'Tight'
            status_class = 'warning'
            message = f'Projected finish is day {projected_day} — cutting it close with only {buffer} day{"s" if buffer != 1 else ""} to spare.'
        else:
            overrun = abs(buffer)
            status = 'wont_finish'
            status_label = "Won't Finish"
            status_class = 'danger'
            message = f'At your current pace you will miss the deadline by {overrun} day{"s" if overrun != 1 else ""}. Pick up the pace!'

        return {
            'projected_day': projected_day,
            'days_remaining': days_remaining,
            'status': status,
            'status_label': status_label,
            'status_class': status_class,
            'message': message,
        }