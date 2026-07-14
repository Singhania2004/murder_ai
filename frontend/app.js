// Game state
let gameState = null;
let gameComplete = false;
let ws = null;
let isConnected = false;
let selectedSuspectId = null;
let selectedClueId = null;

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const actionSelect = document.getElementById('action-select');
const sendBtn = document.getElementById('send-btn');
const startBtn = document.getElementById('start-btn');
const resetBtn = document.getElementById('reset-btn');
const statusText = document.getElementById('status-text');
const caseTitle = document.getElementById('case-title');
const caseStatus = document.getElementById('case-status');
const accusationCount = document.getElementById('accusation-count');
const suspectsList = document.getElementById('suspects-list');
const evidenceList = document.getElementById('evidence-list');
const notes = document.getElementById('notes');

// WebSocket connection
function connectWebSocket() {
    const wsUrl = `ws://localhost:8000/ws/client_${Date.now()}`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        isConnected = true;
        statusText.textContent = 'Ready';
        statusText.style.color = '#4caf50';
        sendBtn.disabled = false;
        showHowToPlay();
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };

    ws.onclose = () => {
        isConnected = false;
        statusText.textContent = 'Disconnected';
        statusText.style.color = '#ef5350';
        sendBtn.disabled = true;
        addMessage('error', 'Disconnected from server. Please refresh the page.');
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        addMessage('error', 'WebSocket error occurred.');
    };
}

// Show How to Play
function showHowToPlay() {
    chatMessages.innerHTML = `
        <div class="message system">
            <div class="how-to-play">
                <h3>🔍 Welcome to AI Murder Mystery!</h3>
                <p style="color: #aaa; margin-bottom: 12px;">A detective game where you interrogate AI suspects to solve a murder.</p>
                <ul>
                    <li><strong>🎮 Start Game</strong> - Begin a new murder case</li>
                    <li><strong>🔍 Interrogate</strong> - Click a suspect, then ask questions</li>
                    <li><strong>🔎 Search for Evidence</strong> - Explore the crime scene to find clues</li>
                    <li><strong>🔬 Analyze Evidence</strong> - Click on evidence to get forensic analysis</li>
                    <li><strong>💡 Get Hint</strong> - Ask the Game Master for a subtle clue</li>
                    <li><strong>⚖️ Accuse</strong> - When ready, accuse someone of the murder</li>
                    <li><strong>📝 Notes</strong> - Take notes to track your investigation</li>
                </ul>
                <p style="color: #888; margin-top: 10px; font-size: 13px;">Click <strong style="color: #e94560;">Start Game</strong> to begin your investigation!</p>
            </div>
        </div>
    `;
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    console.log('WebSocket message:', data);

    switch (data.type) {
        case 'game_started':
            gameState = data.game_state;
            gameComplete = false;
            selectedSuspectId = null;
            selectedClueId = null;
            updateUI();
            chatMessages.innerHTML = '';
            addMessage('game-master', data.response);
            statusText.textContent = 'Investigating';
            statusText.style.color = '#ffd54f';
            break;

        case 'action_result':
            gameState = data.game_state;
            gameComplete = data.game_complete || false;
            updateUI();
            
            if (gameComplete) {
                const isCorrect = data.correct;
                if (isCorrect) {
                    const cleanResponse = extractVerdictInfo(data.response, true);
                    addMessage('verdict-win', cleanResponse);
                    statusText.textContent = '✅ Solved!';
                    statusText.style.color = '#4caf50';
                } else {
                    const cleanResponse = extractVerdictInfo(data.response, false);
                    addMessage('verdict-lose', cleanResponse);
                    statusText.textContent = '❌ Case Closed';
                    statusText.style.color = '#ef5350';
                }
            } else {
                addMessage('system', data.response);
            }
            break;

        case 'discover_result':
            gameState = data.game_state;
            updateUI();
            addMessage('system', data.response);
            if (data.new_clues && data.new_clues.length > 0) {
                const clueNames = data.new_clues.map(c => c.description).join(', ');
                addMessage('system', `🔎 New evidence discovered: ${clueNames}`);
            }
            break;

        case 'state':
            gameState = data.game_state;
            updateUI();
            break;

        case 'reset':
            gameState = null;
            gameComplete = false;
            selectedSuspectId = null;
            selectedClueId = null;
            showHowToPlay();
            statusText.textContent = 'Ready';
            statusText.style.color = '#4caf50';
            break;

        case 'error':
            addMessage('error', `❌ ${data.message}`);
            break;

        default:
            console.log('Unknown message type:', data.type);
    }
}

