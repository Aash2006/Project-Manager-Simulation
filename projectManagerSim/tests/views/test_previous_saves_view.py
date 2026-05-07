from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from projectManagerSim.models import Save, SaveCharacter, Character


def make_user(username='testuser', password='testpass123'):
    return User.objects.create_user(username=username, password=password)


def make_completed_save(user, **kwargs):
    defaults = dict(
        status=Save.Status.COMPLETED,
        active=False,
        final_grade='B',
        progress_percent=80,
        score=60,
        current_day=25,
        total_days=28,
        total_tasks_completed=8,
        total_tasks_failed=2,
        highest_daily_progress=30,
        daily_stats=[
            {'day': i, 'progress_gained': 10, 'score_gained': 20, 'tasks_completed': 1, 'tasks_failed': 0}
            for i in range(1, 25)
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
    sc.current_energy = energy
    sc.current_happiness = happiness
    sc.save()
    return sc


class PreviousSavesViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='testpass123')
        self.char1 = make_character('Alice', 'Test', 'backend')
        self.char2 = make_character('Bob', 'Test', 'frontend')
        self.save = make_completed_save(self.user)
        self.sc1 = make_save_character(self.save, self.char1, energy=80, happiness=75)
        self.sc2 = make_save_character(self.save, self.char2, energy=85, happiness=90)

    

    def test_view_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('previous_saves'))
        self.assertEqual(response.status_code, 302)

    def test_view_loads_successfully(self):
        response = self.client.get(reverse('previous_saves'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'game/previous_saves.html')


    #Added to make sure tour doesn't show up on visit to previous saves on brand new account
    def test_tour_step_cleared_on_visit(self):
        session = self.client.session
        session['tour_step'] = 'dashboard'
        session.save()
        self.client.get(reverse('previous_saves'))
        self.assertIsNone(self.client.session.get('tour_step'))


    def test_saves_data_in_context(self):
        response = self.client.get(reverse('previous_saves'))
        self.assertIn('saves_data', response.context)

    def test_saves_data_has_required_keys(self):
        response = self.client.get(reverse('previous_saves'))
        entry = response.context['saves_data'][0]
        for key in [
            'save', 'character_stats', 'improvement_tips',
            'daily_stats_json', 'total_days_played',
            'avg_progress_per_day', 'tasks_completed',
            'tasks_failed', 'highest_daily_progress',
        ]:
            self.assertIn(key, entry, msg=f"Missing key: {key}")

    def test_only_completed_saves_shown(self):
        # Create an active save, should not appear
        Save.objects.create(
            user=self.user,
            status=Save.Status.ONGOING,
            active=True,
            current_day=5,
        )
        response = self.client.get(reverse('previous_saves'))
        saves_data = response.context['saves_data']
        for entry in saves_data:
            self.assertEqual(entry['save'].status, Save.Status.COMPLETED)

    def test_only_shows_current_users_saves(self):
        other_user = make_user('otheruser', 'pass123')
        make_completed_save(other_user)
        response = self.client.get(reverse('previous_saves'))
        for entry in response.context['saves_data']:
            self.assertEqual(entry['save'].user, self.user)

    def test_no_completed_saves_shows_empty_list(self):
        Save.objects.filter(user=self.user).delete()
        response = self.client.get(reverse('previous_saves'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['saves_data']), 0)

    def test_multiple_saves_all_returned(self):
        make_completed_save(self.user, final_grade='A')
        make_completed_save(self.user, final_grade='F')
        response = self.client.get(reverse('previous_saves'))
        self.assertEqual(len(response.context['saves_data']), 3)

    def test_days_played_calculated_correctly(self):
        # current_day=25 → days played = 24
        response = self.client.get(reverse('previous_saves'))
        entry = response.context['saves_data'][0]
        self.assertEqual(entry['total_days_played'], 24)

    def test_avg_progress_calculated_correctly(self):
        # progress_percent=80, days_played=24 → avg = 3.3
        response = self.client.get(reverse('previous_saves'))
        entry = response.context['saves_data'][0]
        self.assertEqual(entry['avg_progress_per_day'], round(80 / 24, 1))

    def test_daily_stats_json_is_valid_json(self):
        import json
        response = self.client.get(reverse('previous_saves'))
        entry = response.context['saves_data'][0]
        parsed = json.loads(entry['daily_stats_json'])
        self.assertEqual(len(parsed), 24)


    def test_character_stats_count(self):
        response = self.client.get(reverse('previous_saves'))
        entry = response.context['saves_data'][0]
        self.assertEqual(len(entry['character_stats']), 2)

    def test_character_stats_thriving_label(self):
        response = self.client.get(reverse('previous_saves'))
        entry = response.context['saves_data'][0]
        labels = {s['name']: s['performance_label'] for s in entry['character_stats']}
        self.assertEqual(labels['Alice Test'], 'Thriving')
        self.assertEqual(labels['Bob Test'], 'Thriving')

    def test_character_stats_burned_out_label(self):
        burned_save = make_completed_save(self.user)
        make_save_character(burned_save, self.char1, energy=5, happiness=5)
        make_save_character(burned_save, self.char2, energy=5, happiness=5)
        response = self.client.get(reverse('previous_saves'))
        burned_entry = next(
            e for e in response.context['saves_data']
            if e['save'].id == burned_save.id
        )
        for stat in burned_entry['character_stats']:
            self.assertEqual(stat['performance_label'], 'Burned Out')

    def test_character_stats_sorted_worst_first(self):
        response = self.client.get(reverse('previous_saves'))
        entry = response.context['saves_data'][0]
        stats = entry['character_stats']
        combined_scores = [s['final_energy'] + s['final_happiness'] for s in stats]
        self.assertEqual(combined_scores, sorted(combined_scores))


    def test_improvement_tips_generated(self):
        response = self.client.get(reverse('previous_saves'))
        entry = response.context['saves_data'][0]
        self.assertIsInstance(entry['improvement_tips'], list)
        self.assertGreater(len(entry['improvement_tips']), 0)

    def test_incomplete_progress_triggers_tip(self):
        # progress_percent=80 so project is unfinished
        response = self.client.get(reverse('previous_saves'))
        entry = response.context['saves_data'][0]
        tip_texts = ' '.join(tip for _, tip in entry['improvement_tips'])
        self.assertIn('unfinished', tip_texts.lower())

    def test_high_fail_rate_triggers_tip(self):
        # total_tasks_completed=2, total_tasks_failed=8 : fail rate > 0.3
        bad_save = make_completed_save(
            self.user,
            total_tasks_completed=2,
            total_tasks_failed=8,
            progress_percent=100,
        )
        make_save_character(bad_save, self.char1, energy=80, happiness=80)
        make_save_character(bad_save, self.char2, energy=80, happiness=80)
        response = self.client.get(reverse('previous_saves'))
        bad_entry = next(
            e for e in response.context['saves_data']
            if e['save'].id == bad_save.id
        )
        tip_texts = ' '.join(tip for _, tip in bad_entry['improvement_tips'])
        self.assertIn('tasks failed', tip_texts.lower())

    def test_perfect_run_shows_no_major_issues(self):
        perfect_save = make_completed_save(
            self.user,
            progress_percent=100,
            total_tasks_failed=0,
            total_tasks_completed=10,
        )
        make_save_character(perfect_save, self.char1, energy=90, happiness=90)
        make_save_character(perfect_save, self.char2, energy=90, happiness=90)
        response = self.client.get(reverse('previous_saves'))
        perfect_entry = next(
            e for e in response.context['saves_data']
            if e['save'].id == perfect_save.id
        )
        tip_texts = ' '.join(tip for _, tip in perfect_entry['improvement_tips'])
        self.assertIn('no major issues', tip_texts.lower())