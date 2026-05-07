    // AJAX Functions
    async function setCharacterResting(saveCharacterId, isResting) {
      try {
        const response = await fetch(window.ENDPOINTS.toggleResting, {
          method: 'POST',
          headers: {
            'X-CSRFToken': window.CSRF_TOKEN,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            save_character_id: saveCharacterId,
            is_resting: isResting
          })
        })
    
        const data = await response.json()
        if (!data.success) return
    
        // Replace old card
        const oldCard = document.getElementById('character-card-' + saveCharacterId)
        if (!oldCard) return
    
        oldCard.outerHTML = data.character_card_html
    
        // Get the new card
        const newCard = document.getElementById('character-card-' + saveCharacterId)
        if (!newCard) return
    
        // Move to correct list
        const workingList = document.getElementById('working-list')
        const restingList = document.getElementById('resting-list')
    
        if (isResting && restingList) {
          restingList.prepend(newCard)
        } else if (!isResting && workingList) {
          workingList.prepend(newCard)
        }
    
        // Reattach listeners
        attachListeners()
        updateRestingButtons()
      } catch (error) {
        console.error('Updating resting state failed', error)
      }
    }