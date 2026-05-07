from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Save(models.Model):
    """User's game save data"""
    class Status(models.TextChoices):
        ONGOING = 'ONGOING', 'Ongoing'
        COMPLETED = 'COMPLETED', 'Completed'
    
    status = models.CharField(
        max_length = 10,
        choices = Status.choices,
        default = Status.ONGOING
    )
    
    active = models.BooleanField(
        default = False,
    )
    
    user = models.ForeignKey(
        User, 
        on_delete = models.CASCADE,
        related_name = 'saves'
        )
    
    save_name = models.CharField(max_length = 100, blank=True) 

    available_decisions = models.JSONField(
        null = True, 
        blank = True, 
    )

    progress_percent = models.IntegerField(
        default = 0,
        validators = [MinValueValidator(0), MaxValueValidator(100)]
    )

    score = models.IntegerField(
        default = 0
    )
    
    final_grade = models.CharField(
        max_length = 10,
        null = True, 
        blank = True, 
    )

    current_day = models.IntegerField(
        default = 1,
        validators = [MinValueValidator(0)]
    )

    total_days = models.IntegerField(
        default = 42,
        validators = [MinValueValidator(1)]
    )

    available_decisions = models.JSONField(
        null = True, 
        blank = True, 
    )

    started_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    # Statistics fields
    total_tasks_completed = models.IntegerField(default=0)
    total_tasks_failed = models.IntegerField(default=0)
    total_energy_consumed = models.IntegerField(default=0)
    total_bugs_fixed = models.IntegerField(default=0)
    total_decisions_made = models.IntegerField(default=0)
    highest_daily_progress = models.IntegerField(default=0)
    
    # JSON field for detailed history
    daily_stats = models.JSONField(
        null=True,
        blank=True,
        default=list,
        help_text="Array of daily statistics"
    )


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.save_name} - {self.user.username}"
    
    def update_progress(self, amount):
        result = self.progress_percent + amount
        self.progress_percent = max(0, min(100, result))
        self.save()

    def update_score(self, amount):
        """Update the game score by amount, clamped to [-100, 100]"""
        result = self.score + amount 
        self.score = max(-100, min(100, result)) 
        self.save()

    def deactivate(self):
        self.active = False
        self.save()
    
    def get_days_until_deadline(self):
        return self.total_days - self.current_day
    
    def remove_decision(self, decision):
        """Remove a decision thats been made from the m2m relationship"""
        self.decisions.remove(decision)
        self.save()
    def get_characters(self):
        return self.characters.all()
    
    @property
    def is_finished(self):
        return self.current_day >= self.total_days or self.progress_percent >= 100
    
    class Meta:
        ordering = ['-last_used']
        constraints = [
            models.UniqueConstraint(
                fields=["user"], 
                condition=models.Q(active=True), 
                name="unique_active_user_save")
                # Only one save per user is active at any time
        ]

