console.log('text-llm.js loaded (updated)');
let currentLanguage = 'en';

// Proxy URL: default to localhost:3000 but allow using relative path when proxy is hosted with frontend
const PROXY_URL = window.PROXY_URL || 'http://localhost:3000/api/generate';

const greetings = {
    en: 'Hello! I\'m your local AI assistant. How can I help you today?',
    hi: 'नमस्ते! मैं आपका स्थानीय AI सहायक हूं। आज मैं आपकी कैसे मदद कर सकता हूं?'
};

// Prompt template. Edit this to change how user input is embedded.
// Use {{USER}} as placeholder for the raw user input. You can also use
// {{CONTEXT}} and {{INSTRUCTIONS}} for additional data.
const PROMPT_TEMPLATE = `
You are a strict, professional evaluator for a kiosk-based system. 
Your answers must always be concise, highly relevant to the user's query, 
and limited to what is necessary—no extra explanation.

Your task:
Answer user's query correctly and precisely, give only accurate information. Search the web if needed to verify the information.
Response should be plain text, in about 2-3 sentences.

User Input:
{{USER}}

Context:
{{CONTEXT}}

Instructions:
{{INSTRUCTIONS}}
`;

function buildPrompt(template, userText, extras = {}) {
    let out = template;
    out = out.replace(/{{\s*USER\s*}}/g, userText || '');
    out = out.replace(/{{\s*CONTEXT\s*}}/g, extras.context || '');
    out = out.replace(/{{\s*INSTRUCTIONS\s*}}/g, extras.instructions || '');
    // replace any additional placeholders in extras
    Object.keys(extras).forEach(k => {
        const re = new RegExp(`{{\\s*${k.toUpperCase()}\\s*}}`, 'g');
        out = out.replace(re, extras[k] || '');
    });
    return out.trim();
}

function setLanguage(lang) {
    currentLanguage = lang;
    const sel = document.getElementById('language-select');
    if (sel) sel.value = lang;
}

function clearChat() {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    chatMessages.innerHTML = `
        <div class="message bot">
            <div class="message-content">
                ${greetings[currentLanguage]}
            </div>
        </div>
    `;
}

function appendMessage(role, text, id) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    const div = document.createElement('div');
    div.className = 'message ' + (role === 'user' ? 'user' : 'bot');
    if (id) div.id = id;
    const inner = document.createElement('div');
    inner.className = 'message-content';
    inner.textContent = text;
    div.appendChild(inner);
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return div;
}

async function callProxy(prompt) {
    try {
        const res = await fetch(PROXY_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        const j = await res.json();
        return j;
    } catch (err) {
        return { ok: false, error: String(err) };
    }
}

async function sendMessage(event) {
    event && event.preventDefault && event.preventDefault();
    const input = document.getElementById('user-input');
    if (!input) return;
    const userMessage = input.value.trim();
    if (!userMessage) return;

    // show user message
    appendMessage('user', userMessage);
    input.value = '';

    // show loading
    const loadingId = 'loading-msg';
    appendMessage('bot', 'Thinking…', loadingId);

    // build prompt from template so user input is embedded into a structured prompt
    const extras = { context: `Language: ${currentLanguage}`, instructions: '' };
    const finalPrompt = buildPrompt(PROMPT_TEMPLATE, userMessage, extras);
    const resp = await callProxy(finalPrompt);
    // remove loading
    const loading = document.getElementById(loadingId);
    if (loading) loading.remove();

    if (resp && resp.ok) {
        const text = resp.text || (resp.raw && JSON.stringify(resp.raw)) || 'No response text';
        appendMessage('bot', text);
    } else {
        const err = resp && (resp.error || resp) || 'Unknown error';
        appendMessage('bot', 'Error: ' + (typeof err === 'string' ? err : JSON.stringify(err)));
    }
}
