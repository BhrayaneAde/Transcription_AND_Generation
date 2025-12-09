// App.tsx
import React, { useEffect, useRef, useState } from "react";
import "./App.css";

interface Message {
  user: string;
  ai?: string;
}

const App: React.FC = () => {
  // UI / connexion
  const [backendUrl, setBackendUrl] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState("Déconnecté");
  const [messages, setMessages] = useState<Message[]>([]);

  // Modes / flags
  const [listeningActive, setListeningActive] = useState(false); // mode écoute globale activée
  const [vadEnabled, setVadEnabled] = useState(true); // on conserve le choix VAD
  const [isRecording, setIsRecording] = useState(false);

  // Refs pour audio / VAD / enregistrement
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const rafIdRef = useRef<number | null>(null);
  const silenceStartRef = useRef<number | null>(null);
  const speakingRef = useRef(false);
  const isSendingRef = useRef(false); // éviter envoi concurrent
  const activationRequestedRef = useRef(false); // éviter double activation

  // Paramètres VAD
  const SPEECH_THRESHOLD = 12; // ajustable: seuil pour considérer qu'on parle
  const SILENCE_THRESHOLD = 6; // ajustable: seuil de "vrai" silence
  const SILENCE_DURATION = 3000; // ms (3s)

  // --- Connexion test ---
  const testConnection = async () => {
    try {
      const cleanUrl = backendUrl.replace(/\/$/, "");
      const res = await fetch(`${cleanUrl}/`);
      if (res.ok) {
        setIsConnected(true);
        setStatus("✅ Connecté - Prêt");
        setBackendUrl(cleanUrl);
      } else {
        setStatus("❌ Erreur connexion");
      }
    } catch (err) {
      setStatus("❌ Impossible de se connecter");
    }
  };

  // --- Activation / Désactivation de l'agent (écoute permanente) ---
  const activateAgent = async () => {
    if (listeningActive || activationRequestedRef.current) return;
    activationRequestedRef.current = true;
    try {
      // obtenir le flux micro (on gardera les pistes ouvertes tout le temps)
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      // créer AudioContext + analyser
      const AudioCtxClass = (window as any).AudioContext || (window as any).webkitAudioContext;
      const audioCtx = new AudioCtxClass();
      audioContextRef.current = audioCtx;
      // forcer reprise si besoin (Chrome)
      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 512;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      setStatus("👂 Écoute active — en attente de voix");
      setListeningActive(true);
      activationRequestedRef.current = false;

      // lancer la boucle d'analyse (VAD passive)
      rafIdRef.current = requestAnimationFrame(analyzeLoop);
    } catch (err) {
      console.error("Erreur accès micro:", err);
      setStatus("❌ Erreur microphone");
      activationRequestedRef.current = false;
    }
  };

  const deactivateAgent = () => {
    // arrêt propre de tout (arrêter tracks, fermer AudioContext, annuler RAF)
    if (rafIdRef.current) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }

    if (audioContextRef.current) {
      try {
        audioContextRef.current.close();
      } catch {}
      audioContextRef.current = null;
    }

    analyserRef.current = null;
    setListeningActive(false);
    setIsRecording(false);
    setStatus("⏹️ Agent désactivé");
  };

  // --- Boucle d'analyse (écoute passive puis démarrage enregistrement) ---
  const analyzeLoop = () => {
    try {
      if (!analyserRef.current) return;

      const analyser = analyserRef.current;
      const bufferLen = analyser.fftSize;
      const data = new Uint8Array(bufferLen);
      analyser.getByteTimeDomainData(data);

      // calcul simple d'énergie RMS
      let sum = 0;
      for (let i = 0; i < bufferLen; i++) {
        const v = (data[i] - 128) / 128;
        sum += v * v;
      }
      const volume = Math.sqrt(sum / bufferLen) * 100;

      // Détection du début de parole
      if (!isRecording && !isSendingRef.current && volume > SPEECH_THRESHOLD) {
        console.log("-> Début parole détecté (analyse). Volume:", volume);
        startRecording(); // démarrer MediaRecorder
      }

      // si enregistrement en cours, on continue la boucle (mais stopRecording gère la fin)
      rafIdRef.current = requestAnimationFrame(analyzeLoop);
    } catch (err) {
      console.error("erreur analyzeLoop", err);
      rafIdRef.current = requestAnimationFrame(analyzeLoop);
    }
  };

  // --- Start / Stop recording (MediaRecorder) ---
  const startRecording = async () => {
    if (!mediaStreamRef.current) {
      console.warn("startRecording appelé sans mediaStream");
      return;
    }
    if (isRecording) return;

    try {
      setIsRecording(true);
      setStatus("🎤 Enregistrement...");
      audioChunksRef.current = [];

      // initialiser MediaRecorder
      const options: any = { mimeType: "audio/webm" }; // navigateur moderne ; backend doit accepter
      const mr = new MediaRecorder(mediaStreamRef.current, options);
      mediaRecorderRef.current = mr;

      mr.ondataavailable = (ev: BlobEvent) => {
        if (ev.data && ev.data.size > 0) {
          audioChunksRef.current.push(ev.data);
        }
      };

      mr.onstop = async () => {
        setIsRecording(false);
        setStatus("⏳ Traitement audio...");
        // créer Blob final (wav/webm selon implémentation)
        const audioBlob = new Blob(audioChunksRef.current, { type: audioChunksRef.current[0]?.type || "audio/webm" });
        // envoyer au backend et attendre réponse
        await sendAudioToBackend(audioBlob);
        // Après réception, retourner en écoute passive (analyseLoop tourne déjà)
        if (listeningActive) {
          setStatus("👂 Écoute active — en attente de voix");
          // réinitialiser VAD
          silenceStartRef.current = null;
          speakingRef.current = false;
          // s'assurer que analyzeLoop tourne
          if (!rafIdRef.current && analyserRef.current) {
            rafIdRef.current = requestAnimationFrame(analyzeLoop);
          }
        }
      };

      mr.start();
      // On démarre aussi la surveillance du silence pour auto-stop
      monitorSilenceWhileRecording();
    } catch (err) {
      console.error("startRecording erreur:", err);
      setIsRecording(false);
      setStatus("❌ Erreur enregistrement");
    }
  };

  const monitorSilenceWhileRecording = () => {
    // boucle dédiée pour détecter la fin de parole pendant que MediaRecorder enregistre
    const check = () => {
      try {
        if (!analyserRef.current) return;

        const analyser = analyserRef.current;
        const bufferLen = analyser.fftSize;
        const data = new Uint8Array(bufferLen);
        analyser.getByteTimeDomainData(data);

        let sum = 0;
        for (let i = 0; i < bufferLen; i++) {
          const v = (data[i] - 128) / 128;
          sum += v * v;
        }
        const volume = Math.sqrt(sum / bufferLen) * 100;
        const now = Date.now();

        // Si on est en train de parler -> reset silence timer
        if (volume > SPEECH_THRESHOLD) {
          speakingRef.current = true;
          silenceStartRef.current = null;
        } else {
          // si on parlait, commencer à compter le silence
          if (speakingRef.current && volume < SILENCE_THRESHOLD) {
            if (!silenceStartRef.current) silenceStartRef.current = now;
            else if (now - silenceStartRef.current > SILENCE_DURATION) {
              // fin de parole détectée
              console.log("Fin parole détectée — arrêt enregistrement");
              if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
                mediaRecorderRef.current.stop();
              }
              return; // on arrête cette boucle
            }
          }
        }

        // continuer la vérification tant que isRecording true pour la transcription
        if (isRecording) {
          requestAnimationFrame(check);
        }
      } catch (err) {
        console.error("monitorSilence erreur:", err);
        if (isRecording) requestAnimationFrame(check);
      }
    };

    // lancer la première itération
    requestAnimationFrame(check);
  };

  // --- Envoi audio au backend et traitement réponse ---
  const sendAudioToBackend = async (audioBlob: Blob) => {
    if (!backendUrl) {
      setStatus("❌ Pas d'URL backend");
      return;
    }
    if (isSendingRef.current) {
      console.warn("Envoi concurrent évité");
      return;
    }
    isSendingRef.current = true;

    try {
      const formData = new FormData();
      // Nommer le fichier avec extension appropriée si possible
      const ext = audioBlob.type.includes("wav") ? "wav" : audioBlob.type.includes("ogg") ? "ogg" : "webm";
      formData.append("file", audioBlob, `audio.${ext}`);

      setStatus("🔁 Envoi au backend...");
      const res = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        setStatus("❌ Erreur backend");
        isSendingRef.current = false;
        return;
      }

      const data = await res.json();
      // mettre à jour messages (remplace le message en cours d'envoi si nécessaire)
      setMessages((prev) => {
        const copy = [...prev];
        copy.push({ user: data.transcript ?? "🗣️ (audio)", ai: data.response ?? "" });
        return copy;
      });

      setStatus("✅ Réponse reçue");
    } catch (err) {
      console.error("sendAudioToBackend erreur:", err);
      setStatus("❌ Erreur envoi");
    } finally {
      isSendingRef.current = false;
    }
  };

  // Nettoyage au démontage
  useEffect(() => {
    return () => {
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
      if (mediaStreamRef.current) mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      if (audioContextRef.current) audioContextRef.current.close().catch(() => {});
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Effacer messages
  const clearMessages = () => setMessages([]);

  return (
    <div className="app">
      <header className="header">
        <h1>🤖 Agent — Écoute automatique (VAD)</h1>
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
          {messages.map((m, i) => (
            <div key={i} className="message-pair">
              <div className="user-message">👤 {m.user}</div>
              {m.ai && <div className="ai-message">🤖 {m.ai}</div>}
            </div>
          ))}
        </div>
      </div>

      <div className="controls">
        <label style={{ display: "block", marginBottom: 10 }}>
          <input
            type="checkbox"
            checked={vadEnabled}
            onChange={(e) => setVadEnabled(e.target.checked)}
            disabled={listeningActive}
          />{" "}
          Mode VAD (arrêt auto après 3s de silence)
        </label>

        {!listeningActive ? (
          <button
            onClick={activateAgent}
            className="activate-btn"
            disabled={!isConnected}
          >
            ▶️ Activer l'agent
          </button>
        ) : (
          <button onClick={deactivateAgent} className="deactivate-btn">
            ⏹️ Désactiver l'agent
          </button>
        )}

        <button onClick={clearMessages} className="clear-btn">
          🗑️ Effacer
        </button>
      </div>

      <div style={{ marginTop: 8 }}>
        <small>
          {isRecording ? "🔴 Enregistrement en cours..." : listeningActive ? "👂 En écoute (démarre l'enregistrement automatiquement lorsque vous parlez)" : "Agent inactif"}
        </small>
      </div>
    </div>
  );
};

export default App;
