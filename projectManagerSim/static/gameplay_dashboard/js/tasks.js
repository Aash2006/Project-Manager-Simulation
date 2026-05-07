async function assignTask(taskId, saveCharacterId) {
      try {
        const response = await fetch(window.ENDPOINTS.assignTask, {
          method: 'POST',
          headers: {
            'X-CSRFToken': window.CSRF_TOKEN,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            task_id: taskId,
            save_character_id: saveCharacterId
          })
        })
        console.log("We're doing ", saveCharacterId, taskId)
        if (!response.ok) throw new Error('Failed to assign task')
    
        const data = await response.json()
    
        // Replace character card
        const characterCard = document.getElementById('character-card-' + saveCharacterId)
        if (characterCard) characterCard.outerHTML = data.character_card_html
    
        // Replace task menu
        const taskMenuCard = document.getElementById('task-assign-menu-card')
        if (taskMenuCard) taskMenuCard.outerHTML = data.task_assign_menu_html
    
        // Replace task page
        const taskPage = document.getElementById('taskPage')
        if (taskPage) taskPage.outerHTML = data.task_page_html

        
    
        // Reattach listeners to new buttons
        attachListeners()
        updateRestingButtons()
      } catch (error) {
        console.error('Assignment failed', error)
        alert('Assignment failed, see console for details')
      }
    }

    async function removeTask(saveCharacterId) {
      try {
        const response = await fetch(window.ENDPOINTS.removeTask, {
          method: 'POST',
          headers: {
            'X-CSRFToken': window.CSRF_TOKEN,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            save_character_id: saveCharacterId
          })
        })
    
        if (!response.ok) throw new Error('Failed to remove task')
    
        const data = await response.json()
    
        // Replace character card
        const characterCard = document.getElementById('character-card-' + saveCharacterId)
        if (characterCard) characterCard.outerHTML = data.character_card_html
    
        // Replace task menu
        const taskMenuCard = document.getElementById('task-assign-menu-card')
        if (taskMenuCard) taskMenuCard.outerHTML = data.task_assign_menu_html

        // Replace task page
        const taskPage = document.getElementById('taskPage')
        if (taskPage) {
          taskPage.outerHTML = data.task_page_html
          console.log("We got a taskPage!")
        } else {
          console.log("We didn't get a taskPage!")
        }
    
        // Reattach listeners to new buttons
        attachListeners()
        updateRestingButtons()

      } catch (error) {
        console.error('Removal failed', error)
        alert('Removal failed, see console for details')
      }
    }


    async function updateTask(saveCharacterId) {
      try {
        const response = await fetch(window.ENDPOINTS.getTask, {
          method: 'POST',
          headers: {
            'X-CSRFToken': window.CSRF_TOKEN,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            save_character_id: saveCharacterId
          })
        })
        if (!response.ok) throw new Error('Failed to get task')
    
        const data = await response.json()
    
        // Replace character card
        const characterCard = document.getElementById('character-card-' + saveCharacterId)
        if (characterCard) characterCard.outerHTML = data.character_card_html
    
        // Replace task menu
        const taskMenuCard = document.getElementById('task-assign-menu-card')
        if (taskMenuCard) taskMenuCard.outerHTML = data.task_assign_menu_html
    
        // Reattach listeners to new buttons
        attachListeners()
        updateRestingButtons()

      } catch (error) {
        console.error('Update failed', error)
        alert('Update failed, see console for details')
      }
    }