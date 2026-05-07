from django.db import models

class TaskType(models.Model):
    """Types of tasks like backend, frontend, API, database design, etc."""
    task_type_name = models.CharField(max_length = 50, unique = True)

    ROLE_CHOICES = [
        ('frontend', 'Frontend Developer'),
        ('backend', 'Backend Developer'),
        ('fullstack', 'Full Stack Developer'),
        ('designer', 'UI/UX Designer'),
        ('tester', 'QA Tester'),
    ]
    
    required_role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='fullstack',
        help_text="Role required for this task type"
    )

    def __str__(self):
        return self.task_type_name
    
# for if we want task types to be allowed for multiple roles
class Role(models.Model):
    name = models.CharField(max_length=100)
    primary_task_types = models.ManyToManyField(TaskType, related_name="primary_roles")
    secondary_task_types = models.ManyToManyField(TaskType, related_name="secondary_roles")