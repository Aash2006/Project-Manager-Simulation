document.addEventListener("click", function(event) {
    const loadBtn = event.target.closest(".load-task");
    if (loadBtn) {
        event.preventDefault();
        handleLoadTask(loadBtn);
        return;
    }

    const removeBtn = event.target.closest(".remove-assignee-btn");
    if (removeBtn) {
        handleRemoveAssignee(removeBtn);
        return;
    }
    
});

function handleLoadTask(button) {
    document.getElementById("task-name").innerText = button.dataset.name;
    document.getElementById("task-type").innerText = button.dataset.type;
    document.getElementById("task-completed").innerText = 
        `Completed: ${button.dataset.completed}`;
    
    const plural_person = button.dataset.requirement == 1 ? 'person' : 'people';
    document.getElementById("task-requirement").innerHTML = 
        `<i class="bi bi-people"></i> ${button.dataset.requirement} ${plural_person}`;
    
    const duration = parseInt(button.dataset.duration);
    const daysWorked = parseFloat(button.dataset.daysworked || 0);
    const timeRemaining = duration - daysWorked;

    let durationText;
    if (daysWorked > 0) {
        const remainingText = timeRemaining === 1 ? '1 day' : `${timeRemaining.toFixed(0)} days`;
        const plural = timeRemaining != 1 ? 's' : '';
        durationText = `<i class="bi bi-clock"></i> ${timeRemaining} day${plural}`;
    } else {
        const totalText = duration === 1 ? '1 day' : `${duration} days`;
        durationText = `<i class="bi bi-clock"></i> ${totalText}`;
    }
    document.getElementById("task-duration").innerHTML = durationText;

    document.getElementById("task-assignees").innerHTML = 
        `${button.dataset.assignees}`;
        
    document.getElementById("task-asign-menu").innerHTML = 
        button.dataset.assignlist;

    // Re-bind specific task buttons if they exist
    if (typeof handleAssignTask === "function") {
        document.querySelectorAll('.assign-task-btn').forEach(btn => {
            btn.removeEventListener('click', handleAssignTask);
            btn.addEventListener('click', handleAssignTask);
        });
    }
}

function handleRemoveAssignee(button) {
    const saveCharacterId = button.dataset.savecharacterid;
    fetch(window.ENDPOINTS.removeTask, {
          method: 'POST',
          headers: {
            'X-CSRFToken': window.CSRF_TOKEN,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            save_character_id: saveCharacterId
          })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.task_page_html) {
            // Replace task page
            const taskPage = document.getElementById('taskPage')
            if (taskPage) {
                taskPage.outerHTML = data.task_page_html
            }
            // Reattach listeners to new buttons
            attachListeners()
            updateRestingButtons()
        }
    })
    .catch(err => console.error("Removal failed:", err));
}