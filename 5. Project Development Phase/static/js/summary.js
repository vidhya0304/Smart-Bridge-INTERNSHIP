const textToSummarize = document.getElementById('textToSummarize');
const summaryLength = document.getElementById('summaryLength');
const summaryFormat = document.getElementById('summaryFormat');
const useLocalT5 = document.getElementById('summaryUseLocalT5');
const summarizeBtn = document.getElementById('summarizeBtn');

const emptyState = document.getElementById('summaryEmptyState');
const loadingOverlay = document.getElementById('summaryLoadingOverlay');
const summarizerOutput = document.getElementById('summarizerOutput');

const outSummary = document.getElementById('outSummary');
const outBulletPoints = document.getElementById('outBulletPoints');
const outKeywords = document.getElementById('outKeywords');

const inWordCount = document.getElementById('inWordCount');
const outWordCount = document.getElementById('outWordCount');

// Update input word counts on typing
textToSummarize.addEventListener('input', () => {
    const text = textToSummarize.value.trim();
    const count = text ? text.split(/\s+/).length : 0;
    inWordCount.textContent = count;
});

summarizeBtn.addEventListener('click', generateSummary);

async function generateSummary() {
    const text = textToSummarize.value.trim();
    if (!text) {
        alert('Please enter or paste some text to summarize.');
        return;
    }
    
    // Show loading
    loadingOverlay.style.display = 'flex';
    emptyState.style.display = 'none';
    summarizerOutput.style.display = 'none';
    
    try {
        const response = await fetch('/api/summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                length: summaryLength.value,
                format: summaryFormat.value,
                use_local: useLocalT5.checked
            })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to generate summary');
        }
        
        const data = await response.json();
        
        // Render values
        outSummary.textContent = data.summary;
        
        // Bullet points
        outBulletPoints.innerHTML = '';
        if (data.bullet_points && Array.isArray(data.bullet_points)) {
            data.bullet_points.forEach(bullet => {
                const li = document.createElement('li');
                li.textContent = bullet;
                outBulletPoints.appendChild(li);
            });
        }
        
        // Keywords tags
        outKeywords.innerHTML = '';
        if (data.keywords && Array.isArray(data.keywords)) {
            data.keywords.forEach(kw => {
                const tag = document.createElement('span');
                tag.className = 'keyword-tag';
                tag.textContent = kw;
                outKeywords.appendChild(tag);
            });
        }
        
        // Calculate output stats
        const outTextCombined = data.summary + ' ' + (data.bullet_points ? data.bullet_points.join(' ') : '');
        const count = outTextCombined.trim() ? outTextCombined.trim().split(/\s+/).length : 0;
        outWordCount.textContent = count;
        
        // Switch view states
        loadingOverlay.style.display = 'none';
        summarizerOutput.style.display = 'block';
        
    } catch (err) {
        loadingOverlay.style.display = 'none';
        emptyState.style.display = 'block';
        alert(`Error: ${err.message}`);
    }
}
