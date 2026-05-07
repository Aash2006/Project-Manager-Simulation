from django.db import models
from projectManagerSim.models.character import Character
from projectManagerSim.models.character_relationships import CharacterRelationship
from projectManagerSim.models.decisions.decision import Decision
from projectManagerSim.models.save_character import SaveCharacter
from projectManagerSim.models.task import Task
import operator

class CharacterDecision(Decision):
    """
    Handles decisions that affect a singular Save Character, exists to contain the various possible requirements for these decisions
    """
    
    task_available = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, related_name='task_available')
    task_complete = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, related_name='task_complete')
    task_working = models.ForeignKey(SaveCharacter, on_delete=models.CASCADE, null=True, related_name='task_working')
    task_not_working = models.ForeignKey(SaveCharacter, on_delete=models.CASCADE, null=True, related_name='task_not_working')
    
    required_characters_in_save = models.ManyToManyField(Character, related_name="in_decision", blank=True)

    stat_requirement = models.JSONField(default=list, blank=True, null=True)

    relationship = models.ForeignKey(CharacterRelationship, on_delete=models.CASCADE, null=True, blank=True)
    relationship_score = models.CharField(max_length = 20, blank=True, null=True)
    """
    Checks stat requirements!
    """
    def is_stat_requirements_fulfilled(self):
        ops = {
            ">": operator.gt,
            "<": operator.lt,
            ">=": operator.ge,
            "<=": operator.le,
            "==": operator.eq
        }
        for req in self.stat_requirement:
            stat_name = req.get('stat')
            op_str = req.get('operator')
            target_val = req.get('value')
            target_char_id = req.get('character_pk')
            if not stat_name or not op_str or not target_val or not target_char_id:
                return False
            if not isinstance(target_val, int) or not isinstance(op_str, str) or not isinstance(stat_name, str):
                return False
            if not ops.get(op_str):
                return False
            target_sc = SaveCharacter.objects.filter(game_save=self.game_save).filter(character_id=target_char_id).first()
            print(f"Checking {target_sc} - {stat_name} {op_str} {target_val}")
            if not target_sc:
                print("Oops! that save character doesnt exist")
                return False 
            current_val = getattr(target_sc, f"current_{stat_name}", None)

            if current_val is None:
                print("Oops! that attribute doesnt exist")
                return False 
            
            if not ops[op_str](current_val, target_val):
                print(f"Ok nope {current_val} {op_str} {target_val} is False")
                return False
            print(f"Ok yep {current_val} {op_str} {target_val} is True")
        
        return True

    """
    We're not really going to have that many crazy requirements so we can really just have the set of requirements be here
    """
    def is_available(self):
        if not super().is_available():
            return False 
        if self.relationship_score:
            if self.relationship:
                print(self.relationship.relationship_type)
                print(self.relationship_score)
                if self.relationship.relationship_type != self.relationship_score:
                    return False
            elif self.relationship_score != "neutral":
                return False
            
        if self.task_available:
            tasks = Task.objects.filter(game_save=self.game_save).filter(is_completed=False).filter(unlocks_at_percent__lte=self.game_save.progress_percent)
            if self.task_available not in tasks:
                return False
        if self.task_complete:
            tasks = Task.objects.filter(game_save=self.game_save).filter(is_completed=False)
            if self.task_complete in tasks:
                return False
        if self.task_working:
            if self.task_available:
                if not self.task_working is None and self.task_working.task_assigned.id == self.task_available.id:
                    return False
            else:
                if not self.task_working.task_assigned:
                    return False
        if self.task_not_working:
            if self.task_not_working.task_assigned:
                return False
        if self.stat_requirement:
            print("Checking Stats Requirement")
            if not self.is_stat_requirements_fulfilled():
                return False
            
        if self.game_save:
            sc_list = self.game_save.characters.values_list('character_id', flat=True)
            for char in self.required_characters_in_save.all():
                if char.id not in sc_list:
                    return False

        return True
    