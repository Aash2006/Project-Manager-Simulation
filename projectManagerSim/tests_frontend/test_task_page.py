import time

import pytest
from selenium.common import UnexpectedAlertPresentException
from projectManagerSim.models import Task, TaskType
from django.middleware.csrf import get_token

@pytest.fixture
def tasks_setup(browser_with_active_game):
    save = browser_with_active_game.game_save
    taskType = TaskType.objects.create(task_type_name="Human After All")
    for i in ["One More Time", "Harder Better Faster Stronger", "Genesis", "Face To Face", "Superheroes", "Randy"]:
        Task.objects.create(
            game_save=save,
            name=i,
            task_type=taskType,
            number_of_people_required=1,
            time_to_complete=2,
            is_completed=False
        )
    tasks_url = f"/game/tasks/"
    tasks_link = browser_with_active_game.find_by_css(f'a[href="{tasks_url}"]').first
    tasks_link.click()
    
    return browser_with_active_game

@pytest.mark.django_db(transaction=True)
def test_task_details_update_on_click(tasks_setup):
    """
    Check Task display update on click
    """
    browser = tasks_setup
    
    task_button = browser.find_by_text("One More Time").first
    task_button.click()

    assert browser.find_by_id("task-name").text == "One More Time"
    assert browser.find_by_id("task-type").text == "Human After All"
    
    assert "1 person" in browser.find_by_id("task-requirement").text

@pytest.mark.django_db(transaction=True)
def test_assign_menu_presence_and_action(tasks_setup, client):
    """
    Checks that the task assign menu works correctly in adding characters
    """
    browser = tasks_setup
    
    client.get('/') 
    token = get_token(client.request().wsgi_request)
    
    browser.cookies.add({'csrftoken': token})
    
    browser.reload()

    browser.find_by_text("One More Time").first.click()
    browser.find_by_css("#task-asign-menu .dropdown-toggle").first.click()
    browser.find_by_css(".assign-task-btn").first.click()
    
    import time
    time.sleep(1) 
    
    browser.reload()
    browser.find_by_text("One More Time").first.click()
    assert "Guy-Manuel" in browser.find_by_id("task-assignees").text


@pytest.mark.django_db(transaction=True)
def test_remove_task_assignee_flow(tasks_setup, client):
    """
    Checks that you can assign and then remove a character correctly
    """
    browser = tasks_setup
    
    client.get('/') 
    token = get_token(client.request().wsgi_request)
    
    browser.cookies.add({'csrftoken': token})
    
    browser.reload()

    browser.find_by_text("One More Time").first.click()
    browser.find_by_css("#task-asign-menu .dropdown-toggle").first.click()
    browser.find_by_css(".assign-task-btn").first.click()
    
    import time
    time.sleep(1) 
    
    browser.reload()
    browser.find_by_text("One More Time").first.click()
    assert "Guy-Manuel" in browser.find_by_id("task-assignees").text
    
    assert browser.is_element_present_by_css(".remove-assignee-btn", wait_time=3)
    
    remove_btn = browser.find_by_css(".remove-assignee-btn").first
    remove_btn.click()
    
    time.sleep(1)

    browser.reload()

    browser.find_by_text("One More Time").first.click()

    assignees_container = browser.find_by_id("task-assignees")
    
    assert "Guy-Manuel" not in assignees_container.text