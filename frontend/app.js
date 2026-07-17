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
                    const cleanResponse = extractVerdictInfo(data.response, true, data.game_state);
                    addMessage('verdict-win', cleanResponse);
                    statusText.textContent = '\u2705 Solved!';
                    statusText.style.color = '#4caf50';
                } else {
                    const cleanResponse = extractVerdictInfo(data.response, false, data.game_state);
                    addMessage('verdict-lose', cleanResponse);
                    statusText.textContent = '\u274c Case Closed';
                    statusText.style.color = '#ef5350';
                }
            } else if (data.action === 'interrogate') {
                // Suspect response — render with styled expression tag
                addSuspectMessage(data.response);
            } else {
                addMessage('system', data.response);
            }
            break;

        case 'discover_result':
            gameState = data.game_state;
            updateUI();
            // Show ONLY the atmospheric narrative, never the clue description
            addMessage('system', data.response);
            if (data.new_clues && data.new_clues.length > 0) {
                // Show clue names so players know what was logged
                const clueNames = data.new_clues
                    .map(c => c.name || c.description?.split(' ').slice(0, 4).join(' ') || 'Unknown evidence')
                    .join(', ');
                addMessage('system', `🔒 New evidence logged: <strong>${clueNames}</strong> — click it in the evidence panel and analyze to reveal details.`);
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

// Build a rich post-case debrief panel
function extractVerdictInfo(response, isCorrect, gs) {
    // --- parse LLM text for killer name, motive, details ---
    const lines = response.split('\n');
    let killerNameParsed = '';
    let motiveParsed = '';
    let detailLines = [];
    for (let line of lines) {
        const l = line.trim();
        if (!l) continue;
        if (/^(true\s+)?killer:/i.test(l)) {
            killerNameParsed = l.replace(/^(true\s+)?killer:\s*/i, '').trim();
        } else if (/^motive:/i.test(l)) {
            motiveParsed = l.replace(/^motive:\s*/i, '').trim();
        } else if (!/^verdict:/i.test(l) && !/^details:/i.test(l)) {
            // Capture DETAILS line content
            const detailMatch = l.match(/^details?:\s*(.+)/i);
            if (detailMatch) detailLines.push(detailMatch[1]);
            else if (l.length > 10) detailLines.push(l);
        }
    }

    // --- build suspect debrief rows from game state ---
    let suspectRows = '';
    let clueRows = '';

    if (gs && gs.suspects && gs.suspects.length > 0) {
        const killer = gs.suspects.find(s => s.is_killer);
        const innocents = gs.suspects.filter(s => !s.is_killer);

        // True killer row — prominent
        if (killer) {
            const killerSecrets = (killer.secrets || []).join('; ') || 'Hidden motive';
            suspectRows += `
                <div class="debrief-suspect killer-row">
                    <div class="debrief-suspect-header">
                        <span class="debrief-badge killer">🔴 THE KILLER</span>
                        <strong>${killer.name}</strong>
                        <span class="debrief-role">${killer.role}</span>
                    </div>
                    <div class="debrief-suspect-body">
                        <p><span class="debrief-label">Motive:</span> ${gs.motive || motiveParsed || 'Unknown'}</p>
                        <p><span class="debrief-label">Alibi (cover story):</span> ${killer.alibi}</p>
                        <p><span class="debrief-label">Their secret:</span> ${killerSecrets}</p>
                    </div>
                </div>`;
        }

        // Innocent suspects — collapsed detail
        for (const s of innocents) {
            const secrets = (s.secrets || []).join('; ') || 'No hidden motive';
            suspectRows += `
                <div class="debrief-suspect innocent-row">
                    <div class="debrief-suspect-header">
                        <span class="debrief-badge innocent">✅ Innocent</span>
                        <strong>${s.name}</strong>
                        <span class="debrief-role">${s.role}</span>
                    </div>
                    <div class="debrief-suspect-body">
                        <p><span class="debrief-label">Why they seemed suspicious:</span> ${secrets}</p>
                        <p><span class="debrief-label">Alibi:</span> ${s.alibi}</p>
                    </div>
                </div>`;
        }

        // Clues breakdown
        const discovered = (gs.discovered_clues || []).filter(c => c.discovered);
        if (discovered.length > 0) {
            for (const c of discovered) {
                const icon = c.is_red_herring ? '🎭' : '🔑';
                const label = c.is_red_herring ? 'Red Herring' : 'Real Clue';
                const cls = c.is_red_herring ? 'clue-herring' : 'clue-real';
                clueRows += `
                    <div class="debrief-clue ${cls}">
                        <span class="debrief-clue-icon">${icon}</span>
                        <div>
                            <strong>${c.name || ''}</strong>
                            ${c.name ? '<br>' : ''}
                            <span class="debrief-clue-desc">${c.description}</span>
                            <span class="debrief-clue-tag">${label}</span>
                        </div>
                    </div>`;
            }
        }
    }

    const narrativeSummary = detailLines.slice(0, 3).join(' ');

    return `
        <div class="verdict-title">${isCorrect ? '🎉 CASE SOLVED!' : '💀 CASE CLOSED'}</div>
        <div class="verdict-subtitle">${isCorrect ? 'You caught the killer!' : 'The killer walked free... Here is what really happened.'}</div>
        ${narrativeSummary ? `<div class="verdict-narrative">${narrativeSummary}</div>` : ''}
        ${suspectRows ? `
        <div class="debrief-section">
            <div class="debrief-section-title">👥 The Full Picture</div>
            <div class="debrief-suspects">${suspectRows}</div>
        </div>` : ''}
        ${clueRows ? `
        <div class="debrief-section">
            <div class="debrief-section-title">🔍 Evidence Breakdown</div>
            <div class="debrief-clues">${clueRows}</div>
        </div>` : ''}
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

// Add a suspect message with styled [expression] tag
function addSuspectMessage(content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message suspect-response';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';
    
    // Parse [expression] tag at the start
    // Pattern: **Name**: [expression] dialogue
    // or just: [expression] dialogue
    const expressionRegex = /^(\*\*[^*]+\*\*:\s*)?(\[[^\]]+\])\s*/;
    const match = content.match(expressionRegex);
    
    if (match) {
        const namePrefix = match[1] || '';
        const expression = match[2];
        const dialogue = content.slice(match[0].length);
        
        // Build the name part (bold)
        let html = '';
        if (namePrefix) {
            const nameText = namePrefix.replace(/\*\*/g, '').replace(/:\s*$/, '');
            html += `<span class="suspect-name">${nameText}</span><span class="suspect-colon">: </span>`;
        }
        html += `<em class="suspect-expression">${expression}</em> `;
        html += `<span class="suspect-dialogue">${dialogue.replace(/\n/g, '<br>')}</span>`;
        contentDiv.innerHTML = html;
    } else {
        // Fallback: render the **Name**: bold, rest as dialogue
        contentDiv.innerHTML = content
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
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
        contentDiv.innerHTML = content
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Update UI
function updateUI() {
    if (!gameState) {
        caseTitle.textContent = 'Not started';
        suspectsList.innerHTML = '<p class="empty">No suspects yet</p>';
        evidenceList.innerHTML = '<p class="empty">No evidence discovered</p>';
        return;
    }

    caseTitle.textContent = gameState.case_title || 'Untitled';

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
                statusBadges += `<span class="status-badge analyzed">\uD83D\uDD2C Analyzed</span>`;
            }
            if (c.discovered) {
                statusBadges += `<span class="status-badge discovered">\uD83D\uDD0D Discovered</span>`;
            }
            
            // Hide description until analyzed
            const typeIcons = { physical: '\uD83D\uDC64', document: '\uD83D\uDCCB', digital: '\uD83D\uDCF1', testimony: '\uD83D\uDDE3\uFE0F' };
            const typeIcon = typeIcons[c.type] || '\uD83D\uDD0D';
            
            let displayText;
            if (c.analyzed) {
                // After analysis: show full description
                displayText = `<div class="evidence-desc">${c.description}</div>`;
            } else {
                // Before analysis: show clue name (or derived fallback) + type icon
                const displayName = c.name || c.description?.split(' ').slice(0, 4).join(' ') || 'Unknown Evidence';
                displayText = `<div class="evidence-desc locked"><strong>${typeIcon} ${displayName}</strong><br><em style="font-size:11px;color:#888;">— analyze to reveal details</em></div>`;
            }
            
            return `
                <div class="evidence-item ${c.discovered ? 'discovered' : ''} ${c.analyzed ? 'analyzed' : ''} ${isSelected ? 'selected' : ''}"
                     data-id="${c.id}" onclick="selectClue('${c.id}')">
                    ${displayText}
                    <div class="type-badges">${statusBadges}</div>
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