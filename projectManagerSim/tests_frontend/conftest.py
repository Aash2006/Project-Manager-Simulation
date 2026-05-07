import pytest
from splinter import Browser
from itertools import combinations
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from django.conf import settings
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.models import User
from projectManagerSim.models import Character, Save, SaveCharacter, CharacterRelationship
from projectManagerSim.models.character_template_relationships import CharacterTemplateRelationship
from splinter.config import Config

@pytest.fixture(scope="session")
def browser():
    """Set up the browser once for the whole test session."""
    executable_path = ChromeDriverManager().install()
    config = Config(headless=True)
    b = Browser("chrome", service=Service(executable_path), config=config)
    b.driver.set_window_size(960, 1080)
    yield b
    b.quit()

@pytest.fixture(autouse=True)
def clean_browser(browser):
    """Ensures every test starts on a blank page."""
    browser.visit("about:blank")

@pytest.fixture
def logged_in_browser(browser, live_server, db):
    """
    Creates a user, logs them in via session cookies, 
    and returns a browser ready to hit the dashboard.
    """
    password = "password123"
    user = User.objects.create_user(username="test_manager", password=password)

    session = SessionStore()
    session[SESSION_KEY] = str(user.pk)
    session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.save()

    browser.visit(f"{live_server.url}/404/") 
    browser.cookies.add({settings.SESSION_COOKIE_NAME: session.session_key})
    
    browser.user_pk = user.pk
    return browser

@pytest.fixture
def browser_with_active_game(logged_in_browser, live_server):
    """
    Automates the 'New Game' process
    """
    user = User.objects.get(pk=logged_in_browser.user_pk)

    chars = []
    first_name_list = [
        "Guy-Manuel de Homem-Christo", "Xavier de Rosnay", 
        "Mike Lévy", "Angèle Joséphine Aimée Van Laeken"
    ]
    for i in range(4):
        char = Character.objects.create(
            first_name=first_name_list[i],
            last_name='',
            description='Developer',
            work_life_balance=60,
            primary_role='frontend',
            secondary_role='designer',
            personality_type='perfectionist_type',
            perfectionist=True,
            night_owl=True,
            works_well_under_pressure=False,
            team_player=False,
        )
        chars.append(char)

    game_save = Save.objects.create(
        user=user,
        save_name="Test Save",
        progress_percent=50,
        current_day=10,
        score=85,
        active=True
    )

    for char in chars:
        SaveCharacter.objects.create(
            game_save=game_save,
            character=char,
            current_energy=100,
            current_happiness=100
        )
    for char1, char2 in combinations(SaveCharacter.objects.all(), 2):
        CharacterRelationship.objects.create(
            character_a=char1,
            character_b=char2,
            relationship_score=-50
        )

    logged_in_browser.visit(f"{live_server.url}/game/start/")

    continue_links = logged_in_browser.links.find_by_text("Continue Game")
    
    if continue_links:
        continue_links.first.click()
    else:
        menu_buttons = logged_in_browser.find_by_css('.menu-buttons a.btn')
        if menu_buttons:
            menu_buttons.first.click()

    logged_in_browser.game_save = game_save
    return logged_in_browser


@pytest.fixture
def browser_with_inactive_game(logged_in_browser, live_server):
    """
    Sets up character templates in the database and navigates to character selection.
    """
    first_name_list = [
        "Guy-Manuel de Homem-Christo", "Xavier de Rosnay", 
        "Mike Lévy", "Angèle Joséphine Aimée Van Laeken"
    ]
    for i in range(4):
        Character.objects.create(
            first_name=first_name_list[i],
            last_name='',
            description='Developer',
            work_life_balance=60,
            primary_role='frontend',
            secondary_role='designer',
            personality_type='perfectionist_type',
            perfectionist=True,
            night_owl=True,
            works_well_under_pressure=False,
            team_player=False,
        )
    
    logged_in_browser.visit(f"{live_server.url}/game/character-selection/")
    
    import time
    time.sleep(1)

    if not logged_in_browser.is_element_present_by_id("selected-count", wait_time=5):
        raise AssertionError("Character selection page did not load correctly")

    return logged_in_browser