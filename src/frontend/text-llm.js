let currentLanguage = 'en';

const greetings = {
    en: 'Hello! I\'m your local AI assistant. How can I help you today?',
    hi: 'नमस्ते! मैं आपका स्थानीय AI सहायक हूं। आज मैं आपकी कैसे मदद कर सकता हूं?'
};

const responses = {
    en: 'I understand your query. This is a local LLM running on Raspberry Pi.',
    hi: 'मैं आपका प्रश्न समझता हूं। यह Raspberry Pi पर चल रहा एक स्थानीय LLM है।'
};

function setLanguage(lang) {
    currentLanguage = lang;
    document.getElementById('language-select').value = lang;
}

function clearChat() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = `
        <div class="message bot">
            <div class="message-content">
                ${greetings[currentLanguage]}
            </div>
        </div>
    `;
}

function sendMessage(event) {
    event.preventDefault();

    const input = document.getElementById('user-input');
    const userMessage = input.value.trim();

    if (!userMessage) return;

    const chatMessages = document.getElementById('chat-messages');

    const userDiv = document.createElement('div');
    userDiv.className = 'message user';
    userDiv.innerHTML = `<div class="message-content">${userMessage}</div>`;
    chatMessages.appendChild(userDiv);

    input.value = '';

    setTimeout(() => {
        const botDiv = document.createElement('div');
        botDiv.className = 'message bot';
        botDiv.innerHTML = `<div class="message-content">${responses[currentLanguage]}</div>`;
        chatMessages.appendChild(botDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 500);

    chatMessages.scrollTop = chatMessages.scrollHeight;
}
