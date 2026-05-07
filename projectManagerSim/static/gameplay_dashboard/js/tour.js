function getTourStep() {
    return document.body.dataset.tourStep;
}


// Global function to restart the tour from anywhere
function restartTour() {
    // Navigate to dashboard with tour trigger if player is not already there
    if (!window.location.pathname.includes('/game/dashboard/')) {
        window.location.href = '/game/dashboard/?new_game=true';
    } else {
        // Already on dashboard, start tour
        startDashboardTour(true);
    }
}

// Jerry speaking state for tour
let tourIsTyping = false;
let tourTypeInterval = null;
let tourLetterIndex = 0;
let tourCurrDialogue = "";
let tourCurrentStepElement = null;

function createJerryHTML(text = '') {
    return `
          <div class="tour-jerry-container" style="display: flex; flex-direction: row; align-items: center; gap: 20px; min-width: 400px;">
              <div class="tour-jerry-speaker" style="flex-shrink: 0; width: 120px;">
                  <img src="/static/images/jerry_talking.png" class="tour-jerry-sprite tour-jerry-talking" alt="Jerry is talking" style="display: none; width: 120px !important; max-width: 120px !important; height: auto !important;">
                  <img src="/static/images/jerry_pausing.png" class="tour-jerry-sprite tour-jerry-pausing" alt="Jerry's mouth's closed" style="width: 120px !important; max-width: 120px !important; height: auto !important;">
              </div>
              <div class="tour-jerry-text" style="flex-grow: 1; font-family: 'Courier New', Courier, monospace; font-size: 1.1rem; min-height: 60px; line-height: 1.4;"></div>
          </div>
      `;
}

function tourJerrySpeak(dialogue, stepElement) {
    const container = stepElement.querySelector('.tour-jerry-container');
    if (!container) return;

    // Store current step element for later use
    tourCurrentStepElement = stepElement;

    const textContainer = container.querySelector('.tour-jerry-text');
    const talkingImg = container.querySelector('.tour-jerry-talking');
    const pausingImg = container.querySelector('.tour-jerry-pausing');

    if (!textContainer) return;

    textContainer.innerHTML = "";
    tourIsTyping = true;
    tourLetterIndex = 0;
    tourCurrDialogue = dialogue;

    // Clear any existing interval
    if (tourTypeInterval) {
        clearInterval(tourTypeInterval);
    }

    tourTypeInterval = setInterval(() => {
        if (tourLetterIndex < dialogue.length) {
            textContainer.innerHTML += dialogue.charAt(tourLetterIndex);

            if (talkingImg && pausingImg) {
                if (tourLetterIndex % 3 === 0) {
                    talkingImg.style.display = 'block';
                    pausingImg.style.display = 'none';
                } else if (tourLetterIndex % 3 === 1) {
                    talkingImg.style.display = 'none';
                    pausingImg.style.display = 'block';
                }
            }
            tourLetterIndex++;
        } else {
            clearInterval(tourTypeInterval);
            tourTypeInterval = null;
            tourIsTyping = false;
            // Close mouth
            if (talkingImg && pausingImg) {
                talkingImg.style.display = 'none';
                pausingImg.style.display = 'block';
            }
        }
    }, 50);
}

function tourCompleteTyping() {
    // Complete the typing animation
    if (tourCurrentStepElement) {
        const textContainer = tourCurrentStepElement.querySelector('.tour-jerry-text');
        const talkingImg = tourCurrentStepElement.querySelector('.tour-jerry-talking');
        const pausingImg = tourCurrentStepElement.querySelector('.tour-jerry-pausing');

        if (textContainer) {
            textContainer.innerHTML = tourCurrDialogue;
        }
        if (talkingImg && pausingImg) {
            talkingImg.style.display = 'none';
            pausingImg.style.display = 'block';
        }
    }
    if (tourTypeInterval) {
        clearInterval(tourTypeInterval);
        tourTypeInterval = null;
    }
    tourIsTyping = false;
}

function initJerryForStep(tour, stepText) {
    setTimeout(() => {
        const currentStep = tour.currentStep;
        if (currentStep && currentStep.el) {
            tourJerrySpeak(stepText, currentStep.el);
        }
    }, 100);
}

