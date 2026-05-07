function updateRestingButtons() {
    return;
}

function attachListeners() {
  document.querySelectorAll('.set-resting-btn').forEach(btn => {
    btn.removeEventListener('click', handleSetResting)
    btn.addEventListener('click', handleSetResting)
  })

  document.querySelectorAll('.remove-task-btn').forEach(btn => {
    btn.removeEventListener('click', handleRemoveTask)
    btn.addEventListener('click', handleRemoveTask)
  })
}

// Handler function
async function handleSetResting(e) {
    const btn = e.target.closest('.set-resting-btn');
    
    if (!btn) return; // Safety check

    const saveCharacterId = btn.dataset.saveCharacterId;
    const targetRestingState = btn.dataset.resting === 'true';
    const card = btn.closest('.character-card');

    console.log("ID Found:", saveCharacterId);

    // Call your fetch function
    const success = await setCharacterResting(saveCharacterId, targetRestingState);

    console.log("Continuing with ", saveCharacterId);
    
    animateProgressBars();
}
async function handleRemoveTask(e) {
  const saveCharacterId = e.currentTarget.dataset.saveCharacterId
  await removeTask(saveCharacterId)
  animateProgressBars();
}

document.addEventListener('DOMContentLoaded', () => {
  attachListeners()
})