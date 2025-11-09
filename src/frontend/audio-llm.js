let currentLanguage = 'en';
let isRecording = false;

const greetings = {
    en: 'Hello! Press and hold the microphone button to speak.',
    hi: 'नमस्ते! बोलने के लिए माइक्रोफोन बटन दबाएं और रोकें।'
};

const responses = {
    en: 'I\'ve processed your voice input using the local speech recognition model.',
    hi: 'मैंने स्थानीय वाक् पहचान मॉडल का उपयोग करके आपके आवाज़ इनपुट को संसाधित किया है।'
};

const listeningStatus = {
    en: 'Listening...',
    hi: 'सुन रहा हूं...'
};

const processingStatus = {
    en: 'Processing...',
    hi: 'प्रसंस्करण...'
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

function startRecording() {
    isRecording = true;
    const micBtn = document.getElementById('mic-btn');
    const status = document.getElementById('recording-status');

    micBtn.classList.add('recording');
    status.textContent = listeningStatus[currentLanguage];
}

function stopRecording() {
    if (!isRecording) return;

    isRecording = false;
    const micBtn = document.getElementById('mic-btn');
    const status = document.getElementById('recording-status');

    micBtn.classList.remove('recording');
    status.textContent = processingStatus[currentLanguage];

    setTimeout(() => {
        processAudio();
        status.textContent = '';
    }, 1000);
}

function processAudio() {
    const chatMessages = document.getElementById('chat-messages');

    const sampleQueries = {
        en: 'What\'s the weather today?',
        hi: 'आज मौसम कैसा है?'
    };

    const userMessage = sampleQueries[currentLanguage];

    const userDiv = document.createElement('div');
    userDiv.className = 'message user';
    userDiv.innerHTML = `<div class="message-content">${userMessage}</div>`;
    chatMessages.appendChild(userDiv);

    setTimeout(() => {
        const botDiv = document.createElement('div');
        botDiv.className = 'message bot';
        botDiv.innerHTML = `<div class="message-content">${responses[currentLanguage]}</div>`;
        chatMessages.appendChild(botDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 800);

    chatMessages.scrollTop = chatMessages.scrollHeight;
}
