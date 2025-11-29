/**
 * Gus App - Frontend Logic
 * Handles chat interactions and source citations
 */

// DOM Elements
const chatArea = document.getElementById('chatArea');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const newChatBtn = document.getElementById('newChatBtn');

// State
let isLoading = false;

/**
 * Create YouTube icon SVG
 */
function getYouTubeIcon() {
    return `<svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814z"/>
        <path fill="#fff" d="M9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
    </svg>`;
}

/**
 * Create book/document icon SVG
 */
function getDocIcon() {
    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
    </svg>`;
}

/**
 * Render sources as clickable citations
 */
function renderSources(sources) {
    if (!sources || sources.length === 0) {
        return '';
    }
    
    let html = `
        <div class="sources-container">
            <div class="sources-label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                </svg>
                Sumber / Sources
            </div>
    `;
    
    sources.forEach(source => {
        const icon = source.type === 'video' ? getYouTubeIcon() : getDocIcon();
        const iconBgClass = source.type === 'video' ? 'background-color: #dc2626;' : 'background-color: #92400e;';
        
        html += `
            <a href="${source.url}" target="_blank" rel="noopener noreferrer" class="source-item">
                <div class="source-icon" style="${iconBgClass}">
                    ${icon}
                </div>
                <div class="source-info">
                    <div class="source-title">${source.title}</div>
                    <div class="source-meta">${source.channel || ''} ${source.date ? '• ' + source.date : ''}</div>
                </div>
            </a>
        `;
    });
    
    html += '</div>';
    return html;
}

/**
 * Add a message to the chat area
 */
function addMessage(text, type = 'bot', sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Handle line breaks in text
    let messageHtml = text.replace(/\n/g, '<br>');
    
    // Add sources if available (only for bot messages)
    if (type === 'bot' && sources && sources.length > 0) {
        messageHtml += renderSources(sources);
    }
    
    contentDiv.innerHTML = messageHtml;
    messageDiv.appendChild(contentDiv);
    chatArea.appendChild(messageDiv);
    
    scrollToBottom();
    return messageDiv;
}

/**
 * Show loading indicator
 */
function showLoading() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message loading-message';
    messageDiv.id = 'loadingMessage';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = `
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
        <span style="margin-left: 8px;">Sedang berpikir...</span>
    `;
    
    messageDiv.appendChild(contentDiv);
    chatArea.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    const loadingMsg = document.getElementById('loadingMessage');
    if (loadingMsg) {
        loadingMsg.remove();
    }
}

/**
 * Scroll chat to bottom
 */
function scrollToBottom() {
    requestAnimationFrame(() => {
        chatArea.scrollTop = chatArea.scrollHeight;
    });
}

/**
 * Auto-resize textarea based on content
 */
function autoResize() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
}

/**
 * Start a new chat
 */
function newChat() {
    // Clear all messages except welcome and disclaimer
    chatArea.innerHTML = `
        <div class="message bot-message">
            <div class="message-content">
                <strong>Assalamu'alaikum!</strong> 👋
                <br><br>
                Ayo, mau tanya apa? Jangan susah-susah, santai aja.
                <br><br>
                <span class="text-amber-600 text-sm">You can also ask in English!</span>
            </div>
        </div>
        
        <div class="disclaimer">
            ⚠️ Ini chatbot edukasi bergaya Gus Baha, <strong>bukan fatwa resmi</strong>. 
            Untuk keputusan penting, konsultasikan dengan ulama.
        </div>
    `;
    userInput.focus();
}

/**
 * Send message to backend
 */
async function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message || isLoading) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input and reset height
    userInput.value = '';
    userInput.style.height = 'auto';
    
    // Set loading state
    isLoading = true;
    sendBtn.disabled = true;
    showLoading();
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        });
        
        const data = await response.json();
        
        hideLoading();
        
        if (data.success && data.response) {
            // Only show sources if context was actually used
            const sourcesToShow = data.context_used ? (data.sources || []) : [];
            addMessage(data.response, 'bot', sourcesToShow);
        } else {
            const errorMsg = data.error || 'Maaf, ada gangguan. Coba lagi ya.';
            addMessage(errorMsg, 'error');
        }
        
    } catch (error) {
        console.error('Chat error:', error);
        hideLoading();
        addMessage('Maaf, koneksi terputus. Coba lagi ya.', 'error');
    } finally {
        isLoading = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}

/**
 * Handle Enter key (send) and Shift+Enter (new line)
 */
function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// Event Listeners
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', handleKeyDown);
userInput.addEventListener('input', autoResize);
newChatBtn.addEventListener('click', newChat);

// Focus input on load (desktop only)
if (window.innerWidth >= 640) {
    userInput.focus();
}

// Prevent zoom on double-tap (iOS)
let lastTouchEnd = 0;
document.addEventListener('touchend', (e) => {
    const now = Date.now();
    if (now - lastTouchEnd <= 300) {
        e.preventDefault();
    }
    lastTouchEnd = now;
}, false);
