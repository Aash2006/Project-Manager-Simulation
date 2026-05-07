// Alert Modal
window.loadAlertModal = function(title, body) {
    document.getElementById("alertModalTitle").innerText = title;
    document.getElementById("alertModalBody").innerText = body;
    const modal = new bootstrap.Modal(document.getElementById("alertModal"));
    modal.show();
}

// Decision Modal cleanup
document.addEventListener("DOMContentLoaded", function() {
    const decisionModal = document.getElementById('decisionModal');
    if (decisionModal) {
        decisionModal.addEventListener('hidden.bs.modal', function() {
            document.querySelector('.modal-backdrop')?.remove();
            document.body.classList.remove('modal-open');
            document.body.style.removeProperty('padding-right');
        });
    }
});

// Load decision into modal
function loadDecisionModal(decisionId) {
    fetch(`/decisions/get_decision/?decision_id=${decisionId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById("decisionModalTitle").innerText = data.title;
            document.getElementById("decisionModalBody").innerText = data.body;

            const btn1 = document.getElementById("decisionModalOption1");
            const btn2 = document.getElementById("decisionModalOption2");

            document.getElementById("decisionModal").dataset.decisionId = data.decision_id;

            btn1.innerText = data.options[0].label;
            btn2.innerText = data.options[1].label;

            btn1.onclick = () => submitDecision(data.options[0].id);
            btn2.onclick = () => submitDecision(data.options[1].id);

            new bootstrap.Modal(document.getElementById("decisionModal")).show();
        });
}

// Submit decision
function submitDecision(optionId) {
    fetch(window.ENDPOINTS.processDecision, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": window.CSRF_TOKEN,
        },
        body: JSON.stringify({
            option_id: optionId,
            decision_id: document.getElementById("decisionModal").dataset.decisionId,
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error("Decision failed");
        } else {
            const modalEl = document.getElementById("decisionModal");
            bootstrap.Modal.getInstance(modalEl)?.hide();
            document.querySelector('.modal-backdrop')?.remove();
            document.body.classList.remove('modal-open');
            document.body.style.removeProperty('padding-right');
        }
    });
}