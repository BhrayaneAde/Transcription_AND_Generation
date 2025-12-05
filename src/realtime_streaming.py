import gradio as gr
import websocket
import json
import base64
import threading
import time
import numpy as np
import struct
import queue

class RealTimeAgent:
    def __init__(self):
        self.ws = None
        self.backend_url = ""
        self.chat_history = []
        self.is_connected = False
        self.audio_buffer = []
        self.is_recording = False
        self.last_speech_time = time.time()
        self.silence_threshold = 0.05
        self.silence_duration = 3.0
        
    def connect_websocket(self, backend_url):
        try:
            self.backend_url = backend_url.strip().rstrip('/')
            ws_url = self.backend_url.replace('http', 'ws') + '/ws'
            self.ws = websocket.WebSocket()
            self.ws.connect(ws_url)
            self.is_connected = True
            return "✅ Connecté au backend", self.format_chat()
        except Exception as e:
            self.is_connected = False
            return f"❌ Erreur: {e}", self.format_chat()
    
    def start_streaming(self, audio_data):
        if not self.is_connected or not self.ws:
            return "❌ Non connecté", self.format_chat()
            
        if audio_data is None:
            return "🎤 En attente...", self.format_chat()
            
        try:
            sample_rate, audio_array = audio_data
            if len(audio_array) == 0:
                return "🎤 En attente...", self.format_chat()
            
            # Détecter niveau audio
            audio_level = np.max(np.abs(audio_array))
            current_time = time.time()
            
            if audio_level > self.silence_threshold:
                # Parole détectée
                self.last_speech_time = current_time
                self.audio_buffer.extend(audio_array)
                
                if not self.is_recording:
                    # Commencer nouveau message utilisateur
                    self.is_recording = True
                    self.chat_history.append(["🎤 ...", None])
                
                return "🎤 Vous parlez...", self.format_chat()
                
            else:
                # Silence détecté
                if self.is_recording:
                    silence_time = current_time - self.last_speech_time
                    
                    if silence_time >= 2.0 and len(self.audio_buffer) > 0:
                        # 2 secondes de silence → traitement
                        self._process_final_audio(sample_rate)
                        return "⏳ IA génère...", self.format_chat()
                
                return "🔇 Silence", self.format_chat()
                
        except Exception as e:
            return f"❌ Erreur: {e}", self.format_chat()
    
    def _send_partial_transcript(self, sample_rate):
        try:
            # Prendre le dernier segment pour transcription partielle
            partial_audio = np.array(self.audio_buffer[-sample_rate:], dtype=np.float32)
            audio_bytes = self._array_to_wav_bytes(partial_audio, sample_rate)
            if len(audio_bytes) == 0:
                return
                
            audio_b64 = base64.b64encode(audio_bytes).decode()
            
            self.ws.send(json.dumps({
                "type": "audio_chunk",
                "data": audio_b64
            }))
            
            # Recevoir transcription partielle
            try:
                self.ws.settimeout(1)
                data = self.ws.recv()
                msg = json.loads(data)
                
                if msg["type"] == "partial_transcript":
                    # Mettre à jour ou ajouter transcription partielle
                    if self.chat_history and "📝" in str(self.chat_history[-1][0]):
                        self.chat_history[-1][0] = f"📝 En cours: {msg['text']}"
                    else:
                        self.chat_history.append([f"📝 En cours: {msg['text']}", None])
                        
            except:
                pass
                
        except Exception as e:
            print(f"Erreur transcription partielle: {e}")
    
    def _process_final_audio(self, sample_rate):
        try:
            # Audio complet
            full_audio = np.array(self.audio_buffer, dtype=np.float32)
            audio_bytes = self._array_to_wav_bytes(full_audio, sample_rate)
            audio_b64 = base64.b64encode(audio_bytes).decode()
            
            # Envoyer pour transcription finale + réponse IA
            self.ws.send(json.dumps({
                "type": "audio_final",
                "data": audio_b64
            }))
            
            # Attendre réponses
            responses = 0
            start_time = time.time()
            
            while responses < 2 and time.time() - start_time < 15:
                try:
                    self.ws.settimeout(3)
                    data = self.ws.recv()
                    msg = json.loads(data)
                    
                    if msg["type"] == "final_transcript":
                        # Mettre à jour le message utilisateur
                        if self.chat_history and self.chat_history[-1][1] is None:
                            self.chat_history[-1][0] = msg["text"]
                        responses += 1
                        
                    elif msg["type"] == "response":
                        # Ajouter réponse IA
                        if self.chat_history and self.chat_history[-1][1] is None:
                            self.chat_history[-1][1] = msg["text"]
                        responses += 1
                        break
                        
                except:
                    break
            
        except Exception as e:
            print(f"Erreur traitement final: {e}")
        finally:
            # Reset
            self.audio_buffer = []
            self.is_recording = False
    

    
    def _array_to_wav_bytes(self, audio_array, sample_rate):
        audio_array = np.array(audio_array, dtype=np.float32)
        if len(audio_array) == 0:
            return b""
        
        # Filtrage basique du bruit
        audio_level = np.max(np.abs(audio_array))
        if audio_level < 0.01:  # Trop faible = bruit
            return b""
            
        # Normalisation
        if audio_level > 1.0:
            audio_array = audio_array / audio_level
        audio_int16 = (audio_array * 32767).astype(np.int16)
        
        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF', 36 + len(audio_int16) * 2, b'WAVE', b'fmt ', 16,
            1, 1, sample_rate, sample_rate * 2, 2, 16, b'data', len(audio_int16) * 2)
        
        return header + audio_int16.tobytes()
    
    def format_chat(self):
        if not self.chat_history:
            return "💬 Conversation vide\n\nParlez dans le micro pour commencer..."
        
        result = ""
        for i, (user_msg, ai_msg) in enumerate(self.chat_history):
            result += f"👤 Vous: {user_msg}\n"
            if ai_msg:
                result += f"🤖 IA: {ai_msg}\n\n"
            else:
                result += "\n"
        return result.strip()
    
    def clear_chat(self):
        self.chat_history = []
        self.audio_buffer = []
        self.is_recording = False
        return self.format_chat()

agent = RealTimeAgent()

with gr.Blocks(title="Agent IA Temps Réel") as demo:
    gr.Markdown("# 🤖 Agent IA - Transcription Temps Réel")
    
    with gr.Row():
        backend_input = gr.Textbox(
            label="URL Backend", 
            placeholder="https://abc123.ngrok.io",
            value=""
        )
        connect_btn = gr.Button("Se connecter", variant="primary")
    
    status_text = gr.Textbox(label="Statut", value="Déconnecté", interactive=False)
    
    chat_display = gr.Textbox(label="Conversation", lines=15, interactive=False)
    
    with gr.Row():
        audio_input = gr.Audio(
            label="🎤 Parlez ici (transcription temps réel)", 
            sources=["microphone"],
            type="numpy",
            streaming=True
        )
        clear_btn = gr.Button("Effacer", variant="secondary")
    
    connect_btn.click(
        agent.connect_websocket,
        inputs=[backend_input],
        outputs=[status_text, chat_display]
    )
    
    audio_input.stream(
        agent.start_streaming,
        inputs=[audio_input],
        outputs=[status_text, chat_display]
    )
    
    clear_btn.click(
        agent.clear_chat,
        outputs=[chat_display]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)