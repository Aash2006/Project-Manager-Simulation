from django.db import models
from projectManagerSim.models.decisions.option import Option
from projectManagerSim.models.save_character import SaveCharacter
from projectManagerSim.models.task import Task


class SaveCharacterOption(Option):
    """
    For options that affect the stats of a single SaveCharacter
    """
    save_character = models.ForeignKey(SaveCharacter, on_delete=models.CASCADE)

    happiness_effect = models.FloatField(default=1.0)
    confidence_effect = models.FloatField(default=1.0)
    dedication_effect = models.FloatField(default=1.0)
    stress_effect = models.FloatField(default=1.0)
    irritability_effect = models.FloatField(default=1.0)

    skill_level_effect = models.FloatField(default=1.0)
    communication_skills_effect = models.FloatField(default=1.0)
    reliability_effect = models.FloatField(default=1.0)
    teachability_effect = models.FloatField(default=1.0)
    
    energy_effect = models.FloatField(default=1.0)

    task_assign_result = models.IntegerField(default=-1)

    set_rest = models.BooleanField(default=False)

    unassign_task = models.BooleanField(default=False)
    class Meta:
        base_manager_name = 'objects'
    """
    Applies changes to SaveCharacter stats & assigned tasks
    """
    def apply(self):
        super().apply()
        sc = self.save_character

        def clamp(current, effect):
            return round(max(0, min(100, current * effect)))

        sc.current_happiness = clamp(sc.current_happiness, self.happiness_effect)
        sc.current_confidence = clamp(sc.current_confidence, self.confidence_effect)
        sc.current_dedication = clamp(sc.current_dedication, self.dedication_effect)
        sc.current_stress = clamp(sc.current_stress, self.stress_effect)
        sc.current_irritability = clamp(sc.current_irritability, self.irritability_effect)

        sc.current_skill_level = clamp(sc.current_skill_level, self.skill_level_effect)
        sc.current_communication_skills = clamp(sc.current_communication_skills, self.communication_skills_effect)
        sc.current_reliability = clamp(sc.current_reliability, self.reliability_effect)
        sc.current_teachability = clamp(sc.current_teachability, self.teachability_effect)

        sc.current_energy = clamp(sc.current_energy, self.energy_effect)
        
        new_task = Task.objects.filter(pk=self.task_assign_result).first()
        if new_task:
            sc.task_assigned = new_task
            sc.is_resting = False
            sc.lock_task = True
        
        if self.unassign_task:
            sc.task_assigned = None 
        
        if self.set_rest:
            sc.task_assigned = None 
            sc.is_resting = True
            sc.lock_rest = True

        sc.save()