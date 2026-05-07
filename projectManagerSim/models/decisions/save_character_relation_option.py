from django.db import models
from projectManagerSim.models.character_relationships import CharacterRelationship
from projectManagerSim.models.decisions.save_character_option import SaveCharacterOption
from projectManagerSim.models.save_character import SaveCharacter
from projectManagerSim.models.task import Task

class SaveCharacterRelationOption(SaveCharacterOption):
    save_character_2 = models.ForeignKey(SaveCharacter, on_delete=models.CASCADE)

    happiness_effect_2 = models.FloatField(default=1.0)
    confidence_effect_2 = models.FloatField(default=1.0)
    dedication_effect_2 = models.FloatField(default=1.0)
    stress_effect_2 = models.FloatField(default=1.0)
    irritability_effect_2 = models.FloatField(default=1.0)

    skill_level_effect_2 = models.FloatField(default=1.0)
    communication_skills_effect_2 = models.FloatField(default=1.0)
    reliability_effect_2 = models.FloatField(default=1.0)
    teachability_effect_2 = models.FloatField(default=1.0)
    
    energy_effect_2 = models.FloatField(default=1.0)

    task_assign_result_2 = models.IntegerField(default=-1)

    set_rest_2 = models.BooleanField(default=False)

    unassign_task_2 = models.BooleanField(default=False)

    relation_change = models.IntegerField(default=0)

    class Meta:
        base_manager_name = 'objects'
    """
    Applies changes to 2nd SaveCharacter stats & assigned tasks too, also adjusts their relationship!
    """
    def apply(self):
        super().apply()
        sc = self.save_character_2

        def clamp(current, effect):
            return round(max(0, min(100, current * effect)))

        sc.current_happiness = clamp(sc.current_happiness, self.happiness_effect_2)
        sc.current_confidence = clamp(sc.current_confidence, self.confidence_effect_2)
        sc.current_dedication = clamp(sc.current_dedication, self.dedication_effect_2)
        sc.current_stress = clamp(sc.current_stress, self.stress_effect_2)
        sc.current_irritability = clamp(sc.current_irritability, self.irritability_effect_2)

        sc.current_skill_level = clamp(sc.current_skill_level, self.skill_level_effect_2)
        sc.current_communication_skills = clamp(sc.current_communication_skills, self.communication_skills_effect_2)
        sc.current_reliability = clamp(sc.current_reliability, self.reliability_effect_2)
        sc.current_teachability = clamp(sc.current_teachability, self.teachability_effect_2)

        sc.current_energy = clamp(sc.current_energy, self.energy_effect_2)
        
        new_task = Task.objects.filter(pk=self.task_assign_result_2).first()
        if new_task:
            sc.task_assigned = new_task
            sc.is_resting = False
            sc.lock_task = True
        
        if self.unassign_task_2:
            sc.task_assigned = None 
        
        if self.set_rest_2:
            sc.task_assigned = None 
            sc.is_resting = True
            sc.lock_rest = True

        sc.save()

        relation = CharacterRelationship.get_relationship_between(self.save_character, self.save_character_2)
        if not relation:
            relation = CharacterRelationship.objects.create(character_a=self.save_character,character_b=self.save_character_2)
        if self.relation_change > 0:
            relation.improve_relationship(self.relation_change)
        else:
            relation.worsen_relationship(self.relation_change*-1)