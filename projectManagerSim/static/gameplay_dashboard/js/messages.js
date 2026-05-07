// Load the raw data once from the json_script tag
const scriptTag = document.getElementById('decisions-data');
const ALL_DECISIONS = scriptTag ? (JSON.parse(scriptTag.textContent) || []) : [];

function closeAndResetWidget() {
    const menu = document.getElementById('messaging-menu');
    const chat = document.getElementById('chat-interface');
    const icon = document.getElementById('widget-icon');
    menu.classList.add('d-none');
    chat.classList.add('d-none');
    icon.innerHTML = '<i class="bi bi-chat-right-dots"></i>';
    const resDiv = document.getElementById('chat-responses');
    resDiv.innerHTML = '';
}

function toggleWidget() {
    const menu = document.getElementById('messaging-menu');
    const chat = document.getElementById('chat-interface');
    const icon = document.getElementById('widget-icon');

    if (!menu.classList.contains('d-none') || !chat.classList.contains('d-none')) {
        menu.classList.add('d-none');
        chat.classList.add('d-none');
        icon.innerHTML = '<i class="bi bi-chat-right-dots"></i>';
    } else {
        menu.classList.remove('d-none');
        icon.innerHTML = '<i class="bi bi-x"></i>';
    }
}

// Finds the specific decision in our JS object and populates the chat
function initiateChat(decisionId) {
    // 1. Grab the latest data directly from the script tag right now
    const scriptElement = document.getElementById('decisions-data');

    if (!scriptElement) {
        console.error("Could not find the decisions-data script tag.");
        return;
    }

    const currentDecisions = JSON.parse(scriptElement.textContent);

    // 2. Check if data exists
    if (!currentDecisions) {
        console.error("Decisions data is null or empty.");
        return;
    }

    console.log("Looking for ID:", decisionId, "within:", currentDecisions);

    // 3. Find the decision
    const decision = currentDecisions.find(d => d.id === decisionId);

    if (decision) {
        openChat(decision.id, decision.title, decision.body, decision.options);
    } else {
        console.error("Decision not found in the current data set.");
    }
}
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
async function typeMessage(element, text, speed = 25) {
    element.textContent = "";
    for (let i = 0; i < text.length; i++) {
        element.textContent += text.charAt(i);
        element.scrollTop = element.scrollHeight;
        await sleep(speed);
    }
}
async function openChat(id, title, body, options) {
    document.getElementById('messaging-menu').classList.add('d-none');
    document.getElementById('chat-interface').classList.remove('d-none');

    document.getElementById('chat-title').innerText = title;
    const resDiv = document.getElementById('chat-responses');
    resDiv.innerHTML = '';

    const text_body = document.getElementById('chat-body');
    await typeMessage(text_body, body, 20);
    await sleep(70);

    options.forEach(opt => {
        const btn = document.createElement('button');
        btn.className = 'btn btn-primary btn-sm rounded-pill px-3';
        btn.innerText = opt.text || opt.label; // Supports both 'text' or 'label' keys
        btn.onclick = () => submitDecision(id, opt.id);
        resDiv.appendChild(btn);
    });
}

function backToMenu() {
    document.getElementById('chat-interface').classList.add('d-none');
    document.getElementById('messaging-menu').classList.remove('d-none');
}

function submitDecision(decisionId, optionId) {
    // Reuse your existing fetch logic here
    fetch(window.ENDPOINTS.processDecision, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({
            option_id: optionId,
            decision_id: decisionId,
        }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Since we aren't using AJAX to refresh the list, 
                // a simple page reload or manually removing the element is best.
                window.location.href = window.location.href;
            }
        })
        .then(data => {
            toggleWidget();
        });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}