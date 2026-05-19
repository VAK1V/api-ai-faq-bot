// ===== Configuration =====
const API_BASE = window.location.origin;
const MAX_TEXT_LENGTH = 500;

// ===== State =====
let currentChatId = null;
let isLoading = false;
let messages = [];

// ===== DOM Elements =====
const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const historyList = document.getElementById('history-list');
const statusDot = document.querySelector('.status-dot');
const statusText = document.querySelector('.status-text');
const modelNameEl = document.getElementById('model-name');
const charCount = document.getElementById('char-count');

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadHistory();
    setupInput();

    // Check health every 30 seconds
    setInterval(checkHealth, 30000);
});

// ===== Health Check =====
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();

        if (data.status === 'ok' && data.model_loaded) {
            statusDot.className = 'status-dot online';
            statusText.textContent = 'Онлайн';
            modelNameEl.textContent = data.model_name || 'Модель загружена';
            sendBtn.disabled = isLoading;
        } else if (data.status === 'ok') {
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Модель загружается...';
            modelNameEl.textContent = 'Загрузка...';
            sendBtn.disabled = true;
        } else {
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Ошибка сервера';
            sendBtn.disabled = true;
        }
    } catch (error) {
        statusDot.className = 'status-dot offline';
        statusText.textContent = 'Нет соединения';
        modelNameEl.textContent = '—';
        sendBtn.disabled = true;
    }
}

// ===== Input Handling =====
function setupInput() {
    messageInput.addEventListener('input', () => {
        // Auto-resize
        messageInput.style.height = 'auto';
        messageInput.style.height = messageInput.scrollHeight + 'px';

        // Character count
        const len = messageInput.value.length;
        charCount.textContent = `${len}/${MAX_TEXT_LENGTH}`;
        charCount.style.color = len > MAX_TEXT_LENGTH ? '#ef4444' : '#888';

        // Enable/disable send button
        sendBtn.disabled = len === 0 || len > MAX_TEXT_LENGTH || isLoading;
    });
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        if (!sendBtn.disabled) {
            sendMessage();
        }
    }
}

function sendSuggestion(button) {
    messageInput.value = button.textContent;
    messageInput.dispatchEvent(new Event('input'));
    sendMessage();
}

// ===== Send Message =====
async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || text.length > MAX_TEXT_LENGTH || isLoading) return;

    // Add user message to UI
    addMessage('user', text);
    messages.push({ role: 'user', text });

    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    messageInput.dispatchEvent(new Event('input'));

    // Show typing indicator
    showTypingIndicator();
    isLoading = true;
    sendBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/api/v1/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка сервера');
        }

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator();

        // Add bot response
        addMessage('bot', data.result, data.processing_time_ms);
        messages.push({ 
            role: 'bot', 
            text: data.result,
            model: data.model,
            time: data.processing_time_ms 
        });

        // Reload history sidebar
        loadHistory();

    } catch (error) {
        removeTypingIndicator();
        addMessage('bot', `❌ Ошибка: ${error.message}`, null, true);
        showToast(error.message, 'error');
    } finally {
        isLoading = false;
        sendBtn.disabled = messageInput.value.length === 0;
    }
}

// ===== Add Message to UI =====
function addMessage(role, text, processingTime = null, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = role === 'user' ? '👤' : '😄';
    const time = new Date().toLocaleTimeString('ru-RU', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });

    let timeInfo = '';
    if (processingTime) {
        timeInfo = `<div class="message-time">${time} · ${(processingTime / 1000).toFixed(1)}с</div>`;
    } else {
        timeInfo = `<div class="message-time">${time}</div>`;
    }

    // Convert newlines to <br>
    const formattedText = text.replace(/\n/g, '<br>');

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div>
            <div class="message-content" style="${isError ? 'color: #ef4444;' : ''}">${formattedText}</div>
            ${timeInfo}
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// ===== Typing Indicator =====
function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message bot typing-indicator-container';
    indicator.id = 'typing-indicator';
    indicator.innerHTML = `
        <div class="message-avatar">😄</div>
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    messagesContainer.appendChild(indicator);
    scrollToBottom();
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

// ===== Scroll =====
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ===== Load History =====
async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/history?limit=50`);
        const data = await response.json();

        renderHistory(data.items);
    } catch (error) {
        historyList.innerHTML = '<div class="empty-state">Не удалось загрузить историю</div>';
    }
}

function renderHistory(items) {
    if (!items || items.length === 0) {
        historyList.innerHTML = '<div class="empty-state">Нет истории запросов</div>';
        return;
    }

    historyList.innerHTML = items.map(item => {
        const date = new Date(item.created_at);
        const timeStr = date.toLocaleDateString('ru-RU', { 
            day: 'numeric', 
            month: 'short',
            hour: '2-digit',
            minute: '2-digit'
        });

        // Truncate text
        const preview = item.input_text.length > 30 
            ? item.input_text.substring(0, 30) + '...' 
            : item.input_text;

        return `
            <button class="history-item" onclick="loadChatFromHistory(${item.id})" title="${item.input_text}">
                <div>${preview}</div>
                <div class="timestamp">${timeStr}</div>
            </button>
        `;
    }).join('');
}

// ===== Load Chat from History =====
async function loadChatFromHistory(id) {
    try {
        const response = await fetch(`${API_BASE}/api/v1/history/${id}`);
        const data = await response.json();

        // Clear current chat
        messagesContainer.innerHTML = '';
        messages = [];

        // Add messages
        addMessage('user', data.input_text);
        addMessage('bot', data.result_text, null, false);

        document.getElementById('chat-title').textContent = `Чат #${id}`;

        // Highlight active
        document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
        event.target.closest('.history-item').classList.add('active');

    } catch (error) {
        showToast('Не удалось загрузить чат', 'error');
    }
}

// ===== New Chat =====
function startNewChat() {
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">😄</div>
            <h2>Привет! Я AI FAQ Bot</h2>
            <p>Задай мне любой вопрос — я постараюсь ответить.</p>
            <div class="suggestions">
                <button onclick="sendSuggestion(this)">Что такое Docker?</button>
                <button onclick="sendSuggestion(this)">Как работает FastAPI?</button>
                <button onclick="sendSuggestion(this)">Объясни REST API</button>
            </div>
        </div>
    `;
    messages = [];
    document.getElementById('chat-title').textContent = 'Новый чат';

    // Remove active highlight
    document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
}

// ===== Toast Notifications =====
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
