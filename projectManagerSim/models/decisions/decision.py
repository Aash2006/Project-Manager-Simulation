from random import randint
from django.db import models
from polymorphic.models import PolymorphicModel
from django.core.validators import MaxValueValidator, MinValueValidator
from ..save import Save


def generate(): return randint(-5, 5)


class Decision(PolymorphicModel):
    """
    Basic Decision Model for scripted scenarios. 
    Polymorphic in order to allow for extension via inheritance.
    
    Edited from initial structure to avoid hardcoding
    """

    #scenario = models.OneToOneField(Scenario, on_delete=models.CASCADE, related_name='decision', null=True)

    #game_saves = models.ManyToManyField(Save, related_name='decisions')
    game_save = models.ForeignKey(Save, on_delete=models.CASCADE, related_name='decisions')

    repeatable = models.BooleanField(default=False)

    title = models.CharField(max_length = 50, default='Decision')

    percentage_chance = models.IntegerField(default=100,                       
        validators = [
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )

    body = models.CharField(max_length = 200, default='Please choose!')

    is_made = models.BooleanField(default=False)

    is_served = models.BooleanField(default=False)

    is_locked = models.BooleanField(default=False)

    related_name = models.CharField(max_length= 50, null=True, blank=True)

    day_requirement = models.IntegerField(default=0,
                                          
        validators = [
            MinValueValidator(0)
        ],
    )

    deadline = models.IntegerField(default=3,
                                          
        validators = [
            MaxValueValidator(10)
        ],
    )
    class Meta:
        base_manager_name = 'objects'
    """
    Really basic is_available method that simply checks if the decision has already been made, if its locked, and if we've reached the correct day
    """
    def is_available(self):
        self.refresh_from_db(fields=['is_locked', 'is_made', 'day_requirement'])
        if self.is_locked:
            print(f"{self} We're locked!")
            return False
        if self.is_made:
            return False 
        if self.game_save.current_day < self.day_requirement:
            return False 
        
        return True


    """
    Unlocks Decision, used to link Decision
    """
    def unlock(self, unlocking_delay=0):
        curr_day = self.game_save.current_day
        new_day = self.day_requirement
        if unlocking_delay > 0:
            new_day = curr_day + unlocking_delay
        Decision.objects.filter(pk=self.pk).update(
            is_locked=False,
            day_requirement=new_day
        )
        self.refresh_from_db()
        #print(f"VERIFIED UNLOCK: {self.title} is now {self.is_locked} in DB.")

    """
    Updates the deadline, and if it hits 0, then 
    """
    def update_deadline(self):
        if self.is_made:
            return
        self.deadline -= 1
        self.save()
        if self.deadline <= 0:
            print("My Deadline is Over!")
            option_1 = self.options.all().order_by('pk').first()
            if option_1:
                option_1.apply()
            self.is_made = True 
            self.save()
    
    def __str__(self):
        return f"{type(self)} - {self.title}"