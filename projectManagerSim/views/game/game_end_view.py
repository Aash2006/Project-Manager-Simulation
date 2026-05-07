import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.response import TemplateResponse
from django.views import View

from projectManagerSim.models.save import Save


class GameEndView(LoginRequiredMixin, View):
    """Results Screen"""
    RESPONSE = {
        'F':    'You got the lowest grade. There are many things you need to work on.',
        'D-':   "You didn't do well.",
        'D':    "You didn't do great.",
        'D+':   'Just barely failed! Better luck next time!',
        'C-':   'Passed... technically',
        'C':    'Mediocre project!',
        'C+':   "Could've done better.",
        'B-':   'Respectable result!',
        'B':    'Good result!',
        'B+':   'Nobody would be mad at this result!',
        'A-':   'Fantastic Result!',
        'A':    'Grade A Student!',
        'A+':   'Grade A (plus) Student!',
        'A+++': 'Under investigation for plagiarism!',
    }
    GRADES = ['F', 'D-', 'D', 'D+', 'C-', 'C', 'C+', 'B-', 'B', 'B+', 'A-', 'A', 'A+', 'A+++']
    MAX_SCORE = 1200

    def calculate_grade(self, save):
        """Calculate final grade based on progress and score"""
        progress_percent = save.progress_percent
        project_score = max(0, save.score)

        perfectionists = save.characters.filter(character__perfectionist=True)
        if perfectionists.exists():
            perfectionist_bonus = 1.30
            project_score = project_score * perfectionist_bonus

        grade_index = (project_score / self.MAX_SCORE) * (progress_percent / 100) * len(self.GRADES)
        grade_index = min(len(self.GRADES) - 1, grade_index)
        grade = self.GRADES[int(grade_index)]

        save.final_grade = grade
        save.save()
        return grade

    def _build_character_stats(self, save):
        """
        Build end-of-game stats for each team member.
        Derives 'tasks contributed to' from daily_stats isn't possible per-character
        without extra tracking, so we expose the final state and energy efficiency.
        """
        team = save.characters.select_related('character').all()
        stats = []

        for sc in team:
            char = sc.character
            energy_pct = sc.current_energy  # 0-100
            happiness_pct = sc.current_happiness  # 0-100
            combined = (energy_pct + happiness_pct) / 2
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
                'final_energy': energy_pct,
                'final_happiness': happiness_pct,
                'performance_label': performance_label,
                'performance_class': performance_class,
            })


        stats.sort(key=lambda x: (x['final_energy'] + x['final_happiness']))
        return stats

    def _build_improvement_tips(self, save, character_stats):
        """
        Generate targeted improvement tips based on actual run data.
        Returns a list of (icon, tip) tuples.
        """
        tips = []
        daily = save.daily_stats or []

        #Task completion rate
        total_tasks = save.total_tasks_completed + save.total_tasks_failed
        if total_tasks > 0:
            fail_rate = save.total_tasks_failed / total_tasks
            if fail_rate > 0.3:
                tips.append(('⚠️', f'{save.total_tasks_failed} tasks failed — try keeping team energy above 50 before assigning work.'))

        #Progress left on the table
        if save.progress_percent < 100:
            remaining = 100 - save.progress_percent
            tips.append(('📋', f'Project was {remaining}% unfinished — prioritise task coverage earlier in the run.'))

        #Burned-out characters
        burned_out = [c for c in character_stats if c['performance_label'] == 'Burned Out']
        if burned_out:
            names = ', '.join(c['name'].split()[0] for c in burned_out)
            tips.append(('😰', f'{names} finished burned out — schedule rest days before energy hits critical.'))

        #Score trend: did the score stall mid-game?
        if len(daily) >= 6:
            first_half = sum(d.get('score_gained', 0) for d in daily[:len(daily)//2])
            second_half = sum(d.get('score_gained', 0) for d in daily[len(daily)//2:])
            if second_half < first_half * 0.5:
                tips.append(('📉', 'Score dropped off sharply in the second half — keep an eye on team energy as the deadline approaches.'))

        #All good
        if not tips:
            tips.append(('🎉', 'No major issues detected — solid project management!'))

        return tips

    def get(self, request):
        user = request.user
        save = Save.objects.filter(active=True, user=user).first()

        if not save:
            context = {
                'grade': 'No Grade',
                'grade_response': "You don't even have an active save!",
            }
            return TemplateResponse(request, 'game_results.html', context)

        grade = self.calculate_grade(save)
        save.status = Save.Status.COMPLETED
        save.deactivate()

        daily_stats = save.daily_stats or []
        character_stats = self._build_character_stats(save)
        improvement_tips = self._build_improvement_tips(save, character_stats)

        total_days_played = save.current_day - 1
        avg_progress_per_day = (
            round(save.progress_percent / total_days_played, 1)
            if total_days_played > 0 else 0
        )

        context = {
            'grade': grade,
            'grade_response': self.RESPONSE.get(grade, 'No idea what grade this is!'),
            'save': save,

            # Chart data — serialised here so the template just does |safe
            'daily_stats_json': json.dumps(daily_stats),

            # Processed stats
            'total_days_played': total_days_played,
            'avg_progress_per_day': avg_progress_per_day,
            'tasks_completed': save.total_tasks_completed,
            'tasks_failed': save.total_tasks_failed,
            'highest_daily_progress': save.highest_daily_progress,

            # Per-character breakdown
            'character_stats': character_stats,

            # Improvement tips
            'improvement_tips': improvement_tips,
        }
        return TemplateResponse(request, 'game_results.html', context)