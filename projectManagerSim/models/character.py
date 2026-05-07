from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Character(models.Model):
    """
    Game characters that can be assigned to tasks
    
    CORE RESOURCE: ENERGY
    - Characters start with 100 energy
    - Working costs energy (base: 10 per day)
    - Resting recovers energy (base: 20 per day)
    - Low energy (<50) = risk of failure
    
    TRAIT SYSTEM:
    All traits affect ENERGY economy (not speed, since days_worked is an integer)
    Energy management is the core strategic resource
    """

    ROLE_CHOICES = [
        ('frontend', 'Frontend Developer'),
        ('backend', 'Backend Developer'),
        ('fullstack', 'Full Stack Developer'),
        ('designer', 'UI/UX Designer'),
        ('tester', 'QA Tester'),
    ]
    
    # ========== BASIC INFO (EXISTING) ==========
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    
    work_life_balance = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )


    """
    feelings and teamworking skills are effected by player actions and 
    scenarios, and then dictate what characters will do
    """

    # energy is kinda being used like character XP or health
    initial_energy = models.IntegerField(
        default = 75,
        validators = [
            MinValueValidator(0), 
            MaxValueValidator(100)
        ],
    )

    # character feelings
    
    """
    0.35 is min
    0.65 is low
    1.00 is baseline, not too low not too high
    2.00 is high
    3.00 is max
    """
    # can't change this til i check how its being used by others
    initial_happiness = models.IntegerField(
        default=100,
        validators = [
            MinValueValidator(0), 
            MaxValueValidator(100)
        ],
    )
    initial_confidence = models.IntegerField(
        default=100,
        validators = [
            MinValueValidator(50), 
            MaxValueValidator(200)
        ],
    )
    initial_dedication = models.IntegerField(
        default=100,
        validators = [
            MinValueValidator(50), 
            MaxValueValidator(200)
        ],
    )
    initial_stress = models.IntegerField(
        default=100,
        validators = [
            MinValueValidator(50), 
            MaxValueValidator(200)
        ],
    )
    initial_irritability = models.IntegerField(
        default=100,
        validators = [
            MinValueValidator(50), 
            MaxValueValidator(200)
        ],
    )

    # teamworking skills
    initial_skill_level = models.IntegerField(
        default=100,
        validators = [
            MinValueValidator(50), 
            MaxValueValidator(200)
        ],
    )
    initial_communication_skills = models.IntegerField(
        default=100,
        validators = [
            MinValueValidator(50), 
            MaxValueValidator(200)
        ],
    )
    initial_reliability = models.IntegerField(
        default=100,
        validators = [
            MinValueValidator(50), 
            MaxValueValidator(200)
        ],
    )
    initial_teachability = models.IntegerField(
        default=100,
        validators = [
            MinValueValidator(50), 
            MaxValueValidator(200)
        ],
    )
    

    primary_role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='fullstack',
        help_text="Character's main expertise - affects energy efficiency on matching tasks"
    )
    
    secondary_role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        null=True,
        blank=True,
        help_text="Character's secondary skill - minor energy efficiency on matching tasks"
    )
    
    works_well_under_pressure = models.BooleanField(
        default=False,
        help_text="ENERGY EFFECT: Energy cost reduced by 50% in last 3 days (10→5 per day). Can sprint to finish without rest."
    )

    team_player = models.BooleanField(
        default=False,
        help_text="ENERGY EFFECT: No energy penalty when overstaffed. Normally overstaffing costs +20% energy, Team Players work at base cost."
    )

    night_owl = models.BooleanField(
        default=False,
        help_text="ENERGY EFFECT: Recovers 35 energy when resting (instead of 20). 75% better energy recovery."
    )

    perfectionist = models.BooleanField(
        default=False,
        help_text="ENERGY EFFECT: Energy cost +30% (10→13 per day) BUT final project score +30%. High risk, high reward."
    )

    # Does not do anything currently, just flavour text
    PERSONALITY_TYPE_CHOICES = [
        ('perfectionist_type', 'Perfectionist Type'),
        ('speedster_type', 'Speedster Type'),
        ('team_player_type', 'Team Player Type'),
        ('solo_expert_type', 'Solo Expert Type'),
        ('creative_type', 'Creative Type'),
    ]
    
    personality_type = models.CharField(
        max_length=30,  
        choices=PERSONALITY_TYPE_CHOICES,
        default='team_player_type',
        help_text="Determines compatibility with other characters (relationship web)"
    )
    
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self):
        """Returns full name"""
        return f"{self.first_name} {self.last_name}"
    
    def get_role_display_full(self):
        """Returns primary role and secondary role if exists"""
        primary = self.get_primary_role_display()
        if self.secondary_role:
            secondary = dict(self.ROLE_CHOICES)[self.secondary_role]
            return f"{primary} / {secondary}"
        return primary
    
    def get_traits_list(self):
        """Returns list of active trait names for display"""
        traits = []
        if self.works_well_under_pressure:
            traits.append('Works Well Under Pressure')
        if self.team_player:
            traits.append('Team Player')
        if self.night_owl:
            traits.append('Night Owl')
        if self.perfectionist:
            traits.append('Perfectionist')
        return traits
    
    def get_traits_display(self):
        """Returns traits as comma-separated string"""
        traits = self.get_traits_list()
        return ', '.join(traits) if traits else 'No special traits'
    
    def get_personality_type_icon(self):
        """Returns emoji/icon for personality type"""
        icons = {
            'perfectionist_type': '🎯',
            'speedster_type': '⚡',
            'team_player_type': '🤝',
            'solo_expert_type': '🔨',
            'creative_type': '🎨',
        }
        return icons.get(self.personality_type, '👤')
    
    class Meta:
        ordering = ['first_name', 'last_name']