function createJerryButtons(tour, options = {}) {
    const { showPrev = true, nextText = 'Continue', onNext = null, isLast = false, skipText = 'Skip Tutorial' } = options;

    const buttons = [];

    
    buttons.push({
        text: skipText,
        secondary: true,
        classes: 'shepherd-button-secondary tour-skip-btn',
        action: function () {
            tourCompleteTyping();
            tour.cancel();
        }
    });

    
    if (showPrev) {
        buttons.push({
            text: 'Previous',
            secondary: true,
            classes: 'shepherd-button-secondary tour-prev-btn',
            action: function () {
                tourCompleteTyping();
                tour.back();
            }
        });
    }

    buttons.push({
        text: nextText,
        classes: 'shepherd-button-primary tour-continue-btn',
        action: function () {
            if (tourIsTyping) {
                tourCompleteTyping();
                return;
            }
            if (onNext) {
                onNext();
            } else if (isLast) {
                tour.complete();
            } else {
                tour.next();
            }
        }
    });

    return buttons;
}

function showTourPrompt() {
    
    fetch('/tour/complete/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': window.CSRF_TOKEN,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ next_step: 'dashboard' })
    }).then(() => {
        startDashboardTour(true); //show intro message
    });
}

function startDashboardTour(showIntro = false) {
    const tour = new Shepherd.Tour({
        useModalOverlay: true,
        defaultStepOptions: {
            cancelIcon: { enabled: true },
            scrollTo: true,
            classes: 'shepherd-theme-arrows shepherd-jerry',
        }
    });

    if (showIntro) {
        const introText = "Here's a small tour of the game and how things work here.";
        tour.addStep({
            id: 'jerry-intro',
            text: createJerryHTML(),
            buttons: createJerryButtons(tour, { showPrev: false }),
            when: {
                show: () => initJerryForStep(tour, introText)
            }
        });
    }

    const welcomeText = "Welcome to Project Manager Simulator! Let me show you around the dashboard.";
    tour.addStep({
        id: 'welcome',
        text: createJerryHTML(),
        buttons: createJerryButtons(tour, { showPrev: showIntro }),
        when: {
            show: () => initJerryForStep(tour, welcomeText)
        }
    });

    const progressText = "This is your project progress bar. Get it to 100% before the deadline!";
    tour.addStep({
        id: 'progress',
        text: createJerryHTML(),
        attachTo: { element: '.progresscard-progress', on: 'bottom' },
        buttons: createJerryButtons(tour),
        when: {
            show: () => initJerryForStep(tour, progressText)
        }
    });

    const startDayText = "Click Start Day to advance time and see the results of your decisions.";
    tour.addStep({
        id: 'start-day',
        text: createJerryHTML(),
        attachTo: { element: '#start-day-button', on: 'top' },
        buttons: createJerryButtons(tour),
        when: {
            show: () => initJerryForStep(tour, startDayText)
        }
    });

    const attentionText = "This panel shows anything that needs your attention: low energy teammates, unassigned workers and fully rested characters ready to work.";
    tour.addStep({
        id: 'requires-attention',
        text: createJerryHTML(),
        attachTo: { element: '.col-12.col-md-8.w-100', on: 'bottom' },
        buttons: createJerryButtons(tour),
        when: {
            show: () => initJerryForStep(tour, attentionText)
        }
    });

    const teammatesText = "Visit Teammates to manage your team, assign tasks and set rest days.";
    tour.addStep({
        id: 'navbar-teammates',
        text: createJerryHTML(),
        attachTo: { element: 'a[href*="teammates"]', on: 'bottom' },
        buttons: createJerryButtons(tour),
        when: {
            show: () => initJerryForStep(tour, teammatesText)
        }
    });

    const tasksText = "Visit Tasks to see what needs to be done and assign work to your team.";
    tour.addStep({
        id: 'navbar-tasks',
        text: createJerryHTML(),
        attachTo: { element: 'a[href*="tasks"]', on: 'bottom' },
        buttons: createJerryButtons(tour),
        when: {
            show: () => initJerryForStep(tour, tasksText)
        }
    });

    const relationshipsText = "Visit Relationships to see how your team members get along. Good chemistry boosts productivity!";
    tour.addStep({
        id: 'navbar-relationships',
        text: createJerryHTML(),
        attachTo: { element: 'a[href*="relationships"]', on: 'bottom' },
        buttons: createJerryButtons(tour),
        when: {
            show: () => initJerryForStep(tour, relationshipsText)
        }
    });

    const messagesText = "This is your messages widget. Decision events will appear here, make sure to respond to them!";
    tour.addStep({
        id: 'messages',
        text: createJerryHTML(),
        attachTo: { element: '.btn.btn-outline-primary.shadow-lg.rounded-circle.d-flex.align-items-center.justify-content-center.position-relative', on: 'top' },
        buttons: createJerryButtons(tour, { nextText: "Next: Teammates →", isLast: true }),
        when: {
            show: () => initJerryForStep(tour, messagesText)
        }
    });

    tour.on('complete', () => completeTourStep('characters', '/game/teammates/?tour=true'));
    tour.on('cancel', () => cancelTour());
    tour.start();
}