// Extract clean verdict info
function extractVerdictInfo(response, isCorrect) {
    const lines = response.split('\n');
    let killer = '';
    let motive = '';
    let details = [];
    
    for (let line of lines) {
        if (line.includes('KILLER:') || line.includes('killer was') || line.includes('TRUE KILLER:')) {
            killer = line.replace(/[Kk]iller:|TRUE KILLER:/g, '').trim();
        }
        if (line.includes('MOTIVE:') || line.includes('motive was')) {
            motive = line.replace(/[Mm]otive:/g, '').trim();
        }
        if (line.includes('red herring') || line.includes('Red Herring')) {
            continue;
        }
        if (line.trim() && !line.includes('KILLER:') && !line.includes('MOTIVE:')) {
            details.push(line.trim());
        }
    }
    
    if (!killer && !motive) {
        const sentences = response.split(/[.!?]/);
        const firstFew = sentences.slice(0, 5).join('. ');
        return `
            <div class="verdict-title">${isCorrect ? '🎉 CASE SOLVED!' : '💀 CASE CLOSED'}</div>
            <div class="verdict-subtitle">${isCorrect ? 'You caught the killer!' : 'The killer will walk free...'}</div>
            <div class="verdict-details">${firstFew}...</div>
        `;
    }
    
    return `
        <div class="verdict-title">${isCorrect ? '🎉 CASE SOLVED!' : '💀 CASE CLOSED'}</div>
        <div class="verdict-subtitle">${isCorrect ? 'You caught the killer!' : 'The killer will walk free...'}</div>
        <div class="verdict-details">
            <p><strong>🔴 Killer:</strong> ${killer || 'Unknown'}</p>
            <p><strong>📖 Motive:</strong> ${motive || 'Unknown'}</p>
            ${details.length > 0 ? `<p><strong>📌 Details:</strong> ${details.slice(0, 3).join(' ')}</p>` : ''}
        </div>
    `;
}

// Add this function to update placeholder based on action
function updatePlaceholder() {
    const action = actionSelect.value;
    const placeholderMap = {
        'interrogate': 'Ask a question to the selected suspect...',
        'discover': 'Where do you want to search? (optional)',
        'analyze': 'Click a clue first, no typing needed!',
        'hint': 'No typing needed, just click Send!',
        'accuse': 'Enter the name of the person you accuse...'
    };
    chatInput.placeholder = placeholderMap[action] || 'Type your message...';
}

// Add event listener for action select
actionSelect.addEventListener('change', updatePlaceholder);

// Call it on initialization
updatePlaceholder();

// Send message
// Send message
function sendMessage() {
    if (!isConnected) {
        addMessage('error', 'Not connected to server. Please refresh.');
        return;
    }

    const action = actionSelect.value;
    const input = chatInput.value.trim();

    // For analyze, we don't need text input
    if (action === 'analyze') {
        if (!selectedClueId) {
            addMessage('error', 'Please click on a clue to select it first.');
            return;
        }
        ws.send(JSON.stringify({
            action: 'analyze',
            clue_id: selectedClueId
        }));
        const clueDesc = getClueDescription(selectedClueId);
        addMessage('detective', `🔬 Analyzing: ${clueDesc}`);
        chatInput.value = '';
        return;
    }

    // For discover, input is optional
    if (action === 'discover') {
        ws.send(JSON.stringify({
            action: 'discover',
            user_input: input || 'the crime scene'
        }));
        addMessage('detective', `🔎 Searching for evidence: ${input || 'the crime scene'}`);
        chatInput.value = '';
        return;
    }

    // For hint, no input needed
    if (action === 'hint') {
        ws.send(JSON.stringify({ action: 'hint' }));
        addMessage('detective', '💡 Asking for a hint...');
        chatInput.value = '';
        return;
    }

    // For interrogate and accuse, we need input
    if (!input) {
        addMessage('error', 'Please enter a question or name.');
        return;
    }

    if (action === 'interrogate') {
        if (!selectedSuspectId) {
            addMessage('error', 'Please click on a suspect to select them first.');
            return;
        }
        ws.send(JSON.stringify({
            action: 'interrogate',
            suspect_id: selectedSuspectId,
            user_input: input
        }));
        const suspectName = getSuspectName(selectedSuspectId);
        addMessage('detective', `🔍 To ${suspectName}: ${input}`);
    
    } else if (action === 'accuse') {
        ws.send(JSON.stringify({
            action: 'accuse',
            user_input: input,
            motive: 'Based on the evidence gathered'
        }));
        addMessage('detective', `⚖️ Accusing: ${input}`);
    }

    chatInput.value = '';
}

// Get suspect name
function getSuspectName(id) {
    if (!gameState || !gameState.suspects) return 'Unknown';
    const suspect = gameState.suspects.find(s => s.id === id);
    return suspect ? suspect.name : 'Unknown';
}

// Get clue description
function getClueDescription(id) {
    if (!gameState || !gameState.discovered_clues) return 'Unknown';
    const clue = gameState.discovered_clues.find(c => c.id === id);
    return clue ? clue.description : 'Unknown';
}

