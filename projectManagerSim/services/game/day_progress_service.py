import json

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse

from projectManagerSim.models import SaveCharacter, Task, Decision
from projectManagerSim.services.game import CharacterWorkService, TaskProgressService, generate_decisions

class DayProgressService:
    """
    Handles Progressing a Day and handling all the changes in game state.
    """
    def __init__(self, save, request, engine):
        self.save = save 
        self.request = request
        self.engine = engine
    
    def progress_day(self):
        self.save.current_day += 1

        # Group workers by tasks
        task_workers = self._group_workers_by_task()
        
        # Process each character
        results = self._process_all_characters(task_workers)
        
        # Update game state
        self._update_game_progress(self.save, results)
        
        # Check for game end
        if self.save.is_finished:
            return self._handle_game_end(self.save)
        
        # Generate and manage decisions
        self._process_decisions(self.save, self.request)

        # Remove characters who have left
        SaveCharacter.objects.filter(game_save=self.save).filter(leaving=True).delete()
        
        return self._build_success_response(self.save, results, self.request)
    


    def _group_workers_by_task(self):
        """Group characters by their assigned tasks"""
        task_workers = {}
        
        for character in self.engine.characters:
            if not character.is_resting and character.task_assigned:
                task_id = character.task_assigned.id
                if task_id not in task_workers:
                    task_workers[task_id] = []
                task_workers[task_id].append(character)
        
        print(f"Task workers grouped: {len(task_workers)} tasks")
        for task_id, workers in task_workers.items():
            print(f"  Task {task_id}: {len(workers)} workers - {[w.character.first_name for w in workers]}")
        
        return task_workers
    
    def _process_all_characters(self, task_workers):
        results = {
            'updated_characters': [],
            'completed_tasks': [],
            'total_progress': 0,
            'total_points': 0
        }

        # Snapshot task assignments before any processing
        original_assignments = {
            character.id: character.task_assigned_id
            for character in self.engine.characters
        }

        for character in self.engine.characters:
            char_result = self._process_single_character(
                character, task_workers, results, original_assignments
            )
            results['updated_characters'].append(char_result)
            results['total_progress'] += char_result['progress']

        return results
    
    def _process_single_character(self, character, task_workers, results, original_assignments):
        """Process a single character's work for the day"""
        energy_before = character.current_energy
        work_service = CharacterWorkService(character)

        was_assigned_to_task = original_assignments.get(character.id) is not None
        was_resting = character.is_resting


        # Handle deferral time if applicable
        if character.is_resting and character.deferral_time > 0:
            character.deferral_time -= 1
            character.save()

        if character.current_energy > 80:
            character.lock_rest = False
            character.lock_task = False
            character.save()

        if not character.task_assigned:
            character.lock_task = False
            character.save()

        if was_resting:
            work_result = work_service.process_resting()
        elif was_assigned_to_task:
            character.refresh_from_db()
            if character.task_assigned is None:
                # Task completed this cycle — character worked, give them credit
                from projectManagerSim.services.game.character_work_service import WorkResult
                work_result = WorkResult(progress_points=25)
            else:
                work_result = self._process_character_work(character, task_workers, results)
        else:
            work_result = work_service.process_idle()


        results['total_points'] += self._calculate_points(work_result, character.task_assigned, task_workers)
        character_html = render_to_string(
            'game/partials/teammate_card.html',
            {'sc': character},
            request=self.request
        )

        return {
            'first_name': character.character.first_name,
            'last_name': character.character.last_name,
            'current_energy': character.current_energy,
            'energy_before': energy_before,
            'save_character_id': character.id,
            'character_card_html': character_html,
            'current_happiness': character.current_happiness,
            'progress': work_result.progress_points,
            'warning': work_result.warning,
            'deferral_time': character.deferral_time,
        }

    def _process_character_work(self, character, task_workers, results):
        """Process character working on a task"""

        # Check for deferral (energy too low)
        if character.current_energy <= 30:
            return self._handle_task_deferral(character)
        
        work_service = CharacterWorkService(character)
        task = character.task_assigned
        
        # Get workers on this specific task
        workers_on_this_task = task_workers.get(task.id, [])
        team_size = len(workers_on_this_task)
        required_size = task.number_of_people_required
        
        # Apply task happiness effect
        character.apply_task_happiness_effect(task.name)
        
        # Determine if high energy
        high_energy = character.current_energy >= 50
        
        # Handle work with relationship modifiers
        work_result = work_service.process_working(
            task, 
            team_size, 
            required_size,
            task_workers=workers_on_this_task
        )
        
        # Add warning if low energy but not deferred
        if character.current_energy < 50:
            work_result.warning = f"⚠️ {character.character.first_name} worked at reduced efficiency (low energy)"
        
        # Check if this is the first worker on the task (by ID order)
        is_first_worker = (workers_on_this_task[0].id == character.id)
        
        if is_first_worker and team_size >= required_size:
            self._advance_task(
                task, 
                team_size, 
                required_size, 
                workers_on_this_task,
                high_energy,  # Task advances slower if team lead has low energy
                results
            )
        
        return work_result
    
    def _handle_task_deferral(self, character):
        """Handle character deferring task due to low energy"""
        from projectManagerSim.services.game.character_work_service import WorkResult
        
        if character.deferral_time != 5:
            character.deferral_time += 1
            character.save()
            return WorkResult(
                progress_points=-10,
                warning=f"⚠️ {character.character.first_name} deferred work due to low energy"
            )
        else:
            # After 5 days of deferral, energy resets
            character.current_energy = 50
            character.deferral_time = 0
            character.save()
            return WorkResult(progress_points=0)
    
    def _advance_task(self, task, team_size, required_size, task_workers, high_energy, results):
        """Advance task progress and handle completion"""
        task_service = TaskProgressService(task, team_size, required_size, task_workers)
        is_complete, completion_info = task_service.advance_task(
            is_first_worker=True,  # Already checked before calling this method
            high_energy=high_energy
        )
        
        if is_complete and completion_info:
            results['completed_tasks'].append({
                'name': completion_info.name,
                'character': completion_info.character,
                'days_taken': completion_info.days_taken
            })
            results['total_points'] += 100
    
    def _calculate_points(self, work_result, task_assigned, task_workers):
        """Calculate points based on work result"""
        if work_result.progress_points >= 20:
            return 15  # Good work
        elif work_result.progress_points >= 0:
            return 5   # Low energy success
        elif work_result.progress_points >= -20:
            return -20 # Understaffed or deferral
        else:
            return -30 # Failed
    

    
    def _process_decisions(self, save, request):
        """Generate and manage decision messages"""
        # Update deadlines for active decisions
        
        # Generate random decisions for this day
        
        decisions = generate_decisions(save, count=2)
        serialized_decisions = [
            {
                'id': d.id,
                'title': d.title,
                'body': d.body,
                'options': [{'id': o.id, 'text': o.text} for o in d.options.all()]
            }
            for d in decisions
        ]
        
        for decision in save.decisions.filter(is_made=False, is_served=True):
            if hasattr(decision, 'update_deadline'):
                decision.update_deadline()
        print(serialized_decisions)
        
        # Add to available decisions
        if save.available_decisions is None:
            save.available_decisions = []
        
        save.available_decisions.extend(serialized_decisions)
        
        # Remove stale decisions (already made)
        decisions_remove_stale = []
        for d in save.available_decisions:
            decision_object = Decision.objects.filter(game_save=save).filter(pk=d['id']).first()
            if decision_object is None or decision_object.is_made:
                print(f"Stale decision {d['title']} ({d['id']})")
            else:
                decisions_remove_stale.append(d)
                print(d)
        
        save.available_decisions = decisions_remove_stale
        #print(save.available_decisions)
        save.save(update_fields=['available_decisions'])
    
    def _handle_game_end(self, save):
        """Handle game completion"""
        
        print("We're after our final day... end!")
        return JsonResponse({
            'success': True,
            'run_finished': True,
            'redirect': reverse('game_end'),
        })
    
    def _build_success_response(self, save, results, request):
        """Build successful day completion response"""
        print("==== StartDayView POST rendered ====")
        
        # Render messages HTML
        save_character = self.engine.characters.first() if self.engine.characters else None
        messages_html = render_to_string(
            "partials/messages_inner.html",
            {'save': save, 'save_character': save_character},
            request=request
        )
        save_characters = self.engine.characters
        working_characters = save_characters.filter(is_resting=False)
        resting_characters = save_characters.filter(is_resting=True)
        working_no_task = working_characters.filter(task_assigned=None)
        low_energy = working_characters.filter(current_energy__lte=20)
        max_energy = resting_characters.filter(current_energy=100)
        requires_attention_html = render_to_string(
            "partials/requires_attention.html",
            {
                "save": save,
                "save_characters": save_characters,
                "working_characters": working_characters,
                "resting_characters": resting_characters,
                "working_no_task": working_no_task,
                "low_energy": low_energy,
                "max_energy": max_energy,
            },
            request=request
        )
        
        return JsonResponse({
            'success': True,
            'run_finished': False,
            'current_day': save.current_day,
            'total_days': save.total_days,
            'updated_save_characters': results['updated_characters'],
            'total_progress': results['total_progress'],
            'current_progress_percent': save.progress_percent,
            'completed_tasks': results.get('completed_tasks', []), 
            'decisions': save.available_decisions,
            'game_over': False,
            'messages_html': messages_html,
            'requires_attention_html' : requires_attention_html, 
        })
    
    def _update_game_progress(self, save, results):
        """Update overall game progress based on completed tasks"""
        total_tasks = Task.objects.filter(game_save=save).count()
        completed_count = Task.objects.filter(game_save=save, is_completed=True).count()

        if total_tasks > 0:
            save.progress_percent = int((completed_count / total_tasks) * 100)
        else:
            save.progress_percent = 0

        save.score = max(0, save.score + results['total_points'])

        # ── stat tracking ────────────────────────────────────────────────────
        tasks_completed_today = len(results.get('completed_tasks', []))
        save.total_tasks_completed += tasks_completed_today

        # Count failures: any character whose work_result was a hard fail (-30 pts)
        # We approximate from the per-character results list
        failed_today = sum(
            1 for cr in results.get('updated_characters', [])
            if cr.get('progress', 0) <= -30
        )
        save.total_tasks_failed += failed_today

        # Energy consumed: sum of energy lost by all characters this day
        energy_consumed_today = sum(
            max(0, cr.get('energy_before', cr['current_energy']) - cr['current_energy'])
            for cr in results.get('updated_characters', [])
        )
        save.total_energy_consumed += energy_consumed_today
        # ─────────────────────────────────────────────────────────────────────

        if save.daily_stats is None:
            save.daily_stats = []

        save.daily_stats.append({
            'day': save.current_day,
            'progress_gained': results['total_progress'],
            'tasks_completed': tasks_completed_today,
            'score_gained': results['total_points'],
            'tasks_failed': failed_today,
            'energy_consumed': energy_consumed_today,
        })

        if results['total_progress'] > save.highest_daily_progress:
            save.highest_daily_progress = results['total_progress']

        save.save()