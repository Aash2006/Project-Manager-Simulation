from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .task_type import TaskType
from .save import Save


class Task(models.Model):
    """Individual tasks that can be assigned"""
    name = models.CharField(max_length = 100)

    game_save = models.ForeignKey(
        Save, 
        on_delete=models.CASCADE, 
        related_name='tasks', 
        null=True
    )

    internal_id = models.IntegerField(default=0)
    
    task_type = models.ForeignKey(
        TaskType, 
        on_delete=models.CASCADE,
        related_name='tasks', 
    )
    
    is_completed = models.BooleanField(default=False)

    days_worked = models.IntegerField(default=0)

    time_to_complete = models.IntegerField(
        validators = [MinValueValidator(1)]
    )
    
    unlocks_at_percent = models.IntegerField(
        default=0,
        validators = [MinValueValidator(0), MaxValueValidator(100)]
    )
    
    number_of_people_required = models.IntegerField(
        default = 1,
        validators = [MinValueValidator(1), MaxValueValidator(3)]
    )
    
    energy_cost = models.IntegerField(
        default = 20, 
        validators = [MinValueValidator(1), MaxValueValidator(100)],
    )

    difficulty = models.IntegerField(
        default = 5,
        validators = [MinValueValidator(1), MaxValueValidator(10)]
    )

    completion_standard = models.IntegerField(
        default = 0,
        validators = [MinValueValidator(0), MaxValueValidator(100)]
    )
    
    def __str__(self):
        return self.name
    def name_short(self):
        return self.name.split(":")[0]
    def days_left(self):
        return self.time_to_complete - self.days_worked
    def percentage_done(self):
        return int(float(self.days_worked) / float(self.time_to_complete) * 100)
    def get_assignees(self):
        return self.assignment.filter(game_save=self.game_save)