// Add message to chat
function addMessage(type, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';
    
    if (type === 'verdict-win' || type === 'verdict-lose') {
        contentDiv.innerHTML = content;
    } else {
        contentDiv.innerHTML = content.replace(/\n/g, '<br>');
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Update UI
function updateUI() {
    if (!gameState) {
        caseTitle.textContent = 'Not started';
        caseStatus.textContent = 'Waiting';
        accusationCount.textContent = '0/3';
        suspectsList.innerHTML = '<p class="empty">No suspects yet</p>';
        evidenceList.innerHTML = '<p class="empty">No evidence discovered</p>';
        return;
    }

    caseTitle.textContent = gameState.case_title || 'Untitled';
    caseStatus.textContent = gameState.phase || 'Investigation';
    accusationCount.textContent = `${gameState.accusations_made || 0}/${gameState.max_accusations || 3}`;

    // Suspects
    if (gameState.suspects && gameState.suspects.length > 0) {
        suspectsList.innerHTML = gameState.suspects.map(s => {
            let badgeText = s.interrogated ? '✅ Interrogated' : '❓ Unknown';
            let badgeClass = s.interrogated ? '' : '';
            
            if (gameComplete && s.is_killer) {
                badgeText = '🔴 KILLER';
                badgeClass = 'killer-revealed';
            }
            
            const isSelected = selectedSuspectId === s.id;
            
            return `
                <div class="suspect-item ${s.interrogated ? 'interrogated' : ''} ${isSelected ? 'selected' : ''}" 
                     data-id="${s.id}" onclick="selectSuspect('${s.id}')">
                    <span>${s.name}</span>
                    <span class="badge ${badgeClass}">${badgeText}</span>
                </div>
            `;
        }).join('');
    }

    // Evidence
    const discoveredClues = gameState.discovered_clues.filter(c => c.discovered);
    if (discoveredClues.length > 0) {
        evidenceList.innerHTML = discoveredClues.map(c => {
            const isSelected = selectedClueId === c.id;
            let statusBadges = '';
            
            if (c.analyzed) {
                statusBadges += `<span class="status-badge analyzed">🔬 Analyzed</span>`;
            }
            if (c.discovered) {
                statusBadges += `<span class="status-badge discovered">🔍 Discovered</span>`;
            }
            
            return `
                <div class="evidence-item ${c.discovered ? 'discovered' : ''} ${c.analyzed ? 'analyzed' : ''} ${isSelected ? 'selected' : ''}"
                     data-id="${c.id}" onclick="selectClue('${c.id}')">
                    <div>${c.description} ${statusBadges}</div>
                    <div class="type">${c.type}</div>
                </div>
            `;
        }).join('');
    } else {
        evidenceList.innerHTML = '<p class="empty">No evidence discovered yet. Use "Search for Evidence" to find clues!</p>';
    }
}

// Select suspect
function selectSuspect(id) {
    selectedSuspectId = id;
    document.querySelectorAll('.suspect-item').forEach(el => el.classList.remove('selected'));
    const el = document.querySelector(`.suspect-item[data-id="${id}"]`);
    if (el) el.classList.add('selected');
    
    selectedClueId = null;
    document.querySelectorAll('.evidence-item').forEach(el => el.classList.remove('selected'));
}

// Select clue
function selectClue(id) {
    selectedClueId = id;
    document.querySelectorAll('.evidence-item').forEach(el => el.classList.remove('selected'));
    const el = document.querySelector(`.evidence-item[data-id="${id}"]`);
    if (el) el.classList.add('selected');
    
    selectedSuspectId = null;
    document.querySelectorAll('.suspect-item').forEach(el => el.classList.remove('selected'));
}

// Start game
function startGame() {
    if (!isConnected) {
        addMessage('error', 'Not connected to server. Please refresh.');
        return;
    }
    chatMessages.innerHTML = '';
    ws.send(JSON.stringify({ action: 'start' }));
    addMessage('system', '🔄 Generating a new murder mystery...');
}

// Reset game
function resetGame() {
    if (!isConnected) {
        addMessage('error', 'Not connected to server.');
        return;
    }
    ws.send(JSON.stringify({ action: 'reset' }));
}

// Setup action select with all options
function setupActionSelect() {
    actionSelect.innerHTML = `
        <option value="interrogate">🔍 Interrogate</option>
        <option value="discover">🔎 Search for Evidence</option>
        <option value="analyze">🔬 Analyze Evidence</option>
        <option value="hint">💡 Get Hint</option>
        <option value="accuse">⚖️ Accuse</option>
    `;
}

// Event Listeners
sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
startBtn.addEventListener('click', startGame);
resetBtn.addEventListener('click', resetGame);

// Initialize
setupActionSelect();
connectWebSocket();