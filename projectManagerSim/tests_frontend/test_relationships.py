import pytest

@pytest.fixture
def relationships_page(browser_with_active_game):
    browser_with_active_game.find_by_css(f'a[href="/game/relationships/{browser_with_active_game.game_save.id}/"]').first.click()
    return browser_with_active_game

@pytest.mark.django_db(transaction=True)
def test_relationship_selector_navigation(relationships_page):
    browser = relationships_page
    
    selector = browser.find_by_id("character-select").first
    assert selector.value is not None
    
    target_char = browser.game_save.characters.filter(character__first_name="Angèle Joséphine Aimée Van Laeken").first()
    
    browser.find_by_id("character-select").select(str(target_char.character.id))
    
    assert f"character_id={target_char.character.id}" in browser.url
    
    assert browser.is_text_present("Angèle Joséphine Aimée Van Laeken's Relationships")

@pytest.mark.django_db(transaction=True)
def test_relationship_card_content(relationships_page):
    """
    Tests if the relationships show correctly
    """
    browser = relationships_page
    
    assert browser.is_text_present("'s Relationships")
    
    if browser.is_element_present_by_css(".relationship-card"):
        card = browser.find_by_css(".relationship-card").first
        assert card.find_by_css(".relationship-name").visible
        assert card.find_by_css(".badge").visible
        
        assert "energy cost" in card.text
    else:
        assert browser.is_text_present("No relationships defined with teammates")