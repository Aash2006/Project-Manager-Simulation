import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from projectManagerSim.models.save import Save
from projectManagerSim.models.decisions.decision import Decision
from projectManagerSim.models.decisions.option import Option

class DecisionViewTests(TestCase):
    def setUp(self):
        # 1. Setup User
        self.user = User.objects.create_user(username="player1", password="password")
        self.client = Client()
        self.client.login(username="player1", password="password")
        
        # 2. Setup Save - CRITICAL: active=True to satisfy the decorator
        self.game_save = Save.objects.create(
            user=self.user,
            save_name="Active Save",
            active=True,  # This prevents the 302 redirect
            available_decisions=[],
            score=20
        )

        # 3. Setup Decision and Options
        self.decision = Decision.objects.create(
            game_save=self.game_save,
            title="Crisis Meeting",
            body="The servers are down!"
        )
        # The view requires at least 2 options
        self.opt1 = Option.objects.create(decision=self.decision, text="Fix it", score_effect=10)
        self.opt2 = Option.objects.create(decision=self.decision, text="Ignore it", score_effect=-10)

    def test_get_decision_success(self):
        """Test GET returns 200 now that active=True is set."""
        url = reverse("get_decision")
        response = self.client.get(url, {'decision_id': self.decision.pk})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "Crisis Meeting")
        self.assertEqual(data["option1"]["option_id"], self.opt1.pk)

    def test_get_decision_not_found(self):
        """Test the 404 branch when a bad ID is passed."""
        url = reverse("get_decision")
        response = self.client.get(url, {'decision_id': 9999})
        self.assertEqual(response.status_code, 404)

    def test_process_decision_full_integration(self):
        """Test POST applies effects and updates the save's JSON list."""
        url = reverse("process_decision")
        
        # Pre-populate the JSON list as the view expects
        self.game_save.available_decisions = [
            {'id': self.decision.pk, 'title': self.decision.title, 'body' : self.decision.body, 'options': [{'id': self.opt1.id, 'text': self.opt1.text}, {'id': self.opt2.id, 'text': self.opt2.text}]}
        ]
        self.game_save.save()

        payload = {
            "decision_id": self.decision.pk,
            "option_id": self.opt1.pk
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        
        # Verify database updates
        self.game_save.refresh_from_db()
        # 1. Decision removed from JSON list
        self.assertEqual(len(self.game_save.available_decisions), 0)
        # 2. Score effect applied (20 + 10 = 30)
        self.assertEqual(self.game_save.score, 30)

    def test_process_decision_invalid_data(self):
        """Test 400 response for malformed JSON."""
        url = reverse("process_decision")
        response = self.client.post(
            url,
            data=json.dumps({"wrong_key": "data"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_get_decision_insufficient_options(self):
        """Tests the 500 error branch when a decision has only 1 option."""
        bad_decision = Decision.objects.create(game_save=self.game_save, title="Broken")
        Option.objects.create(decision=bad_decision, text="Lonely Option")
        
        url = reverse("get_decision")
        response = self.client.get(url, {'decision_id': bad_decision.pk})
        self.assertEqual(response.status_code, 500)