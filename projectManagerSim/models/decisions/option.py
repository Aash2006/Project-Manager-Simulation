from django.db import models
from polymorphic.models import PolymorphicModel

from django.core.validators import MinValueValidator
from projectManagerSim.models.save_character import SaveCharacter
from projectManagerSim.models.task import Task
from projectManagerSim.models.task_type import TaskType
from .decision import Decision
from django.db.models import Max

class Option(PolymorphicModel):
    """
    Table linking a decision to it's options, and tracking option effects
    Can extend to add in extra unique effects of each option on the game
    """
    decision = models.ForeignKey(
        Decision,
        on_delete=models.CASCADE,
        related_name = 'options'
    )
    score_effect = models.IntegerField(default=0)
    text = models.CharField(max_length = 50, default='This is one of your options')
    is_availible = models.BooleanField(default=True)
    leave_team = models.IntegerField(null=True, blank=True, default=0)
    unlocking_day_delay = models.IntegerField(default=0, 
                                          
        validators = [
            MinValueValidator(0)
        ],
        null=True,
        blank=True
    )

    class Meta:
        base_manager_name = 'objects'

    unlocking_decision = models.ForeignKey(
        'projectManagerSim.Decision',
        on_delete=models.SET_NULL,
        related_name = 'unlocking_options',
        null=True,
        blank=True
    )
    create_tasks = models.JSONField(default=list, blank=True, null=True)


    def apply(self):
        our_save = self.decision.game_save
        target_id = self.leave_team

        our_save.update_score(self.score_effect)
        
        if self.unlocking_decision:
            self.unlocking_decision.unlock(self.unlocking_day_delay)

        if self.create_tasks:
            count = Task.objects.filter(game_save=self.decision.game_save).aggregate(Max('internal_id'))['internal_id__max']
            if count == None:
                count = 0
            count += 1
            for task in self.create_tasks:
                Task.objects.create(
                    name=f"Task {count}: {task['name']}",
                    task_type=TaskType.objects.get(pk=task['task_type']),
                    game_save=self.decision.game_save, 
                    time_to_complete=task['time_to_complete'],
                    unlocks_at_percent=task['unlocks_at_percent'],
                    number_of_people_required=task['number_of_people_required'],
                    energy_cost=task['energy_cost'],
                    difficulty=task['difficulty'],
                    internal_id=count
                )
                count += 1

        if target_id:
            print(f"Kicking out character ID: {target_id}")
            for_removal = SaveCharacter.objects.filter(
                game_save=our_save, 
                character_id=target_id
            ).first()
            if for_removal:
                for_removal.leaving = True
                for_removal.save(update_fields=['leaving'])
                print("Deletion successful.")
            else:
                print("They don't have a SC???")

        return




