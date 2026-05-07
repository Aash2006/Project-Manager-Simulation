import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from projectManagerSim.models import Save, SaveCharacter


class PreviousSavesView(LoginRequiredMixin, TemplateView):
    """Lists all completed saves for the user with end screen stats."""

    template_name = "game/previous_saves.html"

    def get(self, request, *args, **kwargs):
        request.session['tour_step'] = None
        return super().get(request, *args, **kwargs)

    def _build_character_stats(self, save):
        team = SaveCharacter.objects.filter(
            game_save=save
        ).select_related('character')

        stats = []
        for sc in team:
            char = sc.character
            combined = (sc.current_energy + sc.current_happiness) / 2

            if combined >= 75:
                performance_label = 'Thriving'
                performance_class = 'success'
            elif combined >= 50:
                performance_label = 'Doing OK'
                performance_class = 'primary'
            elif combined >= 30:
                performance_label = 'Struggling'
                performance_class = 'warning'
            else:
                performance_label = 'Burned Out'
                performance_class = 'danger'

            stats.append({
                'name': char.get_full_name(),
                'role': char.get_role_display_full(),
                'traits': char.get_traits_list(),
                'personality_icon': char.get_personality_type_icon(),
                'final_energy': sc.current_energy,
                'final_happiness': sc.current_happiness,
                'performance_label': performance_label,
                'performance_class': performance_class,
            })

        stats.sort(key=lambda x: (x['final_energy'] + x['final_happiness']))
        return stats

    def _build_improvement_tips(self, save, character_stats):
        tips = []
        daily = save.daily_stats or []

        total_tasks = save.total_tasks_completed + save.total_tasks_failed
        if total_tasks > 0:
            fail_rate = save.total_tasks_failed / total_tasks
            if fail_rate > 0.3:
                tips.append(('⚠️', f'{save.total_tasks_failed} tasks failed — try keeping team energy above 50 before assigning work.'))

        if save.progress_percent < 100:
            remaining = 100 - save.progress_percent
            tips.append(('📋', f'Project was {remaining}% unfinished — prioritise task coverage earlier in the run.'))

        burned_out = [c for c in character_stats if c['performance_label'] == 'Burned Out']
        if burned_out:
            names = ', '.join(c['name'].split()[0] for c in burned_out)
            tips.append(('😰', f'{names} finished burned out — schedule rest days before energy hits critical.'))

        if len(daily) >= 6:
            first_half = sum(d.get('score_gained', 0) for d in daily[:len(daily) // 2])
            second_half = sum(d.get('score_gained', 0) for d in daily[len(daily) // 2:])
            if second_half < first_half * 0.5:
                tips.append(('📉', 'Score dropped off sharply in the second half — keep an eye on team energy as the deadline approaches.'))

        if not tips:
            tips.append(('🎉', 'No major issues detected — solid project management!'))

        return tips

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        completed_saves = Save.objects.filter(
            user=user,
            status=Save.Status.COMPLETED,
        ).order_by('-last_used')

        saves_data = []
        for save in completed_saves:
            character_stats = self._build_character_stats(save)
            improvement_tips = self._build_improvement_tips(save, character_stats)
            total_days_played = save.current_day - 1
            avg_progress_per_day = (
                round(save.progress_percent / total_days_played, 1)
                if total_days_played > 0 else 0
            )

            saves_data.append({
                'save': save,
                'character_stats': character_stats,
                'improvement_tips': improvement_tips,
                'daily_stats_json': json.dumps(save.daily_stats or []),
                'total_days_played': total_days_played,
                'avg_progress_per_day': avg_progress_per_day,
                'tasks_completed': save.total_tasks_completed,
                'tasks_failed': save.total_tasks_failed,
                'highest_daily_progress': save.highest_daily_progress,
            })

        context['saves_data'] = saves_data
        return context