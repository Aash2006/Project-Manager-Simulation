from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from projectManagerSim.models import Save, SaveCharacter, Character


class Command(BaseCommand):
    help = 'Creates fake completed saves for testing the previous saves page'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='player1',
            help='Username to create saves for (default: player1)',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of completed saves to create (default: 3)',
        )

    def handle(self, *args, **options):
        username = options['username']
        count = options['count']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User '{username}' not found. Run the seed command first."))
            return

        characters = list(Character.objects.all()[:4])
        if len(characters) < 4:
            self.stdout.write(self.style.ERROR("Not enough characters in the database. Run the seed command first."))
            return

        # Vary the runs so the page looks interesting
        runs = [
            {
                'final_grade': 'A',
                'progress_percent': 100,
                'score': 85,
                'current_day': 22,
                'total_tasks_completed': 10,
                'total_tasks_failed': 0,
                'highest_daily_progress': 45,
                'energies': [80, 70, 90, 85],
                'happinesses': [85, 75, 90, 80],
                'daily_stats': [
                    {'day': i, 'progress_gained': 10 + (i % 3) * 5, 'score_gained': 20 + (i % 4) * 10, 'tasks_completed': 1 if i % 3 == 0 else 0, 'tasks_failed': 0}
                    for i in range(1, 22)
                ],
            },
            {
                'final_grade': 'C',
                'progress_percent': 60,
                'score': 35,
                'current_day': 28,
                'total_tasks_completed': 5,
                'total_tasks_failed': 4,
                'highest_daily_progress': 20,
                'energies': [15, 20, 10, 25],
                'happinesses': [20, 15, 10, 30],
                'daily_stats': [
                    {'day': i, 'progress_gained': max(0, 5 - (i % 5)), 'score_gained': max(0, 10 - (i % 6) * 3), 'tasks_completed': 0, 'tasks_failed': 1 if i % 7 == 0 else 0}
                    for i in range(1, 28)
                ],
            },
            {
                'final_grade': 'B+',
                'progress_percent': 90,
                'score': 65,
                'current_day': 25,
                'total_tasks_completed': 8,
                'total_tasks_failed': 2,
                'highest_daily_progress': 35,
                'energies': [55, 60, 45, 70],
                'happinesses': [60, 55, 50, 65],
                'daily_stats': [
                    {'day': i, 'progress_gained': 8 + (i % 4) * 3, 'score_gained': 15 + (i % 3) * 8, 'tasks_completed': 1 if i % 4 == 0 else 0, 'tasks_failed': 1 if i % 10 == 0 else 0}
                    for i in range(1, 25)
                ],
            },
            {
                'final_grade': 'F',
                'progress_percent': 20,
                'score': 5,
                'current_day': 28,
                'total_tasks_completed': 2,
                'total_tasks_failed': 8,
                'highest_daily_progress': 10,
                'energies': [5, 10, 8, 12],
                'happinesses': [10, 8, 5, 15],
                'daily_stats': [
                    {'day': i, 'progress_gained': max(0, 3 - (i % 4)), 'score_gained': max(0, 5 - i % 6), 'tasks_completed': 0, 'tasks_failed': 1 if i % 4 == 0 else 0}
                    for i in range(1, 28)
                ],
            },
            {
                'final_grade': 'A+++',
                'progress_percent': 100,
                'score': 100,
                'current_day': 18,
                'total_tasks_completed': 12,
                'total_tasks_failed': 0,
                'highest_daily_progress': 60,
                'energies': [95, 90, 88, 92],
                'happinesses': [95, 92, 90, 95],
                'daily_stats': [
                    {'day': i, 'progress_gained': 15 + (i % 3) * 8, 'score_gained': 30 + (i % 2) * 15, 'tasks_completed': 1 if i % 2 == 0 else 0, 'tasks_failed': 0}
                    for i in range(1, 18)
                ],
            },
        ]

        created = 0
        for i in range(count):
            run = runs[i % len(runs)]

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

            for j, char in enumerate(characters):
                sc = SaveCharacter(game_save=save, character=char)
                sc.save()
                sc.current_energy = run['energies'][j]
                sc.current_happiness = run['happinesses'][j]
                sc.save()

            created += 1
            self.stdout.write(f"  ✓ Created run {created}: Grade {run['final_grade']} ({run['progress_percent']}% complete)")

        self.stdout.write(self.style.SUCCESS(f"\nCreated {created} completed save(s) for '{username}'."))
        self.stdout.write(f"Visit /game/start/ and click Previous Saves to test.")