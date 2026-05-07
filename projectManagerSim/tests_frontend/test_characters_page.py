import time

import pytest
from selenium.common import UnexpectedAlertPresentException
from projectManagerSim.models import Task, TaskType
from django.middleware.csrf import get_token

@pytest.fixture
def teammates_page(browser_with_active_game):
    teammates_url = "/game/teammates/"
    teammates_link = browser_with_active_game.find_by_css(f'a[href="{teammates_url}"]').first
    teammates_link.click()

    save = browser_with_active_game.game_save
    taskType = TaskType.objects.create(task_type_name="Human After All")
        
    Task.objects.create(
        game_save=save,
        name="One More Time",
        task_type=taskType,
        number_of_people_required=1,
        time_to_complete=2,
        is_completed=False
    )
    
    assert "teammates" in browser_with_active_game.url
    return browser_with_active_game

@pytest.mark.django_db(transaction=True)
def test_toggle_resting_status(teammates_page, client):
    """
    Test that clicking set to rest button makes the character rest
    """
    browser = teammates_page
    
    from django.middleware.csrf import get_token
    client.get('/')
    token = get_token(client.request().wsgi_request)
    browser.cookies.add({'csrftoken': token})
    browser.reload()

    char_name = "Guy-Manuel de Homem-Christo"
    assert browser.is_text_present(char_name)
    
    rest_button = browser.find_by_css(".set-resting-btn[data-resting='true']").first
    rest_button.click()

    time.sleep(1)
    browser.reload()

    work_button = browser.find_by_css(".set-resting-btn[data-resting='false']").first
    assert work_button.visible
    
    card = browser.find_by_id(f"character-card-{browser.game_save.characters.first().id}")
    assert "is-resting" in card['class']

def test_character_info_modal(browser_with_active_game, live_server):
    """Test that clicking Info button shows character details."""
    import time
    browser = browser_with_active_game
    browser.visit(live_server.url + "/game/teammates/")

    info_buttons = browser.find_by_text("Info")
    assert len(info_buttons) > 0, "No Info buttons found on page"
    info_buttons.first.click()

    time.sleep(0.5)

    back_divs = browser.find_by_css('[id^="back-"]')
    assert len(back_divs) > 0, "No back content divs found"

    page_html = browser.html
    assert "Description" in page_html or "Personality" in page_html, \
        "Character info not visible after clicking Info"

@pytest.mark.django_db(transaction=True)
def test_remove_task_from_teammate_card(teammates_page, client):
    """
    Test that removing task works correctly
    """
    browser = teammates_page
    save = browser.game_save
    
    char = save.characters.first()
    task = save.tasks.first()
    char.task_assigned = task
    char.save()
    browser.reload()

    assert browser.is_text_present(task.name)

    remove_btn = browser.find_by_css(".remove-task-btn").first
    remove_btn.click()
    
    time.sleep(1)
    browser.reload()

    assert browser.is_text_present("No task currently assigned")