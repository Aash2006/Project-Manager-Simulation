from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from projectManagerSim.models import Save, SaveCharacter, Character, Task, TaskType


def make_user(username='testuser', password='testpass123'):
    return User.objects.create_user(username=username, password=password)


def make_save(user, **kwargs):
    defaults = dict(
        active=True,
        current_day=5,
        progress_percent=40,
        score=60,
        total_tasks_completed=8,
        total_tasks_failed=2,
        highest_daily_progress=25,
        daily_stats=[
            {'day': 1, 'progress_gained': 10, 'tasks_completed': 2, 'score_gained': 50, 'tasks_failed': 0},
            {'day': 2, 'progress_gained': 15, 'tasks_completed': 3, 'score_gained': 75, 'tasks_failed': 1},
            {'day': 3, 'progress_gained': 5,  'tasks_completed': 1, 'score_gained': 25, 'tasks_failed': 0},
            {'day': 4, 'progress_gained': 10, 'tasks_completed': 2, 'score_gained': 50, 'tasks_failed': 1},
        ],
    )
    defaults.update(kwargs)
    return Save.objects.create(user=user, **defaults)


def make_character(first_name='Alice', last_name='Test', role='backend', **kwargs):
    defaults = dict(
        first_name=first_name,
        last_name=last_name,
        primary_role=role,
        initial_energy=75,
        initial_happiness=100,
    )
    defaults.update(kwargs)
    return Character.objects.create(**defaults)


def make_save_character(save, character, energy=80, happiness=75):
    sc = SaveCharacter(game_save=save, character=character)
    sc.save()
    # Override the values set by SaveCharacter.save() 
    sc.current_energy = energy
    sc.current_happiness = happiness
    sc.save()
    return sc



class GameStatisticsViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='testpass123')
        self.save = make_save(self.user)
        self.char1 = make_character('Alice', 'Test', 'backend')
        self.char2 = make_character('Bob', 'Test', 'frontend')
        self.sc1 = make_save_character(self.save, self.char1, energy=80, happiness=75)
        self.sc2 = make_save_character(self.save, self.char2, energy=90, happiness=85)

    def test_view_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('game_statistics'))
        self.assertEqual(response.status_code, 302)

    def test_view_loads_successfully(self):
        response = self.client.get(reverse('game_statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'game/game_statistics.html')

    def test_context_contains_save(self):
        response = self.client.get(reverse('game_statistics'))
        self.assertEqual(response.context['save'], self.save)

    def test_required_context_keys_present(self):
        response = self.client.get(reverse('game_statistics'))
        for key in [
            'total_days_played', 'avg_progress_per_day', 'tasks_completed',
            'character_stats', 'daily_stats_json',
            'team_characters', 'highest_daily_progress',
        ]:
            self.assertIn(key, response.context, msg=f"Missing context key: {key}")

    def test_days_played_calculated_correctly(self):
        # current_day=5, days played = 5 - 1 = 4
        response = self.client.get(reverse('game_statistics'))
        self.assertEqual(response.context['total_days_played'], 4)

    def test_avg_progress_calculated_correctly(self):
        # progress_percent=40, days_played=4, avg = 10.0
        response = self.client.get(reverse('game_statistics'))
        self.assertEqual(response.context['avg_progress_per_day'], 10.0)

    def test_character_stats_reflects_save_character_values(self):
        """final_energy/happiness should come from SaveCharacter, not Character template"""
        response = self.client.get(reverse('game_statistics'))
        stats = response.context['character_stats']
        self.assertEqual(len(stats), 2)
        names = [s['name'] for s in stats]
        self.assertIn('Alice Test', names)
        self.assertIn('Bob Test', names)
        alice = next(s for s in stats if s['name'] == 'Alice Test')
        self.assertEqual(alice['current_energy'], 80)
        self.assertEqual(alice['current_happiness'], 75)

    def test_daily_stats_json_is_valid_json(self):
        import json
        response = self.client.get(reverse('game_statistics'))
        json_str = response.context['daily_stats_json'] 
        parsed = json.loads(json_str)
        self.assertEqual(len(parsed), 4)
        self.assertEqual(parsed[0]['day'], 1)

    def test_daily_stats_content(self):
        import json
        response = self.client.get(reverse('game_statistics'))
        daily = json.loads(response.context['daily_stats_json'])
        self.assertEqual(len(daily), 4)
        self.assertEqual(daily[1]['progress_gained'], 15)
        self.assertEqual(daily[1]['tasks_failed'], 1)


    def test_team_characters_count(self):
        response = self.client.get(reverse('game_statistics'))
        self.assertEqual(len(response.context['team_characters']), 2)

    def test_empty_team_does_not_crash(self):
        SaveCharacter.objects.filter(game_save=self.save).delete()
        response = self.client.get(reverse('game_statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['character_stats']), 0)

    def test_day_one_avg_progress_no_division_by_zero(self):
        """current_day=1 means 0 days played — should not divide by zero"""
        self.save.current_day = 1
        self.save.save()
        response = self.client.get(reverse('game_statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['avg_progress_per_day'], 0)



class GameEndViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='testpass123')
        self.save = make_save(self.user)
        self.char1 = make_character('Alice', 'Test', 'backend')
        self.char2 = make_character('Bob', 'Test', 'frontend')
        self.sc1 = make_save_character(self.save, self.char1, energy=20, happiness=15)
        self.sc2 = make_save_character(self.save, self.char2, energy=85, happiness=90)

    def test_view_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('game_end'))
        self.assertEqual(response.status_code, 302)

    def test_view_loads_successfully(self):
        response = self.client.get(reverse('game_end'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'game_results.html')

    def test_no_active_save_shows_no_grade(self):
        self.save.active = False
        self.save.save()
        response = self.client.get(reverse('game_end'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['grade'], 'No Grade')

    def test_save_is_deactivated_after_visit(self):
        self.client.get(reverse('game_end'))
        self.save.refresh_from_db()
        self.assertFalse(self.save.active)

    def test_save_is_marked_completed_after_visit(self):
        self.client.get(reverse('game_end'))
        self.save.refresh_from_db()
        self.assertEqual(self.save.status, Save.Status.COMPLETED)

    def test_grade_is_calculated_and_stored(self):
        self.client.get(reverse('game_end'))
        self.save.refresh_from_db()
        self.assertIsNotNone(self.save.final_grade)
        self.assertIn(self.save.final_grade, [
            'F', 'D-', 'D', 'D+', 'C-', 'C', 'C+',
            'B-', 'B', 'B+', 'A-', 'A', 'A+', 'A+++'
        ])

    def test_required_context_keys_present(self):
        response = self.client.get(reverse('game_end'))
        for key in [
            'grade', 'grade_response', 'save', 'daily_stats_json',
            'total_days_played', 'avg_progress_per_day', 'tasks_completed',
            'tasks_failed', 'highest_daily_progress', 'character_stats',
            'improvement_tips',
        ]:
            self.assertIn(key, response.context, msg=f"Missing context key: {key}")

    def test_daily_stats_json_is_valid_json(self):
        import json
        response = self.client.get(reverse('game_end'))
        parsed = json.loads(response.context['daily_stats_json'])
        self.assertEqual(len(parsed), 4)

    def test_character_stats_performance_labels(self):
        """Low energy/happiness char should be Burned Out, high should be Thriving"""
        response = self.client.get(reverse('game_end'))
        stats = response.context['character_stats']
        labels = {s['name']: s['performance_label'] for s in stats}
        self.assertEqual(labels['Alice Test'], 'Burned Out')
        self.assertEqual(labels['Bob Test'], 'Thriving')

    def test_character_stats_sorted_worst_first(self):
        """Burned out characters should appear first"""
        response = self.client.get(reverse('game_end'))
        stats = response.context['character_stats']
        self.assertEqual(stats[0]['name'], 'Alice Test')  # energy=20, happiness=15

    def test_improvement_tips_generated(self):
        response = self.client.get(reverse('game_end'))
        tips = response.context['improvement_tips']
        self.assertIsInstance(tips, list)
        self.assertGreater(len(tips), 0)

    def test_burned_out_character_triggers_tip(self):
        """Alice is burned out so there should be a tip mentioning rest days"""
        response = self.client.get(reverse('game_end'))
        tips = response.context['improvement_tips']
        tip_texts = ' '.join(tip for _, tip in tips)
        self.assertIn('burned out', tip_texts.lower())

    def test_incomplete_progress_triggers_tip(self):
        """progress_percent=40 should trigger an unfinished tip"""
        response = self.client.get(reverse('game_end'))
        tips = response.context['improvement_tips']
        tip_texts = ' '.join(tip for _, tip in tips)
        self.assertIn('unfinished', tip_texts.lower())

    def test_perfect_run_shows_no_major_issues(self):
        """A run with 100% progress, no failures, and healthy team should get a positive tip"""
        self.save.progress_percent = 100
        self.save.total_tasks_failed = 0
        self.save.save()
        self.sc1.current_energy = 90
        self.sc1.current_happiness = 90
        self.sc1.save()
        # Need a fresh active save since the view deactivates it
        fresh_save = make_save(
            make_user('user2', 'pass2'),
            progress_percent=100,
            total_tasks_failed=0,
        )
        sc = make_save_character(fresh_save, self.char1, energy=90, happiness=90)
        self.client.login(username='user2', password='pass2')
        response = self.client.get(reverse('game_end'))
        tips = response.context['improvement_tips']
        tip_texts = ' '.join(tip for _, tip in tips)
        self.assertIn('no major issues', tip_texts.lower())

    
    def test_projection_key_present_in_context(self):
        response = self.client.get(reverse('game_statistics'))
        self.assertIn('projection', response.context)

    def test_projection_on_track(self):
        self.save.current_day = 10
        self.save.progress_percent = 40
        self.save.save()
        response = self.client.get(reverse('game_statistics'))
        projection = response.context['projection']
        self.assertEqual(projection['status'], 'on_track')
        self.assertEqual(projection['status_class'], 'success')

    def test_projection_wont_finish(self):
        self.save.current_day = 10
        self.save.progress_percent = 1
        self.save.save()
        response = self.client.get(reverse('game_statistics'))
        projection = response.context['projection']
        self.assertEqual(projection['status'], 'wont_finish')
        self.assertEqual(projection['status_class'], 'danger')

    def test_projection_tight(self):
        # progress=90, current_day=26, total_days=28, avg=90/25=3.6%/day
        # days_needed = 10/3.6 ≈ 3, projected_day = 26+3 = 29, buffer = 28-29 = -1, wont_finish
        # Try progress=85, current_day=20, total_days=28, avg=85/19≈4.47
        # days_needed = 15/4.47 ≈ 3, projected_day = 23, buffer = 28-23 = 5, on_track
        self.save.progress_percent = 97
        self.save.current_day = int( 26 * (42/28))
        self.save.save()
        response = self.client.get(reverse('game_statistics'))
        projection = response.context['projection']
        self.assertEqual(projection['status'], 'tight')
        self.assertEqual(projection['status_class'], 'warning')

    def test_projection_unknown_when_no_progress(self):
        self.save.progress_percent = 0
        self.save.save()
        response = self.client.get(reverse('game_statistics'))
        projection = response.context['projection']
        self.assertEqual(projection['status'], 'unknown')
        self.assertIsNone(projection['projected_day'])

    def test_projection_unknown_when_day_one(self):
        self.save.current_day = 1
        self.save.save()
        response = self.client.get(reverse('game_statistics'))
        projection = response.context['projection']
        self.assertEqual(projection['status'], 'unknown')

    def test_projection_unknown_before_day_5(self):
        self.save.current_day = 4
        self.save.save()
        response = self.client.get(reverse('game_statistics'))
        projection = response.context['projection']
        self.assertEqual(projection['status'], 'unknown')
        self.assertIn('day 5', projection['message'])