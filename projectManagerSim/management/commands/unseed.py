from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from projectManagerSim.models import Character, CharacterRelationship, CharacterTemplateRelationship, TaskType, Task, Save, SaveCharacter

class Command(BaseCommand):
    help = 'Clears all test data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-superusers',
            action='store_true',
            help='Keep superuser accounts',
        )

    def handle(self, *args, **options):
        
        # Count before deletion
        save_char_count = SaveCharacter.objects.count()
        save_count = Save.objects.count()
        task_count = Task.objects.count()
        task_type_count = TaskType.objects.count()
        character_count = Character.objects.count()
        template_relationship_count = CharacterTemplateRelationship.objects.count()
        relationship_count = CharacterRelationship.objects.count()
        
        if options['keep_superusers']:
            user_count = User.objects.filter(is_superuser=False).count()
        else:
            user_count = User.objects.count()
        
        # Delete in order 
        CharacterRelationship.objects.all().delete()
        SaveCharacter.objects.all().delete()
        Save.objects.all().delete()
        Task.objects.all().delete()
        TaskType.objects.all().delete()
        CharacterTemplateRelationship.objects.all().delete()
        Character.objects.all().delete()
        
        if options['keep_superusers']:
            User.objects.filter(is_superuser=False).delete()
        else:
            User.objects.all().delete()
        
