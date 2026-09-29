const micButton = document.getElementById('mic-button');
const statusText = document.getElementById('status-text');
const chatContainer = document.getElementById('chat-container');

// Web Speech API
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const synth = window.speechSynthesis;
let recognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        micButton.classList.add('listening');
        statusText.textContent = 'Listening...';
    };

    recognition.onresult = (event) => {
        const query = event.results[0][0].transcript;
        addMessage(query, 'user');
        statusText.textContent = 'Processing...';
        sendCommand(query);
    };

    recognition.onerror = (event) => {
        micButton.classList.remove('listening');
        statusText.textContent = 'Error: ' + event.error;
    };

    recognition.onend = () => {
        micButton.classList.remove('listening');
        if (statusText.textContent === 'Listening...') {
            statusText.textContent = 'Tap to speak';
        }
    };
} else {
    statusText.textContent = 'Web Speech API not supported in this browser.';
    micButton.disabled = true;
}

micButton.addEventListener('click', () => {
    if (micButton.classList.contains('listening')) {
        recognition.stop();
    } else {
        synth.cancel(); // Stop any ongoing speech
        recognition.start();
    }
});

function addMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);
    msgDiv.innerHTML = `<p>${text}</p>`;
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function speakText(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    
    utterance.onend = () => {
        statusText.textContent = 'Tap to speak';
    };

    synth.speak(utterance);
}

async function sendCommand(query) {
    try {
        const response = await fetch('/api/command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            addMessage(data.response, 'system');
            statusText.textContent = 'Speaking...';
            speakText(data.response);
        } else {
            addMessage('Error processing command.', 'system');
            statusText.textContent = 'Tap to speak';
        }
    } catch (error) {
        console.error('API Error:', error);
        addMessage('Failed to connect to Omni Server.', 'system');
        statusText.textContent = 'Tap to speak';
    }
}
