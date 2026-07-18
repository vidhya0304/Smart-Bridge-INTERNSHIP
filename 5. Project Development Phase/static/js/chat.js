const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');
const metricCount = document.getElementById('metricCount');
const charCount = document.getElementById('charCount');

let chatHistory = [];
let lastResponseRaw = null;

// Handle enter key to send
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);
clearChatBtn.addEventListener('click', clearHistory);

copyBtn.addEventListener('click', copyLastResponse);
downloadBtn.addEventListener('click', downloadLastResponse);

function useSuggestedTopic(topic) {
    chatInput.value = topic;
    chatInput.focus();
}

async function sendMessage() {
    const question = chatInput.value.trim();
    if (!question) return;
    
    // Disable inputs and show sending state
    chatInput.value = '';
    chatInput.disabled = true;
    sendBtn.disabled = true;
    
    // Append User Message
    appendMessage(question, 'user');
    
    // Add temporary loading indicator
    const loadingId = appendLoadingIndicator();
    
    try {
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                history: chatHistory
            })
        });
        
        // Remove loading indicator
        removeElement(loadingId);
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to fetch AI response');
        }
        
        const data = await response.json();
        lastResponseRaw = data;
        
        // Append structured AI message
        appendStructuredResponse(data);
        
        // Store in history
        chatHistory.push({ role: 'user', content: question });
        chatHistory.push({ role: 'assistant', content: JSON.stringify(data) });
        
        // Update stats
        updateStats();
        
        // Enable actions
        copyBtn.disabled = false;
        downloadBtn.disabled = false;
        
    } catch (error) {
        removeElement(loadingId);
        appendMessage(`Error: ${error.message}`, 'error');
    } finally {
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

function appendMessage(text, role) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message');
    
    if (role === 'user') {
        messageDiv.classList.add('message-user');
        messageDiv.textContent = text;
    } else if (role === 'error') {
        messageDiv.classList.add('message-assistant');
        messageDiv.style.borderLeft = '4px solid #ef4444';
        messageDiv.style.color = '#ef4444';
        messageDiv.textContent = text;
    } else {
        messageDiv.classList.add('message-assistant');
        messageDiv.textContent = text;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendStructuredResponse(data) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message', 'message-assistant');
    
    // Bullets list
    let pointsHtml = '';
    if (data.key_points && Array.isArray(data.key_points)) {
        pointsHtml = data.key_points.map(pt => `<li>${pt}</li>`).join('');
    }
    
    messageDiv.innerHTML = `
        <div class="ai-structured-response">
            <div class="response-block">
                <div class="response-block-title"><i class="fas fa-check-circle"></i> Direct Answer</div>
                <div>${data.answer}</div>
            </div>
            
            <div class="response-block">
                <div class="response-block-title"><i class="fas fa-circle-info"></i> Explanation</div>
                <div style="white-space: pre-wrap;">${data.explanation}</div>
            </div>
            
            <div class="response-block">
                <div class="response-block-title"><i class="fas fa-lightbulb"></i> Practical Example</div>
                <div>${data.example}</div>
            </div>
            
            <div class="response-block">
                <div class="response-block-title"><i class="fas fa-list-ul"></i> Key Takeaways</div>
                <ul style="padding-left: 1.25rem; margin-top: 0.25rem;">
                    ${pointsHtml}
                </ul>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendLoadingIndicator() {
    const id = 'loading_' + Date.now();
    const loadingDiv = document.createElement('div');
    loadingDiv.id = id;
    loadingDiv.classList.add('chat-message', 'message-assistant');
    loadingDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <div class="spinner" style="width: 20px; height: 20px; border-width: 3px;"></div>
            <span style="color: var(--text-muted); font-size: 0.9rem;">EduGenie is thinking...</span>
        </div>
    `;
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
}

function removeElement(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function clearHistory() {
    chatHistory = [];
    lastResponseRaw = null;
    chatMessages.innerHTML = `
        <div class="chat-message message-assistant">
            <p>Chat history cleared. What topic are we studying next?</p>
        </div>
    `;
    copyBtn.disabled = true;
    downloadBtn.disabled = true;
    updateStats();
}

function updateStats() {
    metricCount.textContent = chatHistory.length + 1;
    let chars = 0;
    if (lastResponseRaw) {
        chars += (lastResponseRaw.answer?.length || 0) + 
                 (lastResponseRaw.explanation?.length || 0) + 
                 (lastResponseRaw.example?.length || 0);
    }
    charCount.textContent = chars;
}

function copyLastResponse() {
    if (!lastResponseRaw) return;
    const textToCopy = `
DIRECT ANSWER:
${lastResponseRaw.answer}

DETAILED EXPLANATION:
${lastResponseRaw.explanation}

PRACTICAL EXAMPLE:
${lastResponseRaw.example}

KEY TAKEAWAYS:
${lastResponseRaw.key_points ? lastResponseRaw.key_points.join('\n') : ''}
`.trim();

    navigator.clipboard.writeText(textToCopy)
        .then(() => alert('Copied last structured response to clipboard!'))
        .catch(err => alert('Failed to copy: ' + err));
}

function downloadLastResponse() {
    if (!lastResponseRaw) return;
    const fileContent = `
# EduGenie Study Session Notes

## Direct Answer
${lastResponseRaw.answer}

## Detailed Explanation
${lastResponseRaw.explanation}

## Practical Example
${lastResponseRaw.example}

## Key Takeaways
${lastResponseRaw.key_points ? lastResponseRaw.key_points.map(p => `- ${p}`).join('\n') : ''}

---
Session notes generated on ${new Date().toLocaleDateString()} by EduGenie AI Assistant.
`.trim();

    const blob = new Blob([fileContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `edugenie_notes_${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
