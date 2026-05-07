// Updates the resting buttons and makes them disappear according to which list they are in (working vs resting)
function updateRestingButtons() {
  // Working cards
  document.querySelectorAll('#working-list .character-card').forEach(card => {
    const setWorkBtn = card.querySelector('[data-resting="false"]')
    const setRestBtn = card.querySelector('[data-resting="true"]')
    if (setWorkBtn) setWorkBtn.style.display = 'none'
    if (setRestBtn) setRestBtn.style.display = 'inline-block'
  })

  // Resting cards
  document.querySelectorAll('#resting-list .character-card').forEach(card => {
    const setWorkBtn = card.querySelector('[data-resting="false"]')
    const setRestBtn = card.querySelector('[data-resting="true"]')
    if (setWorkBtn) setWorkBtn.style.display = 'inline-block'
    if (setRestBtn) setRestBtn.style.display = 'none'
  })
}

// Generic popup
function showMyPopup(title, content) {
  const modal = document.getElementById('myPopupModal')
  if (!modal) return
  modal.querySelector('.modal-title').textContent = title
  modal.querySelector('.modal-body').textContent = content
  new bootstrap.Modal(modal).show()
}

/**
 * === Overall Progress bar helpers (to match bug bar style + animations) ===
 * Requires your updated HTML elements:
 * - #project-progress-bar (existing)
 * - #progressWrap (new wrapper)
 * - #progressPct (new % label)
 */
function clamp(n, lo, hi) {
  return Math.max(lo, Math.min(hi, n))
}

function parsePercentFromWidthString(widthStr) {
  // Accepts "60%" or "60" etc.
  if (!widthStr) return null
  const cleaned = String(widthStr).replace('%', '').trim()
  const n = Number(cleaned)
  return Number.isFinite(n) ? clamp(n, 0, 100) : null
}

function pulseProgressCard() {
  const wrap = document.getElementById('progressWrap')
  if (!wrap) return
  wrap.classList.remove('progresscard-pulse')
  // Force reflow so animation restarts
  void wrap.offsetWidth
  wrap.classList.add('progresscard-pulse')
}

function setOverallProgress(percent) {
  const pct = clamp(Number(percent) || 0, 0, 100)

  const bar = document.getElementById('project-progress-bar')
  const label = document.getElementById('progressPct')

  if (bar) bar.style.width = `${pct}%`
  if (label) label.textContent = String(Math.round(pct))

  pulseProgressCard()
}

// Expose helper globally so other JS files can call it safely
window.setOverallProgress = setOverallProgress

/**
 * Observe changes to the project progress bar's style attribute.
 * This means: even if another JS file updates `#project-progress-bar.style.width`,
 * we still update the label and pulse the wrapper.
 */
function observeProgressBarChanges() {
  const bar = document.getElementById('project-progress-bar')
  if (!bar) return

  const label = document.getElementById('progressPct')

  // Initialize label once from existing inline style width
  const initialPct = parsePercentFromWidthString(bar.style.width)
  if (label && initialPct !== null) {
    label.textContent = String(Math.round(initialPct))
  }

  const observer = new MutationObserver(mutations => {
    for (const m of mutations) {
      if (m.type === 'attributes' && m.attributeName === 'style') {
        const pct = parsePercentFromWidthString(bar.style.width)
        if (pct === null) return

        if (label) label.textContent = String(Math.round(pct))
        pulseProgressCard()
      }
    }
  })

  observer.observe(bar, { attributes: true, attributeFilter: ['style'] })
}

// Handler functions
async function handleSetResting(e) {
  const saveCharacterId = e.currentTarget.dataset.saveCharacterId
  const isResting = e.currentTarget.dataset.resting === 'true'
  await setCharacterResting(saveCharacterId, isResting)
}

async function handleAssignTask(e) {
  const taskId = e.currentTarget.dataset.taskId
  const saveCharacterId = e.currentTarget.dataset.saveCharacterId
  await assignTask(taskId, saveCharacterId)
}

async function handleRemoveTask(e) {
  const saveCharacterId = e.currentTarget.dataset.saveCharacterId
  await removeTask(saveCharacterId)
}

async function handleStartDay(e) {
  const saveId = e.currentTarget.dataset.saveId
  await startDay(saveId)
}

async function handleTestDay(e) {
  const saveId = e.currentTarget.dataset.saveId
  await testDay(saveId)
}

// Attach listeners safely (only once)
function attachListeners() {
  document.querySelectorAll('.set-resting-btn').forEach(btn => {
    btn.removeEventListener('click', handleSetResting)
    btn.addEventListener('click', handleSetResting)
  })

  document.querySelectorAll('.assign-task-btn').forEach(btn => {
    btn.removeEventListener('click', handleAssignTask)
    btn.addEventListener('click', handleAssignTask)
  })

  document.querySelectorAll('.remove-task-btn').forEach(btn => {
    btn.removeEventListener('click', handleRemoveTask)
    btn.addEventListener('click', handleRemoveTask)
  })

  const startBtn = document.getElementById('start-day-button')
  if (startBtn && !startBtn.dataset.listenerAttached) {
    // Your current code uses testDay, leaving as-is
    startBtn.addEventListener('click', handleTestDay)
    startBtn.dataset.listenerAttached = 'true'
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  attachListeners()
  updateRestingButtons()

  observeProgressBarChanges()

})
