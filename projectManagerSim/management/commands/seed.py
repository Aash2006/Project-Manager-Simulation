import random

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from projectManagerSim.fixtures.character_descr import get_character_seed_data, iter_relationship_seed_rows
from projectManagerSim.models import (
    Character,
    CharacterRelationship,
    CharacterTemplateRelationship,
    Decision,
    Option,
    Save,
    SaveCharacter,
    Task,
    TaskType,
)
from projectManagerSim.services import game

class Command(BaseCommand):
    help = "Seeds the database with coursework test data"

    @transaction.atomic
    def handle(self, *args, **options):
        fake = Faker()
        Faker.seed(12345)
        random.seed(12345)

        SaveCharacter.objects.all().delete()
        CharacterRelationship.objects.all().delete()
        CharacterTemplateRelationship.objects.all().delete()
        Character.objects.all().delete()
        Save.objects.all().delete()
        Task.objects.all().delete()
        Decision.objects.all().delete()
        Option.objects.all().delete()
        TaskType.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        users = []

        player_user, _ = User.objects.get_or_create(
            username="player1",
            defaults={
                "first_name": "Player",
                "last_name": "One",
                "email": "player1@example.com",
                "is_staff": False,
                "is_superuser": False,
            },
        )
        player_user.set_password("password123")
        player_user.is_staff = False
        player_user.is_superuser = False
        player_user.save()
        users.append(player_user)

        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "first_name": "Admin",
                "last_name": "User",
                "email": "admin@example.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.set_password("password123")
        admin_user.save()

        for i in range(2):
            username = f"testuser{i + 1}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                    "email": fake.email(),
                    "is_staff": False,
                    "is_superuser": False,
                },
            )
            user.set_password("password123")
            user.is_staff = False
            user.is_superuser = False
            user.save()
            users.append(user)

        for fixture in ["roles", "task_types"]:
            self.stdout.write(f"Loading fixture: {fixture}...")
            call_command("loaddata", fixture)

        self.stdout.write("Creating canonical coursework characters...")
        character_seed_data = get_character_seed_data()
        created_characters = []
        for char_data in character_seed_data:
            pk = char_data.pop("pk")
            archetype = char_data.pop("archetype")
            character = Character.objects.create(pk=pk, **char_data)
            created_characters.append(character)
            self.stdout.write(
                f"  ✓ {character.get_full_name()} — {archetype} ({character.get_role_display_full()})"
            )

        self.stdout.write("Creating baseline template relationships...")
        for row in iter_relationship_seed_rows():
            CharacterTemplateRelationship.objects.create(
                character_a_id=row["character_a_pk"],
                character_b_id=row["character_b_pk"],
                relationship_score=row["relationship_score"],
            )

        active_team = Character.objects.order_by("pk")[:4]
        for user in users:
            day = random.randint(0, 27)
            save = Save.objects.create(
                user=user,
                status=Save.Status.ONGOING,
                active=True,
                progress_percent=random.randint(0, 99),
                current_day=day,
                score=random.randint(-100, 100),
            )
            game.populate_characters(save, active_team)
            game.populate_tasks(save)
            game.populate_decisions(save)

            for _ in range(2):
                day = random.randint(0, 28)
                if day == 28:
                    status = Save.Status.COMPLETED
                    percent = 100
                else:
                    status = Save.Status.ONGOING
                    percent = random.randint(0, 99)

                save = Save.objects.create(
                    user=user,
                    status=status,
                    progress_percent=percent,
                    current_day=day,
                    score=random.randint(-100, 100),
                )
                game.populate_characters(save, active_team)
                game.populate_tasks(save)
                game.populate_decisions(save)

        player_user_2, _ = User.objects.get_or_create(
            username="player2",
            defaults={
                "email": "player2@test.com",
                "first_name": "Player",
                "last_name": "Two",
            },
        )
        player_user_2.set_password("password123")
        player_user_2.is_staff = False
        player_user_2.is_superuser = False
        player_user_2.save()

        self.stdout.write(self.style.SUCCESS("\n========== SEEDING COMPLETE =========="))
        self.stdout.write(f"Users: {User.objects.count()}")
        self.stdout.write(f"Characters: {Character.objects.count()}")
        self.stdout.write(f"Saves: {Save.objects.count()}")
        self.stdout.write(f"SaveCharacters: {SaveCharacter.objects.count()}")
        self.stdout.write(f"Tasks: {Task.objects.count()}")
        self.stdout.write(f"TaskTypes: {TaskType.objects.count()}")
        self.stdout.write(f"Template relationships: {CharacterTemplateRelationship.objects.count()}")
        self.stdout.write(f"Relationships: {CharacterRelationship.objects.count()}")
        self.stdout.write(f"Decisions: {Decision.objects.count()}")
        self.stdout.write(f"Options: {Option.objects.count()}")
