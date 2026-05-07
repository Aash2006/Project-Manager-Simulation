let selectedCharacters = new Set();
const MAX_SELECTION = 4;

function getCSRFToken(){
  return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

document.querySelectorAll('.character-checkbox').forEach(checkbox=>{
  checkbox.addEventListener('change',function(){
  const charId=parseInt(this.value);
  const card=this.closest('.character-card');

  if(this.checked){

    if(selectedCharacters.size>=MAX_SELECTION){
      this.checked=false;
      showError('You can only select 4 characters!');
      return;
    }

  selectedCharacters.add(charId);
  card.classList.add('selected');
  }

  else{
    selectedCharacters.delete(charId);
    card.classList.remove('selected');
  }

  updateSelectionUI();

  });
});

function updateSelectionUI(){
  document.getElementById('selected-count').textContent=
  selectedCharacters.size;

  const confirmBtn=document.getElementById('confirm-team');

  confirmBtn.disabled=
  selectedCharacters.size!==MAX_SELECTION;

  if(selectedCharacters.size===MAX_SELECTION){
    showChemistryPreview();
  }
  else{
  document.getElementById('chemistry-preview').style.display='none';
  }
}

function toggleRelationships(charId){
  const relList=document.getElementById(`relationships-${charId}`);
  const button=relList.previousElementSibling;

  if(relList.style.display==='none'){
    relList.style.display='block';
    button.textContent='Hide Relationships ▲';
  }
  else{
    relList.style.display='none';
    button.textContent='View Relationships ▼';
  }
}

async function showChemistryPreview(){
  
  
  const chemistryPreview = document.getElementById('chemistry-preview');
  const chemistryContent = document.getElementById('chemistry-content');
  

  
  chemistryPreview.style.display = 'block';
  
  // Show loading state
  chemistryContent.innerHTML = `
    <p class="analyzing">
      <span class="spinner-border spinner-border-sm me-2"></span>
      Analyzing team chemistry...
    </p>
  `;
  
  try {
    // Fetch chemistry analysis from your new endpoint
    const selectedArray = Array.from(selectedCharacters);
    
    const response = await fetch('/api/preview-chemistry/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      body: JSON.stringify({
        selected_characters: selectedArray
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      displayChemistry(data.team_chemistry);
    } else {
      chemistryContent.innerHTML = `<p class="text-danger">Failed to analyze chemistry</p>`;
    }
    
  } catch (error) {
    console.error('Chemistry preview error:', error);
    chemistryContent.innerHTML = `<p class="text-danger">Error analyzing chemistry</p>`;
  }
}

document.getElementById('confirm-team')
.addEventListener('click',async function(){

const selectedArray=Array.from(selectedCharacters);
const button=this;

button.disabled=true;
button.textContent='Creating your team...';

try{

  const response=await fetch(window.location.href,{
  method:'POST',
  headers:{
    'Content-Type':'application/json',
    'X-CSRFToken':getCSRFToken()
  },
  body:JSON.stringify({
  selected_characters:selectedArray
})
});

  const data=await response.json();

  if(data.success){
    // Display chemistry analysis
    displayChemistry(data.team_chemistry);
    
    // Change button text
    button.textContent='Team Created! Redirecting...';

    // Clear old bug bar values so new game starts fresh
    Object.keys(localStorage)
        .filter(k => k.startsWith('bug_percent_'))
        .forEach(k => localStorage.removeItem(k));
    
    // Wait 2.5 seconds so user can see chemistry
    setTimeout(() => {
      window.location.href = data.redirect_url;
    }, 2500);
  }


  else{
    alert(`Error: ${data.error}`);
    button.disabled=false;
    button.textContent='Confirm Team & Start Game';
  }
}
catch(error){
  console.error(error);
  alert('Failed to create team.');

  button.disabled=false;
  button.textContent='Confirm Team & Start Game';

  }

});


function showError(message) {
  const toast = document.createElement('div');
  toast.className = 'alert alert-warning alert-dismissible fade show';
  toast.style.position = 'fixed';
  toast.style.top = '20px';
  toast.style.right = '20px';
  toast.style.zIndex = '9999';
  toast.style.minWidth = '300px';
  toast.innerHTML = `
    <strong>⚠️ Selection Limit</strong><br>
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  
  document.body.appendChild(toast);
  
  // Auto-remove after 3 seconds
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function displayChemistry(chemistry) {
  const content = document.getElementById('chemistry-content');
  
  // Determine chemistry color and icon
  switch(chemistry.level) {
    case 'excellent':
      chemColor = '#22c55e'; // Green
      break;
    case 'good':
      chemColor = '#3b82f6'; // Blue
      break;
    case 'mixed':
      chemColor = '#f59e0b'; // Orange
      break;
    case 'poor':
      chemColor = '#ef4444'; // Red
      break;
    case 'volatile':
      chemColor = '#dc2626'; // Dark Red
      break;
    default:
      chemColor = '#6b7280'; // Gray
  }
  
  let html = `
    <div style="padding: 20px; background: linear-gradient(135deg, ${chemColor}15 0%, ${chemColor}05 100%); border-radius: 12px; border: 2px solid ${chemColor}40;">
      
      <!-- Header -->
      <div style="text-align: center; margin-bottom: 15px;">
        <div style="font-size: 2rem; font-weight: bold; color: ${chemColor}; margin-bottom: 10px;">
        </div>
        <p style="margin: 0; font-size: 1.1rem; font-style: italic; color: #64748b;">
          ${chemistry.message}
        </p>
      </div>
      
      <!-- Relationships -->
      <div style="margin-top: 15px;">
  `;
  
  // Best Friends
  if (chemistry.best_friends && chemistry.best_friends.length > 0) {
    html += `
      <div style="margin: 8px 0; padding: 10px; background: #dcfce7; border-radius: 8px; border-left: 4px solid #22c55e;">
        <strong style="color: #166534;">💚 Best Friends:</strong>
        <div style="margin-top: 5px; color: #15803d;">
          ${chemistry.best_friends.join('<br>')}
        </div>
      </div>
    `;
  }
  
  // Friends
  if (chemistry.friends && chemistry.friends.length > 0) {
    html += `
      <div style="margin: 8px 0; padding: 10px; background: #dbeafe; border-radius: 8px; border-left: 4px solid #3b82f6;">
        <strong style="color: #1e40af;">🤝 Friends:</strong>
        <div style="margin-top: 5px; color: #1e3a8a;">
          ${chemistry.friends.join('<br>')}
        </div>
      </div>
    `;
  }
  
  // Tensions
  if (chemistry.tensions && chemistry.tensions.length > 0) {
    html += `
      <div style="margin: 8px 0; padding: 10px; background: #fed7aa; border-radius: 8px; border-left: 4px solid #f97316;">
        <strong style="color: #9a3412;">😬 Tensions:</strong>
        <div style="margin-top: 5px; color: #9a3412;">
          ${chemistry.tensions.join('<br>')}
        </div>
      </div>
    `;
  }
  
  // Rivalries
  if (chemistry.rivalries && chemistry.rivalries.length > 0) {
    html += `
      <div style="margin: 8px 0; padding: 10px; background: #fecaca; border-radius: 8px; border-left: 4px solid #ef4444;">
        <strong style="color: #991b1b;">⚡ Rivalries:</strong>
        <div style="margin-top: 5px; color: #991b1b;">
          ${chemistry.rivalries.join('<br>')}
        </div>
      </div>
    `;
  }
  
  html += `
      </div>
    </div>
  `;
  
  content.innerHTML = html;
}