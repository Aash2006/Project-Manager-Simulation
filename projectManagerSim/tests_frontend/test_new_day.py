import pytest
import time
from django.urls import reverse
from projectManagerSim.models import Save, Task
from django.middleware.csrf import get_token


def skip_tour_if_present(browser):
    """Helper to skip the tour if it appears."""
    time.sleep(0.5)
    skip_btn = browser.find_by_css(".tour-skip-btn")
    if skip_btn:
        try:
            browser.execute_script("arguments[0].click();", skip_btn.first._element)
            time.sleep(0.5)
        except Exception:
            pass


@pytest.mark.django_db(transaction=True)
def test_start_day_progression(browser_with_active_game, client):
    """
    Tests if a new day can be done
    """
    browser = browser_with_active_game
    client.get('/') 
    token = get_token(client.request().wsgi_request)
    browser.cookies.add({'csrftoken': token})
    
    browser.reload()
    
    # Skip tour if it appears
    skip_tour_if_present(browser)
    
    save = Save.objects.filter(active=True).first()
    
    assert f"Day {save.current_day}" in browser.find_by_id("days-in-project-text").text
    initial_progress = float(browser.find_by_id("progressPct").text)

    start_day_btn = browser.find_by_id("start-day-button")
    browser.execute_script("arguments[0].click();", start_day_btn._element)

    if browser.is_element_present_by_id("lowEnergyModal", wait_time=2):
        proceed_btn = browser.find_by_id("proceed-day-button")
        browser.execute_script("arguments[0].click();", proceed_btn._element)

    expected_day_text = f"Day {save.current_day + 1}"
    assert browser.is_text_present(expected_day_text, wait_time=10)

    new_progress = float(browser.find_by_id("progressPct").text)
    
    if browser.is_element_present_by_css(".decision-card"):
        assert browser.find_by_css(".decision-card").visible

@pytest.mark.django_db(transaction=True)
def test_game_over_redirection(browser_with_active_game, client):
    """
    Tests if redirected after final day
    """
    browser = browser_with_active_game
    client.get('/') 
    token = get_token(client.request().wsgi_request)
    browser.cookies.add({'csrftoken': token})
    
    browser.reload()
    
    # Skip tour if it appears
    skip_tour_if_present(browser)
    
    time.sleep(6)
    browser.game_save.current_day = browser.game_save.total_days - 1
    browser.game_save.save()
    for sc in browser.game_save.get_characters():
        sc.is_resting = True 
        sc.save()
    browser.reload()
    
    # Skip tour again after reload
    skip_tour_if_present(browser)

    start_day_btn = browser.find_by_id("start-day-button")
    browser.execute_script("arguments[0].click();", start_day_btn._element)
    
    time.sleep(3)

    assert browser.is_text_present("Project Results", wait_time=10) 
    assert "/game/results" in browser.url
