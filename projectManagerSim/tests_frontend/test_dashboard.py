import time

import pytest

@pytest.mark.django_db(transaction=True)
def test_dashboard_stats_and_progress(browser_with_active_game):
    """
    Checks that the basic UI on the dashboard appears correctly 
    """
    browser = browser_with_active_game

    progress_pct = browser.find_by_id("progressPct").text
    assert "50" in progress_pct

    progress_bar = browser.find_by_id("project-progress-bar")
    assert "width: 50%" in progress_bar['style']

    assert browser.is_text_present("Day 10")

def test_message_widget_toggle(browser_with_active_game):
    """
    Checks that you can toggle the message widget
    """
    browser = browser_with_active_game
    
    menu = browser.find_by_id("messaging-menu")
    assert "d-none" in menu['class']

    widget_button = browser.find_by_css("button[onclick='toggleWidget()']")
    widget_button.click()

    assert "d-none" not in menu['class']
    assert menu.visible

@pytest.mark.django_db(transaction=True)
def test_requires_attention_alerts(browser_with_active_game):
    """
    Checks that requires attention alerts appear when put there 
    """

    browser = browser_with_active_game
    save = browser_with_active_game.game_save

    char_to_fix = save.characters.first()
    char_to_fix.current_energy = 100
    char_to_fix.is_resting = True
    char_to_fix.save()

    browser.reload()

    
    alert_col = browser.find_by_xpath("//h5[contains(text(), 'fully rested')]/..")
    tasks_link = alert_col.find_by_tag("a").first
    
    assert "Go to Tasks" in tasks_link.text
    assert "/game/tasks/" in tasks_link['href']

@pytest.mark.django_db(transaction=True)
def test_message_widget_and_badges(browser_with_active_game):
    """
    Check that messages badge updates with the amount of decisions + 
    Check that messages show up when you click
    """
    browser = browser_with_active_game

    
    save = browser.game_save
    save.refresh_from_db()
    save.available_decisions = [
        {"id": 1, "title": "Too Long", "text": "Can You Feel It?"},
        {"id": 2, "title": "Audio, Video", "text": "Disco"},
        {"id": 3, "title": "We Are", "text": "Your Friends"},
        {"id": 3, "title": "Robot", "text": "Rock"}
    ]
    save.save()

    time.sleep(0.2)
    browser.reload()

    badge = browser.find_by_id("global-badge").first
    assert badge.text == "4"

    browser.find_by_css("button[onclick='toggleWidget()']").click()

    messaging_menu = browser.find_by_id("messaging-menu")
    assert messaging_menu.visible
    assert browser.is_text_present("Too Long")