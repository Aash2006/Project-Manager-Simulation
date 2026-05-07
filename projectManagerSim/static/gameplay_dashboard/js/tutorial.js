let isTyping = false;
let typeInterval = null;
let letterIndex = 0;
let currDialogue = "";
let currTutorialStep = 0;
let talkingImg = null;
let pausingImg = null;
let prevBtn = null;

const jerryContainer = document.getElementById('jerrySpeakerSlot');
const textContainer = document.getElementById('tutorialText');

const tutorialSteps = [
    {body : "Hello there! You're here to learn how to become a project manager aren't you?"},
    {body : "Welcome to the Project Manager Simulation game where you will learn how to manage your own projects at university in a fun and interactive way"},
    {body : "My name is Jerry by the way, I will be here to guide you on how to use this web app"},
    {body : "To start us off, please pick who your teammates will be for this project..."}
];

function jerryStartSpeak(dialogue) {
    if(prevBtn){ // Hides the prev button on the first slide
        if(currTutorialStep==0) {
            prevBtn.style.display = 'none';
    }
    else {
        prevBtn.style.display ='inline-block';
    }
    }
    console.log("Jerry said, " + dialogue + "") // can be removed later
    textContainer.innerHTML = ""
    isTyping = true; // Jerry is about to speak
    letterIndex = 0;
    currDialogue = dialogue;

typeInterval = setInterval(() => {
    if(letterIndex < dialogue.length){
        textContainer.innerHTML += dialogue.charAt(letterIndex);


        if (talkingImg && pausingImg) {
            if(letterIndex % 3 === 0) {
                talkingImg.style.display = 'block'; // open mouth shows on the first letter
                pausingImg.style.display = 'none'; // close mouth image doesn't show during this time
            }
            else if (letterIndex % 3 == 1)
            {
                talkingImg.style.display = 'none';
                pausingImg.style.display = 'block';
            }
        }
        letterIndex++;
    }
    else{
        clearInterval(typeInterval);
        isTyping = false;
        closeJerryMouth();
    }
}, 50);
}
function continueButton() {
    if(isTyping==true) {
        textContainer.innerHTML = currDialogue;
        clearInterval(typeInterval);
        isTyping = false;
        closeJerryMouth();
    }
    else {
        currTutorialStep++
        if(currTutorialStep<tutorialSteps.length){
            jerryStartSpeak(tutorialSteps[currTutorialStep].body); //say the next line
        }
        else{
            skipTutorial();
        }
        }
    }


function skipTutorial() {
    clearInterval(typeInterval);
    isTyping = false;
    closeJerryMouth();
    
    // Properly hide a Bootstrap modal so it removes the dark backdrop
    const tutorialModalEl = document.getElementById('tutorialModal');
    const modalInstance = bootstrap.Modal.getInstance(tutorialModalEl);
    if (modalInstance) {
        modalInstance.hide();
    } else {
        tutorialModalEl.style.display = 'none'; // Fallback
    }
}

function previousButton() {
    if(currTutorialStep>0){
        if(isTyping == true) {clearInterval(typeInterval); isTyping = false};
        currTutorialStep--;
        textContainer.innerHTML = currDialogue = tutorialSteps[currTutorialStep].body; // updates current dialogue and text container with what had been said previously

    if (prevBtn && currTutorialStep === 0) {
           prevBtn.style.display = 'none';
        }
    }
}

function closeJerryMouth() {

    if (talkingImg && pausingImg) {
        talkingImg.style.display = 'none';
        pausingImg.style.display = 'block';
    }
}

// Replace window.onload with this safer event listener
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('tutorialText')) {

        const tutorialModalEl = document.getElementById('tutorialModal');
        const modalInstance = new bootstrap.Modal(tutorialModalEl);
        modalInstance.show();


        prevBtn = document.getElementById('tutorialPreviousBtn');
        talkingImg = document.getElementById('jerryTalking');
        pausingImg = document.getElementById('jerryPausing');


        document.getElementById('tutorialContBtn').addEventListener('click', continueButton);
        document.getElementById('tutorialSkipBtn').addEventListener('click', skipTutorial);
        prevBtn.addEventListener('click', previousButton);

        // Start the dialogue
        jerryStartSpeak(tutorialSteps[currTutorialStep].body);
    }
});