function startCharactersTour() {
    const tour = new Shepherd.Tour({
        useModalOverlay: true,
        defaultStepOptions: {
            cancelIcon: { enabled: true },
            scrollTo: true,
            classes: 'shepherd-theme-arrows shepherd-jerry',
        }
    });

    const welcomeText = "This is your Teammates page. Here you can see everyone on your team and manage them.";
    tour.addStep({
        id: 'characters-welcome',
        text: createJerryHTML(),
        buttons: createJerryButtons(tour, { showPrev: false }),
        when: {
            show: () => initJerryForStep(tour, welcomeText)
        }
    });

    const cardText = "Each card represents a team member. You can see their energy, happiness, and current task.";
    tour.addStep({
        id: 'character-card',
        text: createJerryHTML(),
        attachTo: { element: '.character-card', on: 'right' },
        buttons: createJerryButtons(tour),
        when: {
            show: () => initJerryForStep(tour, cardText)
        }
    });

    const energyText = "Energy determines how much work a character can do. If it drops too low they will defer tasks and lose happiness.";
    tour.addStep({
        id: 'character-energy',
        text: createJerryHTML(),
        attachTo: { element: '.character-card', on: 'right' },
        buttons: createJerryButtons(tour),
        when: {
            show: () => initJerryForStep(tour, energyText)
        }
    });

    const happinessText = "Happiness affects productivity. Overworked or idle characters become unhappy — balance work and rest!";
    tour.addStep({
        id: 'character-happiness',
        text: createJerryHTML(),
        attachTo: { element: '.character-card', on: 'right' },
        buttons: createJerryButtons(tour),
        when: {
            show: () => initJerryForStep(tour, happinessText)
        }
    });

    const restText = "Click Rest to let a character recover energy. Resting characters cannot work on that day.";
    tour.addStep({
        id: 'character-rest',
        text: createJerryHTML(),
        attachTo: { element: '.character-card', on: 'bottom' },
        buttons: createJerryButtons(tour),
        when: {
            show: () => initJerryForStep(tour, restText)
        }
    });

    const infoText = "Click Info to see a character's full stats, traits, and relationships with teammates.";
    tour.addStep({
        id: 'character-info',
        text: createJerryHTML(),
        attachTo: { element: '.info-btn', on: 'top' },
        buttons: createJerryButtons(tour, { nextText: "Next: Tasks →", isLast: true }),
        when: {
            show: () => initJerryForStep(tour, infoText)
        }
    });

    tour.on('complete', () => completeTourStep('tasks', '/game/tasks/?tour=true'));
    tour.on('cancel', () => cancelTour());
    tour.start();
}

function startTasksTour() {
    const tour = new Shepherd.Tour({
        useModalOverlay: true,
        defaultStepOptions: {
            cancelIcon: { enabled: true },
            scrollTo: true,
            classes: 'shepherd-theme-arrows shepherd-jerry',
        }
    });

    const welcomeText = "This is the Tasks page. Every task needs to be completed for the project to succeed.";
    tour.addStep({
        id: 'tasks-welcome',
        text: createJerryHTML(),
        buttons: createJerryButtons(tour, { showPrev: false }),
        when: {
            show: () => initJerryForStep(tour, welcomeText)
        }
    });

    const backlogText = "The Task Backlog shows all unassigned tasks. Assign teammates to tasks to make progress.";
    tour.addStep({
        id: 'task-backlog',
        text: createJerryHTML(),
        attachTo: { element: 'div.overflow-auto:nth-child(5)', on: 'right' },
        buttons: createJerryButtons(tour),
        when: {
            show: () => initJerryForStep(tour, backlogText)
        }
    });

    const assignText = "Click a task to select it, then use the Assign dropdown to assign a teammate to it.";
    tour.addStep({
        id: 'task-assign',
        text: createJerryHTML(),
        attachTo: { element: '#task-asign-menu', on: 'top' },
        buttons: createJerryButtons(tour),
        when: {
            show: () => initJerryForStep(tour, assignText)
        }
    });

    const detailsText = "Each task shows how many people are required and how long it takes to complete.";
    tour.addStep({
        id: 'task-details',
        text: createJerryHTML(),
        attachTo: { element: '#task-requirement', on: 'right' },
        buttons: createJerryButtons(tour, { nextText: "Next: Relationships →", isLast: true }),
        when: {
            show: () => initJerryForStep(tour, detailsText)
        }
    });

    tour.on('complete', () => completeTourStep('relationships', `/game/relationships/${window.SAVE_ID}/?tour=true`));
    tour.on('cancel', () => cancelTour());
    tour.start();
}

