import pytest

@pytest.fixture
def stats_page(browser_with_active_game):
    # Navigate to Statistics
    link = browser_with_active_game.links.find_by_partial_href('statistics/').first
    link.click()
    return browser_with_active_game

@pytest.mark.django_db(transaction=True)
def test_overall_progress_display(stats_page):
    """
    Test that the statistics page shows the correct stats
    """
    browser = stats_page
    save = browser.game_save

    save.progress_percent = 45
    save.score = 1250
    save.save()
    browser.reload()

    assert browser.is_text_present("Overall Progress")
    assert browser.is_text_present("45%")
    assert browser.is_text_present("1250")

@pytest.mark.django_db(transaction=True)
def test_character_stats_table(stats_page):
    """
    Test that the statistics page shows the table correctly
    """
    browser = stats_page

    assert browser.is_text_present("Character Statistics")
    table = browser.find_by_css("table").first
    assert "energy" in table.text.lower()
    assert "happiness" in table.text.lower()

    char = browser.game_save.characters.first()
    char.current_energy = 88
    char.save()
    
    browser.reload()
    
    assert browser.is_text_present(char.character.first_name)
    assert browser.is_text_present("88%")

@pytest.mark.django_db(transaction=True)
def test_chart_empty_state(stats_page):
    """
    Test that the statistics page shows the correct value when empty
    """
    browser = stats_page
    
    assert browser.is_text_present("No daily statistics yet")