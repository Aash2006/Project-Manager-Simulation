async function handleAssignTask(e) {
  const taskId = e.currentTarget.dataset.taskId
  const saveCharacterId = e.currentTarget.dataset.saveCharacterId
  await assignTask(taskId, saveCharacterId)
}

function updateRestingButtons() {
    console.log("Updating task card!")
    
    return;
}
async function handleRemoveTask(e) {
  const saveCharacterId = e.currentTarget.dataset.saveCharacterId
  await removeTask(saveCharacterId)
}

// Attach listeners safely (only once)
function attachListeners() {
  document.querySelectorAll('.assign-task-btn').forEach(btn => {
    btn.removeEventListener('click', handleAssignTask)
    btn.addEventListener('click', handleAssignTask)
  })
  document.querySelectorAll('.remove-task-btn').forEach(btn => {
    btn.removeEventListener('click', handleRemoveTask)
    btn.addEventListener('click', handleRemoveTask)
  })
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  attachListeners()
})
