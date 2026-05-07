# projectManagerSim/tests_frontend/test_character_select.py

import pytest
import time
from django.middleware.csrf import get_token


def skip_tutorial_if_present(browser):
    time.sleep(1)
    skip_btn = browser.find_by_id("tutorialSkipBtn")
    if skip_btn:
        try:
            browser.execute_script("arguments[0].click();", skip_btn.first._element)
            time.sleep(0.5)
        except Exception:
            pass


def skip_tour_if_present(browser):
    time.sleep(0.5)
    skip_btn = browser.find_by_css(".tour-skip-btn")
    if skip_btn:
        try:
            browser.execute_script("arguments[0].click();", skip_btn.first._element)
            time.sleep(0.5)
        except Exception:
            pass


@pytest.mark.django_db(transaction=True)
def test_character_selection_mechanics(browser_with_inactive_game):
    browser = browser_with_inactive_game

    skip_tutorial_if_present(browser)
    
    # DEBUG: Print page HTML to see what's there
    print("\n=== DEBUGGING CHARACTER SELECTION PAGE ===")
    print(f"URL: {browser.url}")
    print(f"Page has selected-count: {browser.is_element_present_by_id('selected-count')}")
    
    # Check for various selectors
    print(f"Has .character-checkbox: {len(browser.find_by_css('.character-checkbox'))}")
    print(f"Has .select-button: {len(browser.find_by_css('.select-button'))}")
    print(f"Has input[type=checkbox]: {len(browser.find_by_css('input[type=checkbox]'))}")
    print(f"Has .character-card: {len(browser.find_by_css('.character-card'))}")
    print(f"Has button elements: {len(browser.find_by_tag('button'))}")
    
    # Print first character card if it exists
    cards = browser.find_by_css('.character-card')
    if cards:
        print(f"\nFirst card HTML snippet:\n{cards.first.html[:500]}")

    assert browser.find_by_id("selected-count").text == "0"
    confirm_btn = browser.find_by_id("confirm-team")
    assert confirm_btn.has_class("disabled") or confirm_btn['disabled'] == 'true'
    
    # Try to find checkboxes
    select_elements = browser.find_by_css('input[type="checkbox"]')
    if not select_elements:
        select_elements = browser.find_by_css('.select-button')
    if not select_elements:
        select_elements = browser.find_by_css('.character-checkbox')
    
    assert len(select_elements) >= 4, f"Expected at least 4 selection elements, found {len(select_elements)}"

    for i in range(4):
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_elements[i]._element)
        time.sleep(0.3)
        browser.execute_script("arguments[0].click();", select_elements[i]._element)
        time.sleep(0.3)

    assert browser.find_by_id("selected-count").text == "4"
    assert not confirm_btn.has_class("disabled")

    toggle_btn = browser.find_by_css(".toggle-relationships").first
    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", toggle_btn._element)
    time.sleep(0.3)
    browser.execute_script("arguments[0].click();", toggle_btn._element)
    rel_list = browser.find_by_css(".relationships-list").first
    assert rel_list.visible


@pytest.mark.django_db(transaction=True)
def test_confirm_team_and_redirect(browser_with_inactive_game, client):
    browser = browser_with_inactive_game

    skip_tutorial_if_present(browser)

    client.get('/')
    token = get_token(client.request().wsgi_request)
    browser.cookies.add({'csrftoken': token})
    browser.reload()

    skip_tutorial_if_present(browser)

    # Try multiple selectors with priority order
    select_elements = browser.find_by_css('input[type="checkbox"]')
    if not select_elements:
        select_elements = browser.find_by_css('.select-button')
    if not select_elements:
        select_elements = browser.find_by_css('.character-checkbox')
    
    for i in range(4):
        browser.execute_script("arguments[0].scrollIntoView();", select_elements[i]._element)
        time.sleep(0.5)
        browser.execute_script("arguments[0].click();", select_elements[i]._element)
        time.sleep(0.1)

    confirm_btn = browser.find_by_id("confirm-team")
    browser.execute_script("arguments[0].scrollIntoView();", confirm_btn._element)
    time.sleep(0.5)
    browser.execute_script("arguments[0].click();", confirm_btn._element)
    time.sleep(2)

    skip_tour_if_present(browser)

    assert browser.is_text_present("Dashboard", wait_time=10)
    assert "/game/dashboard/" in browser.url