function startRelationshipsTour() {
    const tour = new Shepherd.Tour({
        useModalOverlay: true,
        defaultStepOptions: {
            cancelIcon: { enabled: true },
            scrollTo: true,
            classes: 'shepherd-theme-arrows shepherd-jerry',
        }
    });

    const welcomeText = "This is the Relationships page. Team chemistry has a real impact on productivity.";
    tour.addStep({
        id: 'relationships-welcome',
        text: createJerryHTML(),
        buttons: createJerryButtons(tour, { showPrev: false }),
        when: {
            show: () => initJerryForStep(tour, welcomeText)
        }
    });

    const detailText = "Characters who are friends or best friends work better together. Rivals and tensions drain energy faster.";
    tour.addStep({
        id: 'relationships-detail',
        text: createJerryHTML(),
        buttons: createJerryButtons(tour),
        when: {
            show: () => initJerryForStep(tour, detailText)
        }
    });

    const tipText = "Try to assign tasks to characters who get along well — it makes a big difference to your project outcome!";
    tour.addStep({
        id: 'relationships-tip',
        text: createJerryHTML(),
        buttons: createJerryButtons(tour, { nextText: "Next: Settings →", isLast: true }),
        when: {
            show: () => initJerryForStep(tour, tipText)
        }
    });

    tour.on('complete', () => completeTourStep('settings', '/settings/?tour=true'));
    tour.on('cancel', () => cancelTour());
    tour.start();
}

function startSettingsTour() {
    const tour = new Shepherd.Tour({
        useModalOverlay: true,
        defaultStepOptions: {
            cancelIcon: { enabled: true },
            scrollTo: true,
            classes: 'shepherd-theme-arrows shepherd-jerry',
        }
    });

    const welcomeText = "This is your Settings page where you can update your password and email.";
    tour.addStep({
        id: 'settings-welcome',
        text: createJerryHTML(),
        buttons: createJerryButtons(tour, { showPrev: false }),
        when: {
            show: () => initJerryForStep(tour, welcomeText)
        }
    });

    const passwordText = "Use this form to change your password at any time.";
    tour.addStep({
        id: 'settings-password',
        text: createJerryHTML(),
        attachTo: { element: '.card', on: 'right' },
        buttons: createJerryButtons(tour),
        when: {
            show: () => initJerryForStep(tour, passwordText)
        }
    });

    const completeText = "That's the full tour! You're ready to manage your project. Good luck, ensure your team is happy and energised!";
    tour.addStep({
        id: 'tour-complete',
        text: createJerryHTML(),
        buttons: createJerryButtons(tour, { nextText: "Let's play!", isLast: true }),
        when: {
            show: () => initJerryForStep(tour, completeText)
        }
    });

    tour.on('complete', () => completeTourStep(null, '/game/dashboard/'));
    tour.on('cancel', () => cancelTour());
    tour.start();
}

function completeTourStep(nextStep, redirectUrl) {
    fetch('/tour/complete/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': window.CSRF_TOKEN,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ next_step: nextStep })
    }).then(() => {
        window.location.href = redirectUrl;
    });
}

function cancelTour() {
    fetch('/tour/complete/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': window.CSRF_TOKEN,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ next_step: null })
    });
}

// Auto-start based on page
document.addEventListener('DOMContentLoaded', () => {
    const step = document.body.dataset.tourStep;
    if (step === 'prompt') showTourPrompt();
    else if (step === 'dashboard') startDashboardTour();
    else if (step === 'characters') startCharactersTour();
    else if (step === 'tasks') startTasksTour();
    else if (step === 'relationships') startRelationshipsTour();
    else if (step === 'settings') startSettingsTour();
});