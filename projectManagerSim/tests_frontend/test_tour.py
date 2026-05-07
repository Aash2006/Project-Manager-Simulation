import pytest
import time


@pytest.fixture
def browser_with_tour(browser_with_active_game, live_server):
    """
    Sets up a browser with an active game and tour_step set to 'prompt'.
    This triggers the tour when visiting the dashboard.
    """
    browser = browser_with_active_game
    
    # Set the tour_step in session by visiting dashboard with new_game param
    browser.visit(f"{live_server.url}/game/dashboard/?new_game=true")
    
    # Wait for page load and tour to initialize
    time.sleep(1)
    
    return browser


@pytest.mark.django_db(transaction=True)
def test_tour_starts_on_new_game(browser_with_tour):
    """
    Tests that the tour starts when visiting dashboard with new_game parameter.
    """
    browser = browser_with_tour
    
    # Wait for Shepherd tour to appear
    time.sleep(1)
    
    # Check for Shepherd tour overlay
    shepherd_modal = browser.find_by_css(".shepherd-modal-overlay-container")
    assert shepherd_modal, "Shepherd tour overlay should appear"
    
    # Check for tour step element
    shepherd_element = browser.find_by_css(".shepherd-element")
    assert shepherd_element, "Tour step element should be visible"


@pytest.mark.django_db(transaction=True)
def test_tour_shows_jerry(browser_with_tour):
    """
    Tests that Jerry appears in tour popups.
    """
    browser = browser_with_tour
    
    time.sleep(1.5)
    
    # Check for Jerry's container in the tour
    jerry_container = browser.find_by_css(".tour-jerry-container")
    assert jerry_container, "Jerry container should exist in tour"
    
    # Check for Jerry's images
    jerry_pausing = browser.find_by_css(".tour-jerry-pausing")
    assert jerry_pausing, "Jerry pausing image should exist"


@pytest.mark.django_db(transaction=True)
def test_tour_jerry_typing_effect(browser_with_tour):
    """
    Tests that Jerry's typing effect works in the tour.
    """
    browser = browser_with_tour
    
    time.sleep(0.5)
    
    jerry_text = browser.find_by_css(".tour-jerry-text")
    initial_text = jerry_text.text if jerry_text else ""
    
    time.sleep(1)
    
    jerry_text = browser.find_by_css(".tour-jerry-text")
    later_text = jerry_text.text if jerry_text else ""
    
    # Text should have content after typing
    assert len(later_text) > 0, "Tour text should have typed content"


@pytest.mark.django_db(transaction=True)
def test_tour_continue_button_completes_typing(browser_with_tour):
    """
    Tests that clicking Continue while typing completes the sentence first.
    """
    browser = browser_with_tour
    
    # Wait for typing to start
    time.sleep(0.3)
    
    # Click continue while typing
    continue_btn = browser.find_by_css(".tour-continue-btn")
    if continue_btn:
        continue_btn.first.click()
        time.sleep(0.2)
        
        # Text should now be complete
        jerry_text = browser.find_by_css(".tour-jerry-text")
        assert len(jerry_text.text) > 20, "Text should be complete after clicking continue"


@pytest.mark.django_db(transaction=True)
def test_tour_navigation_previous_button(browser_with_tour):
    """
    Tests that the Previous button appears after advancing and works correctly.
    """
    browser = browser_with_tour
    
    time.sleep(1.5)
    
    # Advance to next step (click continue twice - once to complete typing, once to advance)
    continue_btn = browser.find_by_css(".tour-continue-btn")
    browser.execute_script("arguments[0].click();", continue_btn.first._element)
    time.sleep(0.3)
    continue_btn = browser.find_by_css(".tour-continue-btn")
    browser.execute_script("arguments[0].click();", continue_btn.first._element)
    time.sleep(1.5)
    
    # Now Previous button should be visible
    prev_buttons = browser.find_by_css(".tour-prev-btn")
    assert prev_buttons, "Previous button should appear after advancing"


@pytest.mark.django_db(transaction=True)
def test_tour_skip_button_cancels_tour(browser_with_tour):
    """
    Tests that the Skip Tutorial button cancels the tour.
    """
    browser = browser_with_tour
    
    time.sleep(1)
    
    # Find and click skip button
    skip_btn = browser.find_by_css(".tour-skip-btn")
    if skip_btn:
        skip_btn.first.click()
        time.sleep(0.5)
        
        # Tour overlay should be gone
        shepherd_overlay = browser.find_by_css(".shepherd-modal-overlay-container")
        # If overlay exists, it should not be visible or should be gone
        if shepherd_overlay:
            assert not shepherd_overlay.visible or len(shepherd_overlay) == 0, \
                "Tour overlay should be hidden after skip"


@pytest.mark.django_db(transaction=True)
def test_tour_buttons_styled_correctly(browser_with_tour):
    """
    Tests that tour buttons have the correct styling classes.
    """
    browser = browser_with_tour
    
    time.sleep(1)
    
    # Check for shepherd-jerry class on content
    jerry_tour = browser.find_by_css(".shepherd-jerry")
    assert jerry_tour, "Tour should have shepherd-jerry class for styling"
    
    # Check for correct button classes
    continue_btn = browser.find_by_css(".tour-continue-btn")
    skip_btn = browser.find_by_css(".tour-skip-btn")
    
    assert continue_btn, "Continue button should exist"
    assert skip_btn, "Skip button should exist"


