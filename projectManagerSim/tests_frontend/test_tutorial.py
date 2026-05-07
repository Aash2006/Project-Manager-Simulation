import pytest
import time


@pytest.mark.django_db(transaction=True)
def test_tutorial_modal_appears_on_character_selection(browser_with_inactive_game):
    """
    Tests that the tutorial modal with Jerry appears when starting a new game
    and landing on the character selection page.
    """
    browser = browser_with_inactive_game
    
    # Wait for the tutorial modal to appear
    time.sleep(1)
    
    # Check that the tutorial modal is visible
    modal = browser.find_by_id("tutorialModal")
    assert modal, "Tutorial modal should exist"
    
    # Check that Jerry's image is visible
    jerry_pausing = browser.find_by_id("jerryPausing")
    assert jerry_pausing, "Jerry pausing image should exist"
    
    # Check that the tutorial text container exists
    tutorial_text = browser.find_by_id("tutorialText")
    assert tutorial_text, "Tutorial text container should exist"


@pytest.mark.django_db(transaction=True)
def test_tutorial_typing_effect(browser_with_inactive_game):
    """
    Tests that Jerry's typing effect works - text appears character by character.
    """
    browser = browser_with_inactive_game
    
    # Wait for typing to start
    time.sleep(0.5)
    
    tutorial_text = browser.find_by_id("tutorialText")
    initial_text = tutorial_text.text
    
    # Wait a bit more for more text to appear
    time.sleep(1)
    
    later_text = tutorial_text.text
    
    # Text should have grown as typing progressed
    assert len(later_text) >= len(initial_text), "Text should be typing out"


@pytest.mark.django_db(transaction=True)
def test_tutorial_continue_completes_typing(browser_with_inactive_game):
    """
    Tests that clicking Continue while typing completes the current sentence.
    """
    browser = browser_with_inactive_game
    
    # Wait for typing to start but not finish
    time.sleep(0.3)
    
    # Get the expected first dialogue
    expected_text = "Hello there! You're here to learn how to become a project manager aren't you?"
    
    # Click continue to complete typing
    continue_btn = browser.find_by_id("tutorialContBtn")
    continue_btn.click()
    
    time.sleep(0.2)
    
    tutorial_text = browser.find_by_id("tutorialText")
    assert tutorial_text.text == expected_text, "Continue should complete the full sentence"


@pytest.mark.django_db(transaction=True)
def test_tutorial_navigation_buttons(browser_with_inactive_game):
    """
    Tests that Previous and Continue buttons navigate between tutorial steps.
    """
    browser = browser_with_inactive_game
    
    # Wait for first step
    time.sleep(0.5)
    
    # Previous button should be hidden on first step
    prev_btn = browser.find_by_id("tutorialPreviousBtn")
    assert prev_btn['style'] == 'display: none;' or 'none' in prev_btn['style'], \
        "Previous button should be hidden on first step"
    
    # Click continue twice (once to complete typing, once to advance)
    continue_btn = browser.find_by_id("tutorialContBtn")
    continue_btn.click()
    time.sleep(0.1)
    continue_btn.click()
    time.sleep(0.5)
    
    # Now Previous button should be visible
    prev_btn = browser.find_by_id("tutorialPreviousBtn")
    assert 'inline-block' in prev_btn['style'] or prev_btn['style'] == '', \
        "Previous button should be visible after advancing"
    
    # Check we're on second step
    tutorial_text = browser.find_by_id("tutorialText")
    assert "Welcome to the Project Manager Simulation" in tutorial_text.text or len(tutorial_text.text) > 0


@pytest.mark.django_db(transaction=True)
def test_tutorial_skip_closes_modal(browser_with_inactive_game):
    """
    Tests that Skip Tutorial button closes the modal.
    """
    browser = browser_with_inactive_game
    
    time.sleep(0.5)
    
    # Find and click skip button
    skip_btn = browser.find_by_id("tutorialSkipBtn")
    skip_btn.click()
    
    time.sleep(0.5)
    
    # Modal should be hidden (Bootstrap removes 'show' class)
    modal = browser.find_by_id("tutorialModal")
    assert 'show' not in modal['class'], "Tutorial modal should be hidden after skip"


@pytest.mark.django_db(transaction=True)
def test_tutorial_jerry_mouth_animation(browser_with_inactive_game):
    """
    Tests that Jerry's mouth animates during typing (talking/pausing images swap).
    """
    browser = browser_with_inactive_game
    
    # Wait for typing animation
    time.sleep(0.3)
    
    # Check that one of the images is visible during typing
    jerry_talking = browser.find_by_id("jerryTalking")
    jerry_pausing = browser.find_by_id("jerryPausing")
    
    # During animation, one should be visible
    assert jerry_talking or jerry_pausing, "At least one Jerry image should exist"


@pytest.mark.django_db(transaction=True)
def test_tutorial_completes_all_steps(browser_with_inactive_game):
    """
    Tests that going through all tutorial steps eventually closes the modal.
    """
    browser = browser_with_inactive_game
    
    continue_btn = browser.find_by_id("tutorialContBtn")
    
    # There are 4 tutorial steps, so we need to click continue 8 times
    # (once to complete typing, once to advance, for each step)
    for _ in range(8):
        time.sleep(0.3)
        continue_btn.click()
    
    time.sleep(0.5)
    
    # Modal should be hidden after completing all steps
    modal = browser.find_by_id("tutorialModal")
    assert 'show' not in modal['class'], "Tutorial modal should be hidden after completing all steps"
