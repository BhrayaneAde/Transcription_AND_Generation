import React, { useState, useRef, useEffect } from 'react';
import './App.css';

interface Message {
  user: string;
  ai?: string;
}

const App: React.FC = () => {
  const [backendUrl, setBackendUrl] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState('Déconnecté');
  const [currentTranscript, setCurrentTranscript] = useState('');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Test connexion backend
  const testConnection = async () => {
    try {
      const response = await fetch(`${backendUrl}/`);
      if (response.ok) {
        setIsConnected(true);
        setStatus('✅ Connecté - Prêt à enregistrer');
      } else {
        setStatus('❌ Erreur connexion');
      }
    } catch (error) {
      setStatus('❌ Impossible de se connecter');
    }
  };



  // Démarrer enregistrement
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        sendAudioToBackend(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start(100); // Chunks de 100ms
      setIsRecording(true);
      setStatus('🎤 Enregistrement...');
      
      // Ajouter message en cours
      setMessages(prev => [...prev, { user: '🎤 En cours...' }]);
      
      // Détecter silence (simulation - 3 secondes max)
      silenceTimerRef.current = setTimeout(() => {
        stopRecording();
      }, 10000);
      
    } catch (error) {
      setStatus('❌ Erreur microphone');
    }
  };

  // Arrêter enregistrement
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setStatus('⏳ Traitement...');
      
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
    }
  };

  // Envoyer audio au backend
  const sendAudioToBackend = async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'audio.wav');
      
      const response = await fetch(`${backendUrl}/chat`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Mettre à jour le dernier message
        setMessages(prev => {
          const newMessages = [...prev];
          if (newMessages.length > 0) {
            newMessages[newMessages.length - 1] = {
              user: data.transcript,
              ai: data.response
            };
          }
          return newMessages;
        });
        
        setStatus('✅ Prêt');
      } else {
        setStatus('❌ Erreur traitement');
      }
    } catch (error) {
      setStatus('❌ Erreur envoi');
    }
  };

  // Effacer conversation
  const clearMessages = () => {
    setMessages([]);
    setCurrentTranscript('');
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🤖 Agent IA - Temps Réel</h1>
      </header>
      
      <div className="connection">
        <input
          type="text"
          placeholder="https://abc123.ngrok.io"
          value={backendUrl}
          onChange={(e) => setBackendUrl(e.target.value)}
          className="url-input"
        />
        <button onClick={testConnection} className="connect-btn">
          Se connecter
        </button>
        <span className="status">{status}</span>
      </div>
      
      <div className="chat-container">
        <div className="messages">
          {messages.map((msg, index) => (
            <div key={index} className="message-pair">
              <div className="user-message">
                👤 {msg.user}
              </div>
              {msg.ai && (
                <div className="ai-message">
                  🤖 {msg.ai}
                </div>
              )}
            </div>
          ))}
          {currentTranscript && (
            <div className="current-transcript">
              📝 {currentTranscript}
            </div>
          )}
        </div>
      </div>
      
      <div className="controls">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={!isConnected}
          className={`record-btn ${isRecording ? 'recording' : ''}`}
        >
          {isRecording ? '🛑 Arrêter' : '🎤 Parler'}
        </button>
        <button onClick={clearMessages} className="clear-btn">
          🗑️ Effacer
        </button>
      </div>
    </div>
  );
};

export default App;