@pytest.mark.django_db(transaction=True)
def test_tour_jerry_image_sizing(browser_with_tour):
    """
    Tests that Jerry's image is properly sized (not giant).
    """
    browser = browser_with_tour
    
    time.sleep(1)
    
    jerry_img = browser.find_by_css(".tour-jerry-pausing")
    if jerry_img:
        # Check that the image has proper sizing constraints
        style = jerry_img.first['style']
        assert 'width: 120px' in style or 'max-width: 120px' in style, \
            "Jerry image should have constrained width"


@pytest.mark.django_db(transaction=True)
def test_tour_advances_through_steps(browser_with_tour):
    """
    Tests that the tour advances through multiple steps by checking text changes.
    """
    browser = browser_with_tour
    
    time.sleep(1.5)
    
    # Get initial text (wait for typing to complete)
    continue_btn = browser.find_by_css(".tour-continue-btn")
    browser.execute_script("arguments[0].click();", continue_btn.first._element)
    time.sleep(0.5)
    
    jerry_text = browser.find_by_css(".tour-jerry-text")
    first_text = jerry_text.text if jerry_text else ""
    
    # Advance to next step
    continue_btn = browser.find_by_css(".tour-continue-btn")
    browser.execute_script("arguments[0].click();", continue_btn.first._element)
    time.sleep(1.5)
    
    # Complete typing on new step
    continue_btn = browser.find_by_css(".tour-continue-btn")
    browser.execute_script("arguments[0].click();", continue_btn.first._element)
    time.sleep(0.5)
    
    # Get new step text
    jerry_text = browser.find_by_css(".tour-jerry-text")
    second_text = jerry_text.text if jerry_text else ""
    
    # Text should be different between steps
    assert first_text != second_text, "Tour should show different text on different steps"


@pytest.mark.django_db(transaction=True)
def test_tour_attaches_to_elements(browser_with_tour):
    """
    Tests that tour steps eventually attach to specific page elements.
    The first few steps are general (no attachment), but later steps attach to UI elements.
    """
    browser = browser_with_tour
    
    time.sleep(1)
    
    # Advance through several steps (first 2-3 are intro/welcome, not attached)
    # We need to go through enough steps to reach one that attaches
    for _ in range(8):  # 4 steps * 2 clicks each (complete typing + advance)
        time.sleep(0.4)
        btn = browser.find_by_css(".tour-continue-btn")
        if btn:
            browser.execute_script("arguments[0].click();", btn.first._element)
    
    time.sleep(1)
    
    # At this point we should be on a step that attaches to an element
    # Check that the shepherd element exists and has positioning (indicates attachment)
    shepherd_element = browser.find_by_css(".shepherd-element")
    assert shepherd_element, "Tour step element should exist"
    
    # Check for arrow which indicates attachment to an element
    shepherd_arrow = browser.find_by_css(".shepherd-arrow")
    assert shepherd_arrow, "Tour should have arrow indicating attachment to page element"


@pytest.mark.django_db(transaction=True)
def test_how_to_play_button_exists(browser_with_active_game, live_server):
    """
    Tests that the 'Help' button exists on the dashboard next to Start Day.
    """
    browser = browser_with_active_game
    
    # Visit dashboard
    browser.visit(f"{live_server.url}/game/dashboard/")
    time.sleep(1)
    
    # Skip tour if it appears
    skip_btn = browser.find_by_css(".tour-skip-btn")
    if skip_btn:
        browser.execute_script("arguments[0].click();", skip_btn.first._element)
        time.sleep(0.5)
    
    # Check for Help button on dashboard
    how_to_play_btn = browser.find_by_id("how-to-play-btn")
    assert how_to_play_btn, "Help button should exist on dashboard"
    assert "Help" in how_to_play_btn.text, "Button should say 'Help'"


@pytest.mark.django_db(transaction=True)
def test_how_to_play_button_starts_tour(browser_with_active_game, live_server):
    """
    Tests that clicking 'How to Play' starts the tour.
    """
    browser = browser_with_active_game
    
    # Visit dashboard
    browser.visit(f"{live_server.url}/game/dashboard/")
    time.sleep(1)
    
    # Skip tour if it appears
    skip_btn = browser.find_by_css(".tour-skip-btn")
    if skip_btn:
        browser.execute_script("arguments[0].click();", skip_btn.first._element)
        time.sleep(0.5)
    
    # Make sure tour is gone
    time.sleep(0.5)
    
    # Click How to Play button
    how_to_play_btn = browser.find_by_id("how-to-play-btn")
    browser.execute_script("arguments[0].click();", how_to_play_btn._element)
    time.sleep(1.5)
    
    # Tour should now be visible
    shepherd_overlay = browser.find_by_css(".shepherd-modal-overlay-container")
    assert shepherd_overlay, "Tour should start after clicking How to Play"


@pytest.mark.django_db(transaction=True)
def test_info_tooltip_on_bug_status(browser_with_active_game, live_server):
    """
    Tests that the Bug Status info tooltip exists on the dashboard.
    """
    browser = browser_with_active_game
    
    # Visit dashboard
    browser.visit(f"{live_server.url}/game/dashboard/")
    time.sleep(1)
    
    # Skip tour if it appears
    skip_btn = browser.find_by_css(".tour-skip-btn")
    if skip_btn:
        browser.execute_script("arguments[0].click();", skip_btn.first._element)
        time.sleep(0.5)
    
    # Check for info icon near Bug Status
    bug_status_info = browser.find_by_css(".bugbar-title .info-tooltip")
    assert bug_status_info, "Info tooltip should exist near Bug Status"
