from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.management import call_command
from projectManagerSim.models import Save, SaveCharacter, Character, Task, TaskType
from projectManagerSim.services.game import create_save
import random


class Command(BaseCommand):
    help = 'Creates a demo setup for screencasting - previous saves + an active save with statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='player1',
            help='Username to create demo for (default: player1)',
        )

    def handle(self, *args, **options):
        username = options['username']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User '{username}' not found. Run seed first."))
            return

        characters = list(Character.objects.all())
        if len(characters) < 4:
            self.stdout.write(self.style.ERROR("Not enough characters. Run seed first."))
            return

        # Deactivate any existing active save
        Save.objects.filter(user=user, active=True).update(active=False)

        # ── Previous saves ────────────────────────────────────────────────────
        completed_runs = [
            {
                'final_grade': 'A+++',
                'progress_percent': 100,
                'score': 98,
                'current_day': 20,
                'total_tasks_completed': 12,
                'total_tasks_failed': 0,
                'highest_daily_progress': 55,
                'energies': [90, 85, 92, 88],
                'happinesses': [95, 88, 90, 92],
                'daily_stats': [
                    {'day': i, 'progress_gained': 12 + (i % 3) * 6, 'score_gained': 25 + (i % 4) * 10, 'tasks_completed': 1 if i % 2 == 0 else 0, 'tasks_failed': 0}
                    for i in range(1, 20)
                ],
            },
            {
                'final_grade': 'B',
                'progress_percent': 85,
                'score': 58,
                'current_day': 26,
                'total_tasks_completed': 7,
                'total_tasks_failed': 3,
                'highest_daily_progress': 30,
                'energies': [45, 55, 40, 60],
                'happinesses': [50, 60, 45, 65],
                'daily_stats': [
                    {'day': i, 'progress_gained': 8 + (i % 4) * 3, 'score_gained': 12 + (i % 3) * 7, 'tasks_completed': 1 if i % 4 == 0 else 0, 'tasks_failed': 1 if i % 9 == 0 else 0}
                    for i in range(1, 26)
                ],
            },
            {
                'final_grade': 'C',
                'progress_percent': 55,
                'score': 22,
                'current_day': 28,
                'total_tasks_completed': 4,
                'total_tasks_failed': 6,
                'highest_daily_progress': 18,
                'energies': [20, 15, 25, 18],
                'happinesses': [25, 20, 18, 22],
                'daily_stats': [
                    {'day': i, 'progress_gained': max(0, 6 - (i % 5)), 'score_gained': max(0, 8 - i % 7), 'tasks_completed': 0, 'tasks_failed': 1 if i % 5 == 0 else 0}
                    for i in range(1, 28)
                ],
            },
        ]

        for run in completed_runs:
            save = Save.objects.create(
                user=user,
                status=Save.Status.COMPLETED,
                active=False,
                final_grade=run['final_grade'],
                progress_percent=run['progress_percent'],
                score=run['score'],
                current_day=run['current_day'],
                total_days=28,
                total_tasks_completed=run['total_tasks_completed'],
                total_tasks_failed=run['total_tasks_failed'],
                highest_daily_progress=run['highest_daily_progress'],
                daily_stats=run['daily_stats'],
            )
            team = characters[:4]
            for j, char in enumerate(team):
                sc = SaveCharacter(game_save=save, character=char)
                sc.save()
                sc.current_energy = run['energies'][j]
                sc.current_happiness = run['happinesses'][j]
                sc.save()
            self.stdout.write(f"  ✓ Created completed run: Grade {run['final_grade']}")

        # ── Active save ───────────────────────────────────────────────────────
        self.stdout.write("\nCreating active save...")
        team = characters[:4]
        active_save = create_save(user, team)

        # Push it to day 8 with some realistic statistics
        active_save.current_day = 8
        active_save.score = 45
        active_save.progress_percent = 28
        active_save.total_tasks_completed = 3
        active_save.total_tasks_failed = 1
        active_save.highest_daily_progress = 35
        active_save.daily_stats = [
            {'day': 1, 'progress_gained': 10, 'score_gained': 15, 'tasks_completed': 0, 'tasks_failed': 0},
            {'day': 2, 'progress_gained': 15, 'score_gained': 20, 'tasks_completed': 1, 'tasks_failed': 0},
            {'day': 3, 'progress_gained': 8,  'score_gained': 10, 'tasks_completed': 0, 'tasks_failed': 1},
            {'day': 4, 'progress_gained': 35, 'score_gained': 40, 'tasks_completed': 1, 'tasks_failed': 0},
            {'day': 5, 'progress_gained': 20, 'score_gained': 25, 'tasks_completed': 0, 'tasks_failed': 0},
            {'day': 6, 'progress_gained': 18, 'score_gained': 22, 'tasks_completed': 1, 'tasks_failed': 0},
            {'day': 7, 'progress_gained': 12, 'score_gained': 18, 'tasks_completed': 0, 'tasks_failed': 0},
        ]
        active_save.save()

        # Set character energies to varied levels for interest
        save_characters = list(SaveCharacter.objects.filter(game_save=active_save))
        energies = [75, 45, 90, 30]
        happinesses = [80, 55, 85, 40]
        for i, sc in enumerate(save_characters):
            sc.current_energy = energies[i]
            sc.current_happiness = happinesses[i]
            sc.save()

        self.stdout.write(f"  ✓ Created active save at day 8 with statistics")
        self.stdout.write(self.style.SUCCESS(f"\nDemo setup complete for '{username}'."))
        self.stdout.write(f"Log in and go to /game/start/ to begin the screencast.")