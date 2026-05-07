from dataclasses import dataclass
from projectManagerSim.models import CharacterRelationship


@dataclass
class WorkResult:
    """Result of a character's work for the day"""
    progress_points: int = 0
    warning: str = None


class CharacterWorkService:
    """Handles character work, rest, and idle states"""
    
    def __init__(self, save_character):
        self.character = save_character
        self.wlb = save_character.character.work_life_balance
        self.wlb_factor = (self.wlb - 50) / 50
    
    def process_resting(self):
        """Handle character resting to recover energy"""
        base_recovery = 20
        
        if self.character.character.night_owl:
            base_recovery = 35
        
        recovery = round(base_recovery * (1 + self.wlb_factor * 0.5))
        
        self.character.current_energy = min(100, self.character.current_energy + recovery)
        self.character.current_happiness = min(100, self.character.current_happiness + 10)
        self.character.save()

        if self.character.current_energy > 80:
            self.character.lock_rest = False
            self.character.save()
        
        return WorkResult(progress_points=0)
    
    def process_idle(self):
        """Handle character being idle (no task assigned, not resting)"""
        energy_loss = round(10 * (1 + self.wlb_factor))
        happiness_loss = 5
        
        self.character.current_energy = max(0, self.character.current_energy - energy_loss)
        self.character.current_happiness = max(0, self.character.current_happiness - happiness_loss)
        self.character.save()
        
        return WorkResult(
            progress_points=-10,
            warning=f"⚠️ {self.character.character.first_name} is idle - assign them or set them to rest!"
        )
    
    def process_working(self, task, team_size, required_size, task_workers=None):
        """
        Handle character working on a task
        
        Args:
            task: The Task object being worked on
            team_size: Number of people currently assigned to this task
            required_size: Number of people required for this task
            task_workers: List of SaveCharacter objects working on this task (for relationship checks)
        """
        energy_multiplier = self._calculate_total_energy_multiplier(
            task, 
            team_size, 
            required_size, 
            task_workers
        )
        
        base_energy = 10
        base_happiness = 5
        
        energy_loss = round(base_energy * energy_multiplier)
        happiness_loss = round(base_happiness * (1 + self.wlb_factor) * energy_multiplier)
        
        self.character.current_happiness = max(self.character.current_happiness - happiness_loss, 0)
        self.character.current_energy = max(self.character.current_energy - energy_loss, 0)
        
        if self.character.current_energy >= 50:
            result = self._work_with_high_energy(task, team_size, required_size)
        else:
            result = self._work_with_low_energy(task, team_size, required_size)
        
        self.character.save()
        return result
    
    def _calculate_total_energy_multiplier(self, task, team_size, required_size, task_workers):
        """
        Calculate the total energy cost multiplier based on all factors
        
        Factors:
        1. WLB modifier (existing)
        2. Role matching
        3. Traits (perfectionist, works_well_under_pressure)
        4. Team Player trait (overstaffing)
        5. Relationships (when working with others)
        
        Returns:
            float: Total multiplier for energy cost
        """
        multiplier = 1.0
        
        multiplier *= (1 + self.wlb_factor)
        
        role_modifier = self._get_role_modifier(task)
        multiplier *= role_modifier
        
        trait_modifier = self._get_trait_modifier(task, team_size, required_size)
        multiplier *= trait_modifier
        
        if task_workers and len(task_workers) > 1:
            relationship_modifier = self._get_relationship_modifier(task_workers)
            multiplier *= relationship_modifier

        staffing_modifier = self._calculate_energy_multiplier(team_size, required_size)
        multiplier *= staffing_modifier
        
        return multiplier
    
    def _get_role_modifier(self, task):
        """
        Calculate energy modifier based on role matching
        """
        if not hasattr(task.task_type, 'required_role'):
            return 1.0
        
        required_role = task.task_type.required_role
        char = self.character.character
        
        if char.primary_role == 'fullstack':
            return 1.00
        
        if char.primary_role == required_role:
            return 0.75
        
        if char.secondary_role == required_role:
            return 0.90
        
        return 1.30
    
    def _get_trait_modifier(self, task, team_size, required_size):
        """
        Calculate energy modifier based on character traits
        
        Returns:
            float: Energy multiplier
        """
        modifier = 1.0
        char = self.character.character
        
        if char.perfectionist:
            modifier *= 1.30
        
        if char.works_well_under_pressure:
            save = self.character.game_save
            days_left = save.total_days - save.current_day
            if days_left <= 3:
                modifier *= 0.50
        
        if char.team_player and team_size > required_size:
            pass
        
        return modifier
    
    def _get_relationship_modifier(self, task_workers):
        """
        Calculate energy modifier based on relationships with teammates
        
        Args:
            task_workers: List of SaveCharacter objects working on this task
        
        Returns:
            float: Energy multiplier based on average relationship quality
        """
        if not task_workers or len(task_workers) <= 1:
            return 1.0
        
        total_modifier = 0
        relationship_count = 0
        
        for worker in task_workers:
            if worker.id == self.character.id:
                continue  # Skip self
            
            modifier = CharacterRelationship.get_energy_modifier_between(
                self.character, 
                worker          
            )
            
            total_modifier += modifier
            relationship_count += 1
        
        if relationship_count > 0:
            return total_modifier / relationship_count
        
        return 1.0
        
    def _calculate_energy_multiplier(self, team_size, required_size):
        """
        Calculate energy multiplier based on team size vs required size
        (Existing method - kept for compatibility)
        
        This is now partially replaced by _calculate_total_energy_multiplier
        but keeping it for the overstaffing logic
        """
        char = self.character.character
        
        if team_size < required_size:
            return 1.20
        elif team_size > required_size:
            if char.team_player:
                return 1.00
            else:
                return 2.00
        else:
            return 1.00
    
    def _work_with_high_energy(self, task, team_size, required_size):
        """Handle work when energy is sufficient (≥50)"""
        base_progress = 25
        
        if team_size < required_size:
            return WorkResult(
                progress_points=-20,
                warning=f"⚠️ Task understaffed ({team_size}/{required_size} people)"
            )
        
        return WorkResult(progress_points=base_progress)
    
    def _work_with_low_energy(self, task, team_size, required_size):
        """Handle work when energy is low (<50) - random success/failure"""
        import random
        
        if random.random() < 0.5:
            return WorkResult(
                progress_points=20,
                warning=f"⚠️ {self.character.character.first_name} is working on low energy"
            )
        else:
            return WorkResult(
                progress_points=-30,
                warning=f"❌ {self.character.character.first_name} failed due to low energy!"
            )