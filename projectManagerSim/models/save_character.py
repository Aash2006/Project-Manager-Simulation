from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


from .character import Character
from .save import Save
from .task import Task

class SaveCharacter(models.Model): #CharacterInstance
    """Linking table to save charachters at specific states"""
    game_save  = models.ForeignKey(
        Save, 
        on_delete = models.CASCADE,
        related_name="characters"
    )

    character = models.ForeignKey(
        Character, 
        on_delete = models.CASCADE,
    )

    task_assigned = models.ForeignKey(
        Task, 
        on_delete = models.SET_NULL, 
        null = True, 
        blank = True,
        related_name='assignment'
    )

    leaving = models.BooleanField(default=False)

    is_resting = models.BooleanField(
        default=False
    )

    time_remaining_on_task = models.IntegerField(
        default = 0,
        validators = [MinValueValidator(0)]
    )

    deferral_time = models.IntegerField( # for characters to be able to defer tasks to the next day, upto a max of 5 days in a row
        default = 0,
        validators = [MinValueValidator(0), MaxValueValidator(5)]
    )

    # 'health'
    current_energy = models.IntegerField(
        default = 100,
        validators = [MinValueValidator(0), MaxValueValidator(100)]
    )

    # feelings
    current_happiness = models.IntegerField(
        default = 100,
        validators = [MinValueValidator(0), MaxValueValidator(100)]
    )

    current_confidence = models.IntegerField(
        default = 100,
        validators = [MinValueValidator(50), MaxValueValidator(200)]
    )

    current_dedication = models.IntegerField(
        default = 100,
        validators = [MinValueValidator(50), MaxValueValidator(200)]
    )

    current_stress = models.IntegerField(
        default = 100,
        validators = [MinValueValidator(50), MaxValueValidator(200)]
    )

    current_irritability = models.IntegerField(
        default = 100,
        validators = [MinValueValidator(50), MaxValueValidator(200)]
    )

    # teamworking skills
    current_skill_level = models.IntegerField(
        default = 100,
        validators = [MinValueValidator(50), MaxValueValidator(200)]
    )

    current_communication_skills = models.IntegerField(
        default = 100,
        validators = [MinValueValidator(50), MaxValueValidator(200)]
    )

    current_reliability = models.IntegerField(
        default = 100,
        validators = [MinValueValidator(50), MaxValueValidator(200)]
    )

    current_teachability = models.IntegerField(
        default = 100,
        validators = [MinValueValidator(50), MaxValueValidator(200)]
    )
    
    current_effective_productivity = models.IntegerField(
        default = 100,
        validators = [MinValueValidator(0), MaxValueValidator(100)]
    )
    lock_rest = models.BooleanField(default=False)
    lock_task = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        """
        Custom save to pull initial values from the Character template 
        ONLY when the record is first created.
        """
        if not self.pk:  # This check ensures it ONLY runs on the first save
            # Map the Template values to the Instance values
            self.current_energy = self.character.initial_energy
            self.current_happiness = self.character.initial_happiness
            self.current_confidence = self.character.initial_confidence
            self.current_dedication = self.character.initial_dedication
            self.current_stress = self.character.initial_stress
            self.current_irritability = self.character.initial_irritability
            self.current_skill_level = self.character.initial_skill_level
            self.current_communication_skills = self.character.initial_communication_skills
            self.current_reliability = self.character.initial_reliability
            self.current_teachability = self.character.initial_teachability
            
        super().save(*args, **kwargs)
    
    def calc_effective_productivity(self):
        """Calcs EP based on all skills and feelings"""

    def increase(self, emotion):
        # code
        self.calc_effective_productivity()

    def decreace(self, emotion):
        # code
        self.calc_effective_productivity()


    def calculate_happiness_change_for_energy(self, energy_level):
        """Calculate happiness change based on energy level when performing tasks"""
        
        # Energy thresholds
        CRITICAL_ENERGY = 10    # Below this: major happiness decrease
        LOW_ENERGY = 30         # Below this: happiness decrease
        HIGH_ENERGY = 70        # Above this: happiness increase
        VERY_HIGH_ENERGY = 85   # Above this: bonus happiness increase
        
        # Happiness change amounts
        CRITICAL_PENALTY = -15   # Major penalty for critical energy
        LOW_PENALTY = -8        # Penalty for low energy
        HIGH_BONUS = 5          # Bonus for high energy
        VERY_HIGH_BONUS = 10    # Major bonus for very high energy
        
        if energy_level < CRITICAL_ENERGY:
            # Critical energy: major happiness decrease
            severity = (CRITICAL_ENERGY - energy_level) / CRITICAL_ENERGY
            return int(CRITICAL_PENALTY * (1 + severity))
            
        elif energy_level < LOW_ENERGY:
            # Low energy: happiness decrease
            severity = (LOW_ENERGY - energy_level) / (LOW_ENERGY - CRITICAL_ENERGY)
            return int(LOW_PENALTY * severity)
            
        elif energy_level <= HIGH_ENERGY:
            # Medium energy: minimal change
            return 0
            
        elif energy_level < VERY_HIGH_ENERGY:
            # High energy: happiness increase
            bonus_factor = (energy_level - HIGH_ENERGY) / (VERY_HIGH_ENERGY - HIGH_ENERGY)
            return int(HIGH_BONUS * (0.5 + bonus_factor))
            
        else:
            # Very high energy: major happiness bonus
            bonus_factor = min(1.0, (energy_level - VERY_HIGH_ENERGY) / (100 - VERY_HIGH_ENERGY))
            return int(VERY_HIGH_BONUS * (0.8 + 0.4 * bonus_factor))
    
    def apply_task_happiness_effect(self, task_name="task"):
        """Apply happiness change when this character completes a task"""
        current_energy = self.current_energy
        current_happiness = self.current_happiness
        
        # Calculate happiness change
        happiness_change = self.calculate_happiness_change_for_energy(current_energy)
        
        # Apply the change, respecting bounds (0-100)
        new_happiness = max(0, min(100, current_happiness + happiness_change))
        
        # Update happiness
        self.current_happiness = new_happiness
        self.save()
        
        # Generate message
        message = self.generate_happiness_message(
            current_energy, happiness_change, current_happiness, new_happiness, task_name
        )
        
        return {
            'old_happiness': current_happiness,
            'new_happiness': new_happiness,
            'happiness_change': happiness_change,
            'applied_change': new_happiness - current_happiness,
            'energy_level': current_energy,
            'message': message,
            'energy_category': self.get_energy_category(current_energy)
        }
    def format_feelings(self):
        out = [f"={self.character.get_full_name()}=\n"]
        stats = [
            "energy", "happiness", "confidence", "dedication", "stress", 
            "irritability", "skill_level", "communication_skills", 
            "reliability", "teachability"
        ]

        for stat in stats:
            value = getattr(self, f"current_{stat}")
            out.append(f"current_{stat} - {value}\n")
        return "".join(out)
    def get_energy_category(self, energy_level):
        """Get energy category for UI display"""
        if energy_level < 10:
            return 'critical'
        elif energy_level < 30:
            return 'low'
        elif energy_level <= 70:
            return 'medium'
        elif energy_level < 85:
            return 'high'
        else:
            return 'very_high'
    
    def generate_happiness_message(self, energy, change, old_happiness, new_happiness, task_name):
        """Generate message for happiness change"""
        if change < -10:
            return f"😰 Working on {task_name} while exhausted (Energy: {energy}) severely hurt morale!"
        elif change < -5:
            return f"😔 Working on {task_name} with low energy (Energy: {energy}) decreased team happiness."
        elif change < 0:
            return f"😐 Working on {task_name} while tired (Energy: {energy}) slightly lowered morale."
        elif change == 0:
            return f"😊 Working on {task_name} with moderate energy (Energy: {energy}) maintained team morale."
        elif change < 5:
            return f"😊 Working on {task_name} with good energy (Energy: {energy}) improved team happiness slightly."
        elif change < 10:
            return f"😄 Working on {task_name} with high energy (Energy: {energy}) boosted team morale!"
        else:
            return f"🎉 Working on {task_name} while energized (Energy: {energy}) greatly improved team happiness!"
    
    def get_happiness_preview(self):
        """Preview what happiness change would occur at current energy"""
        change = self.calculate_happiness_change_for_energy(self.current_energy)
        return {
            'energy': self.current_energy,
            'happiness': self.current_happiness,
            'predicted_change': change,
            'predicted_happiness': max(0, min(100, self.current_happiness + change)),
            'energy_category': self.get_energy_category(self.current_energy)
        }
    
    def is_energy_good_for_happiness(self):
        """Check if current energy level will improve happiness"""
        return self.current_energy > 70
    
    def is_energy_bad_for_happiness(self):
        """Check if current energy level will hurt happiness"""
        return self.current_energy < 30
    
    def get_mood_status(self):
        """Get mood status based on current happiness"""
        if self.current_happiness < 20:
            return {'status': 'very_unhappy', 'emoji': '😢', 'color': 'red'}
        elif self.current_happiness < 40:
            return {'status': 'unhappy', 'emoji': '😔', 'color': 'orange'}
        elif self.current_happiness < 60:
            return {'status': 'neutral', 'emoji': '😐', 'color': 'yellow'}
        elif self.current_happiness < 80: 
            return {'status': 'happy', 'emoji': '😊', 'color': 'light_green'}
        else:
            return {'status': 'very_happy', 'emoji': '😄', 'color': 'green'}
        
    def __str__(self):
        return f"{self.character} in {self.game_save.save_name}"
    


    class Meta:
        unique_together = ['game_save', 'character']


