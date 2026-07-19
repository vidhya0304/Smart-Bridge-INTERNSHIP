const conceptInput = document.getElementById('conceptInput');
const complexityLevel = document.getElementById('complexityLevel');
const explainBtn = document.getElementById('explainBtn');
const explainerOutput = document.getElementById('explainerOutput');
const emptyState = document.getElementById('explainEmptyState');
const loadingOverlay = document.getElementById('explainLoadingOverlay');

const outConcept = document.getElementById('outConcept');
const outBadge = document.getElementById('outBadge');
const outExplanation = document.getElementById('outExplanation');
const outExamples = document.getElementById('outExamples');
const outAnalogies = document.getElementById('outAnalogies');

explainBtn.addEventListener('click', explainConcept);

function setConcept(val) {
    conceptInput.value = val;
    explainConcept();
}

async function explainConcept() {
    const concept = conceptInput.value.trim();
    if (!concept) return;
    
    // Show loading
    loadingOverlay.style.display = 'flex';
    emptyState.style.display = 'none';
    explainerOutput.style.display = 'none';
    
    try {
        const response = await fetch('/api/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                concept: concept,
                level: complexityLevel.value
            })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to explain concept');
        }
        
        const data = await response.json();
        
        // Render Output values
        outConcept.textContent = data.concept;
        outBadge.textContent = complexityLevel.value;
        outExplanation.textContent = data.explanation;
        
        // Examples list
        outExamples.innerHTML = '';
        if (data.examples && Array.isArray(data.examples)) {
            data.examples.forEach(ex => {
                const li = document.createElement('li');
                li.textContent = ex;
                outExamples.appendChild(li);
            });
        }
        
        // Analogies list
        outAnalogies.innerHTML = '';
        if (data.analogies && Array.isArray(data.analogies)) {
            data.analogies.forEach(an => {
                const li = document.createElement('li');
                li.textContent = an;
                outAnalogies.appendChild(li);
            });
        }
        
        // Switch views
        loadingOverlay.style.display = 'none';
        explainerOutput.style.display = 'block';
        
    } catch (err) {
        loadingOverlay.style.display = 'none';
        emptyState.style.display = 'block';
        alert(`Error explaining concept: ${err.message}`);
    }
}
