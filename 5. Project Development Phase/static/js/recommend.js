const subjectInput = document.getElementById('subjectInput');
const learnerLevel = document.getElementById('learnerLevel');
const recommendBtn = document.getElementById('recommendBtn');

const emptyState = document.getElementById('recommendEmptyState');
const loadingOverlay = document.getElementById('recommendLoadingOverlay');
const recommendationsOutput = document.getElementById('recommendationsOutput');

const outSubject = document.getElementById('outSubject');
const outLevelBadge = document.getElementById('outLevelBadge');
const resourcesGrid = document.getElementById('resourcesGrid');
const roadmapTimeline = document.getElementById('roadmapTimeline');

recommendBtn.addEventListener('click', generateRecommendations);

function setSubject(subject) {
    subjectInput.value = subject;
    generateRecommendations();
}

async function generateRecommendations() {
    const subject = subjectInput.value.trim();
    if (!subject) return;
    
    // Show loading
    loadingOverlay.style.display = 'flex';
    emptyState.style.display = 'none';
    recommendationsOutput.style.display = 'none';
    
    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic: subject,
                level: learnerLevel.value
            })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to generate recommendations');
        }
        
        const data = await response.json();
        
        // Render headers
        outSubject.textContent = data.topic;
        outLevelBadge.textContent = data.level;
        
        // Render resources grid
        resourcesGrid.innerHTML = '';
        if (data.resources && Array.isArray(data.resources)) {
            data.resources.forEach(res => {
                const card = document.createElement('div');
                card.className = 'glass-panel';
                card.style.padding = '1.5rem';
                card.style.display = 'flex';
                card.style.flexDirection = 'column';
                
                const typeClass = res.type.toLowerCase() === 'book' ? 'badge-book' : 
                                  (res.type.toLowerCase() === 'course' ? 'badge-course' : 'badge-practice');
                
                card.innerHTML = `
                    <span class="resource-type-badge ${typeClass}">${res.type}</span>
                    <h5 style="font-size: 1.05rem; font-weight: 700; margin-bottom: 0.5rem; flex-grow: 1;">${res.title}</h5>
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1rem;">
                        <i class="fas fa-hourglass-half"></i> Est: ${res.time_estimate}
                    </div>
                    <a href="${res.url.startsWith('http') ? res.url : 'https://www.google.com/search?q=' + encodeURIComponent(res.url)}" 
                       target="_blank" 
                       class="btn btn-secondary btn-sm" 
                       style="font-size: 0.8rem; padding: 0.4rem; justify-content: center; width: 100%;">
                       Access Material <i class="fas fa-up-right-from-square"></i>
                    </a>
                `;
                resourcesGrid.appendChild(card);
            });
        }
        
        // Render roadmap timeline
        roadmapTimeline.innerHTML = '';
        if (data.roadmap && Array.isArray(data.roadmap)) {
            // Sort by step number
            const sortedRoadmap = data.roadmap.sort((a, b) => a.step_number - b.step_number);
            sortedRoadmap.forEach(step => {
                const item = document.createElement('div');
                item.className = 'roadmap-item';
                
                item.innerHTML = `
                    <div class="roadmap-badge">${step.step_number}</div>
                    <div class="roadmap-body">
                        <div class="flex-row-between" style="margin-bottom: 0.5rem;">
                            <h5 style="font-size: 1.1rem; font-weight: 700;">${step.title}</h5>
                            <span style="font-size: 0.8rem; padding: 0.15rem 0.5rem; border-radius: 4px; background-color: var(--primary-light); color: var(--primary); font-weight: 600;">
                                ${step.estimated_hours} hrs
                            </span>
                        </div>
                        <p style="font-size: 0.9rem; color: var(--text-muted);">${step.description}</p>
                    </div>
                `;
                roadmapTimeline.appendChild(item);
            });
        }
        
        // Switch view states
        loadingOverlay.style.display = 'none';
        recommendationsOutput.style.display = 'block';
        
    } catch (err) {
        loadingOverlay.style.display = 'none';
        emptyState.style.display = 'block';
        alert(`Error mapping learning roadmap: ${err.message}`);
    }
}
