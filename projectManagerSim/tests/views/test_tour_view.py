import json
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class TourViewTests(TestCase):
    """Tests for tour and for info icons"""
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.url = reverse("complete_tour")
        self.client.force_login(self.user)

    def test_complete_tour_requires_post(self):
        """GET request should be rejected"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_complete_tour_sets_next_step(self):
        """POST with next_step should set it in session."""
        response = self.client.post(
            self.url,
            data=json.dumps({"next_step": "dashboard"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(self.client.session.get("tour_step"), "dashboard")

    def test_complete_tour_sets_characters_step(self):
        """POST with characters step should set it in session."""
        response = self.client.post(
            self.url,
            data=json.dumps({"next_step": "characters"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get("tour_step"), "characters")

    def test_complete_tour_sets_tasks_step(self):
        """POST with tasks step should set it in session."""
        response = self.client.post(
            self.url,
            data=json.dumps({"next_step": "tasks"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get("tour_step"), "tasks")

    def test_complete_tour_sets_relationships_step(self):
        """POST with relationships step should set it in session."""
        response = self.client.post(
            self.url,
            data=json.dumps({"next_step": "relationships"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get("tour_step"), "relationships")

    def test_complete_tour_with_null_marks_complete(self):
        """POST with null next_step should mark tour as complete."""
        response = self.client.post(
            self.url,
            data=json.dumps({"next_step": None}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertIsNone(self.client.session.get("tour_step"))
        self.assertTrue(self.client.session.get("tour_complete"))

    def test_complete_tour_handles_empty_body(self):
        """POST with empty body should complete tour."""
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertIsNone(self.client.session.get("tour_step"))
        self.assertTrue(self.client.session.get("tour_complete"))

    def test_complete_tour_handles_invalid_json(self):
        """POST with invalid JSON should still succeed """
        response = self.client.post(
            self.url,
            data="not valid json",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)

    def test_tour_step_progression_flow(self):
        """Test full tour progression"""
        response = self.client.post(
            self.url,
            data=json.dumps({"next_step": "prompt"}),
            content_type="application/json"
        )
        self.assertEqual(self.client.session.get("tour_step"), "prompt")
        
        # Move to dashboard
        response = self.client.post(
            self.url,
            data=json.dumps({"next_step": "dashboard"}),
            content_type="application/json"
        )
        self.assertEqual(self.client.session.get("tour_step"), "dashboard")
        
        # Move to characters
        response = self.client.post(
            self.url,
            data=json.dumps({"next_step": "characters"}),
            content_type="application/json"
        )
        self.assertEqual(self.client.session.get("tour_step"), "characters")
        
        # Move to tasks
        response = self.client.post(
            self.url,
            data=json.dumps({"next_step": "tasks"}),
            content_type="application/json"
        )
        self.assertEqual(self.client.session.get("tour_step"), "tasks")
        
        # Move to relationships
        response = self.client.post(
            self.url,
            data=json.dumps({"next_step": "relationships"}),
            content_type="application/json"
        )
        self.assertEqual(self.client.session.get("tour_step"), "relationships")
        
        # Complete tour
        response = self.client.post(
            self.url,
            data=json.dumps({"next_step": None}),
            content_type="application/json"
        )
        self.assertIsNone(self.client.session.get("tour_step"))
        self.assertTrue(self.client.session.get("tour_complete"))

    def test_skip_tour_early(self):
        """Test that skipping tour at any point marks it complete."""
        self.client.post(
            self.url,
            data=json.dumps({"next_step": "dashboard"}),
            content_type="application/json"
        )
        
        # Skip it
        response = self.client.post(
            self.url,
            data=json.dumps({"next_step": None}),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.client.session.get("tour_step"))
        self.assertTrue(self.client.session.get("tour_complete"))


class TourDashboardIntegrationTests(TestCase):
    """Integration tests for tour functionality in the dashboard."""

    def setUp(self):
        from projectManagerSim.models import Character, Save, SaveCharacter, Task, TaskType
        
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        
        # Create save
        self.save = Save.objects.create(
            user=self.user, active=True, save_name="Test Game"
        )
        
        # Create character and save character
        self.character = Character.objects.create(
            first_name="Test", last_name="Character", description="Test"
        )
        self.save_character = SaveCharacter.objects.create(
            game_save=self.save,
            character=self.character,
            current_energy=100,
            is_resting=False,
        )
        
        # Create task type and task
        self.task_type = TaskType.objects.create(task_type_name="Test")
        self.task = Task.objects.create(
            name="Test Task",
            time_to_complete=5,
            task_type=self.task_type,
            energy_cost=10,
            unlocks_at_percent=0
        )
        
        self.client.force_login(self.user)

    def test_dashboard_includes_tour_step_in_context(self):
        """Dashboard should include tour_step from session."""
        session = self.client.session
        session["tour_step"] = "dashboard"
        session.save()
        
        response = self.client.get(reverse("game_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["tour_step"], "dashboard")

    def test_dashboard_shows_tour_when_prompt_step(self):
        """Dashboard should show tour when tour_step is prompt."""
        session = self.client.session
        session["tour_step"] = "prompt"
        session.save()
        
        response = self.client.get(reverse("game_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context.get("show_tour"))

    def test_dashboard_shows_tour_when_dashboard_step(self):
        """Dashboard should show tour when tour_step is dashboard."""
        session = self.client.session
        session["tour_step"] = "dashboard"
        session.save()
        
        response = self.client.get(reverse("game_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context.get("show_tour"))

    def test_dashboard_shows_tour_with_query_param(self):
        """Dashboard should show tour when tour=true query param."""
        response = self.client.get(reverse("game_dashboard") + "?tour=true")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context.get("show_tour"))

    def test_dashboard_no_tour_by_default(self):
        """Dashboard should not show tour by default."""
        response = self.client.get(reverse("game_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context.get("show_tour"))

    def test_dashboard_includes_how_to_play_button(self):
        """Dashboard should include the How to Play button."""
        response = self.client.get(reverse("game_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Help")  # Changed from "How to Play"
        self.assertContains(response, "how-to-play-btn")

    def test_dashboard_includes_bug_status_info_icon(self):
        """Dashboard should include info icon for bug status."""
        response = self.client.get(reverse("game_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "bi-info-circle")
        self.assertContains(response, "The lower the score the better!")


class CharacterSelectionTourTests(TestCase):
    """Tests for tour activation in character selection."""

    def setUp(self):
        from projectManagerSim.models import Character
        
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        
        # Create 4 characters for selection
        for i in range(4):
            Character.objects.create(
                first_name=f"Char{i}",
                last_name=f"Test{i}",
                description=f"Test character {i}"
            )
        
        self.url = reverse("game_start_new")
        self.client.force_login(self.user)

    def test_new_game_sets_tour_step_to_prompt(self):
        """Creating a new game should set tour_step to prompt."""
        from projectManagerSim.models import Character
        
        char_ids = list(Character.objects.values_list("id", flat=True)[:4])
        
        response = self.client.post(
            self.url,
            data=json.dumps({"selected_characters": char_ids}),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertEqual(self.client.session.get("tour_step"), "prompt")
