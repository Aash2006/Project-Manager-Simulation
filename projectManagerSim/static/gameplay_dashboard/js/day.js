    async function startDay(saveId) {
      try {
        const response = await fetch(window.ENDPOINTS.startDay, {
          method: 'POST',
          headers: {
            'X-CSRFToken': window.CSRF_TOKEN,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ save_id: saveId })
        })

        console.log(response);
        if (!response.ok) throw new Error('Failed to start day')

        const data = await response.json()
        console.log('start day response:', data)
        if (!data.success) throw new Error('Start day failed')
          
        
        // If the deadline is reached, we redirect to the given redirect
        if (data.run_finished) {
          window.location.replace(`${data.redirect}`);
          return;
        }
        
        // Update days in project dynamically
        const daysText = document.getElementById('days-in-project-text');
        if (daysText && data.current_day !== undefined) {
          daysText.textContent = `Day ${data.current_day} / ${data.total_days}`;
        }
        
        // Update all character cards
        data.updated_save_characters.forEach((charData) => {
          const oldCard = document.getElementById('character-card-' + charData.save_character_id)
          if (oldCard) {
            oldCard.outerHTML = charData.character_card_html
          }
        })
        
        // Update character progress list
        const list = document.getElementById('start-day-list');
        if (!list) {
          console.warn('Start day list element not found in DOM');
          return;
        }
        
        list.innerHTML = '';
        data.updated_save_characters.forEach((updated_save_character) => {
          const li = document.createElement('li');
          let text = `${updated_save_character.first_name} ${updated_save_character.last_name} - New Energy: ${updated_save_character.current_energy}% - Project Score: ${updated_save_character.progress} pts`;
          
          // Add warning if present
          if (updated_save_character.warning) {
            text += ` ${updated_save_character.warning}`;
          }
          
          // Add deferral time if present
          if (updated_save_character.deferral_time > 0) {
            text += ` - Days Deferred: ${updated_save_character.deferral_time}`;
          }
          
          li.textContent = text;
          list.appendChild(li);
        });

        // Update progress bar
        const progressBar = document.getElementById('project-progress-bar');
        if (progressBar && data.current_progress_percent !== undefined) {
          progressBar.style.width = `${data.current_progress_percent}%`;
          progressBar.textContent = `${data.current_progress_percent}%`;
        }

        // Check for game over
        if (data.game_over) {
          const bugPercent = typeof getBugPercent === 'function' ? getBugPercent() : 0;
          return;
        }

        // Update messages widget
        const messageCheck = document.getElementById('messages');
        if (messageCheck) messageCheck.innerHTML = data.messages_html;
        closeAndResetWidget();
        const attention = document.getElementById('attention');
        if (attention) attention.innerHTML = data.requires_attention_html;
        
        // Refresh buttons and listeners
        updateRestingButtons()
        attachListeners()

        showMyPopup('A day has happened!', '...and a new day begins! Check the progress and characters to see what happened. Get ready for the new day!')
        
      } catch (error) {
        console.error('Start day failed', error)
        alert('Start day failed, see console for details: ' + error.message)
      }
    }



async function testDay(saveId) {
  console.log('testDay called with saveId:', saveId);
  closeAndResetWidget();

  try {
    // Fetch precheck data via GET
    const response = await fetch(`${window.ENDPOINTS.savePrecheck}?save_id=${saveId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    console.log('Response received, status:', response.status);
    if (!response.ok) throw new Error('Save precheck failed');

    const data = await response.json();
    console.log('start day response:', data)
    console.log('Save precheck JSON data:', data);

    const character_warnings = data.character_warnings || [];

    if (character_warnings.length === 0) {
      console.log('No warning characters to show');
      startDay(saveId);
      return;
    }

    // Update the modal list
    const list = document.getElementById('low-energy-list');
    if (!list) {
      console.warn('Low energy list element not found in DOM');
      return;
    }

    list.innerHTML = '';
    character_warnings.forEach((character_warning) => {
      if (character_warning.type === 'low_energy') {
        const li = document.createElement('li');
        li.textContent = `${character_warning.first_name} ${character_warning.last_name} has low energy (${character_warning.current_energy}%) and is not resting! They have a higher chance to fail their task and will subtract project score.`;
        list.appendChild(li);
      } else if (character_warning.type === 'unassigned_task') {
        const li = document.createElement('li');
        li.textContent = `${character_warning.first_name} ${character_warning.last_name} does not have an assigned task and is not resting! This will subtract project score.`;
        list.appendChild(li);
      }
      
    });

    // Show the modal
    const modalEl = document.getElementById('lowEnergyModal');
    if (!modalEl) {
      console.warn('Low energy modal element not found in DOM');
      startDay(saveId);
      return;
    }

    // Show the modal and wait for user decision
    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();

    const userDecision = await new Promise((resolve) => {
      const acceptBtn = document.getElementById('proceed-day-button'); // Accept
      const cancelBtn = document.getElementById('cancel-day-button');  // Cancel

      // If user clicks accept
      if (acceptBtn) {
        acceptBtn.onclick = () => {
          bsModal.hide();
          resolve('accept'); // resolve with a value
        };
      }

      // If user clicks cancel
      if (cancelBtn) {
        cancelBtn.onclick = () => {
          bsModal.hide();
          resolve('cancel'); // resolve with a different value
        };
      }

      // Optional: fallback if no buttons
      if (!acceptBtn && !cancelBtn) {
        resolve('none');
      }
    });

    if (userDecision === 'accept') {
      startDay(saveId);
      // continue your updates / start day
    } else if (userDecision === 'cancel') {
      console.log('User cancelled the day');
      // maybe stop the function or do something else
    } else {
      console.log('No user decision possible');
    }

  } catch (error) {
    console.error('Precheck request failed:', error);
    alert('Precheck request failed: ' + error.message);
  }
}

