from django.contrib.auth.models import User
from django.test import TestCase

from projectManagerSim.models import Character, Save, SaveCharacter, Task, TaskType


class SaveAndTeamModelTests(TestCase):
    def test_can_create_save_with_progress_and_status(self):
        user = User.objects.create_user(username="alice", password="pass12345")

        save = Save.objects.create(
            user=user,
            save_name="Alice Save",
            progress_percent=42,
            current_day=7,
            score=123,
            status=Save.Status.ONGOING,
        )

        self.assertEqual(save.user.username, "alice")
        self.assertEqual(save.save_name, "Alice Save")
        self.assertEqual(save.progress_percent, 42)
        self.assertEqual(save.current_day, 7)
        self.assertEqual(save.score, 123)
        self.assertEqual(save.status, Save.Status.ONGOING)

    def test_savecharacter_links_team_members_to_save(self):
        user = User.objects.create_user(username="bob", password="pass12345")
        save = Save.objects.create(
            user=user,
            save_name="Bob Save",
            progress_percent=0,
            current_day=0,
            score=0,
            status=Save.Status.ONGOING,
        )

        tt = TaskType.objects.create(task_type_name="Backend")
        task = Task.objects.create(name="API work", time_to_complete=5, task_type=tt)

        char = Character.objects.create(
            first_name="Eve",
            last_name="Ng",
            primary_role="frontend",
            description="desc",
        )

        sc = SaveCharacter.objects.create(
            game_save=save,
            character=char,
            task_assigned=task,
            time_remaining_on_task=2,
            current_energy=80,
            current_happiness=90,
        )

        self.assertEqual(sc.game_save, save)
        self.assertEqual(sc.character.first_name, "Eve")
        self.assertEqual(sc.task_assigned.name, "API work")

        # Reverse relation should work (default: savecharacter_set)
        team = save.characters.all()
        self.assertEqual(team.count(), 1)
        self.assertEqual(team.first().character.first_name, "Eve")
