"""
Service for handling task progression and completion during a game day.
"""
from dataclasses import dataclass


@dataclass
class TaskCompletion:
    """Information about a completed task"""
    name: str
    character: str
    days_taken: float


class TaskProgressService:
    """Handles task progression, overstaffing bonuses, and completion"""
    
    def __init__(self, task, team_size, required_size, task_workers):
        self.task = task
        self.team_size = team_size
        self.required_size = required_size
        self.task_workers = task_workers
    
    def advance_task(self, is_first_worker, high_energy=True):
        """
        Advance task progress and check for completion.
        Returns (completed: bool, completion_info: TaskCompletion | None)
        """
        if not is_first_worker:
            return False, None
        
        if self.team_size < self.required_size:
            # Understaffed - no progress
            return False, None
        
        # Calculate days increment based on team size and energy
        days_increment = self._calculate_days_increment(high_energy)
        self.task.days_worked += days_increment
        
        # Check if task is complete
        if self.task.days_worked >= self.task.time_to_complete:
            completion = self._complete_task()
            self.task.save()
            return True, completion
        
        self.task.save()
        return False, None
    
    def _calculate_days_increment(self, high_energy):
        """Calculate how many days of progress to add"""
        if self.team_size == self.required_size:
            return 1 if high_energy else 0
        
        extra_workers = self.team_size - self.required_size

        if high_energy:
            if extra_workers == 1:
                return 2
            else:
                return 3  # 2+ extra workers, capped at 3×
        else:
            if extra_workers == 1:
                return 1
            else:
                return 2
    
    def _complete_task(self):
        """Mark task as complete and unassign all workers"""
        self.task.is_completed = True  # ← Correct field name
        
        # Auto-unassign all workers
        # task_workers is already a list of workers for this specific task
        for worker in self.task_workers:
            worker.task_assigned = None
            worker.save()
        
        return TaskCompletion(
            name=self.task.name,
            character=f"Team of {self.team_size}",
            days_taken=self.task.days_worked
        )