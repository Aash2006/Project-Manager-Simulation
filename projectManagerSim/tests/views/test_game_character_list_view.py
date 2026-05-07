from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.management import call_command
from projectManagerSim.models import Character


class GameCharacterListViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        call_command('seed', verbosity=0)
        self.user = User.objects.get(username='player1')
        self.client.login(username='player1', password='password123')
        from projectManagerSim.services import game
        self.save = game.get_save_or_none(self.user)
        if not self.save:
            characters = Character.objects.order_by('pk')[:4]
            game.create_save(self.user, characters)
            self.save = game.get_save_or_none(self.user)

    def test_characters_page_loads(self):
        response = self.client.get(reverse('game_characters'))
        self.assertEqual(response.status_code, 200)

    def test_characters_in_context(self):
        response = self.client.get(reverse('game_characters'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('characters', response.context)

    def test_relationships_in_context(self):
        response = self.client.get(reverse('game_characters'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('relationships', response.context)

    def test_redirects_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(reverse('game_characters'))
        self.assertNotEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        response = self.client.get(reverse('game_characters'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'game_characters.html')