import gradio as gr
import websocket
import json
import base64
import threading
import time
import numpy as np
import struct

class RealTimeAgent:
    def __init__(self):
        self.ws = None
        self.backend_url = ""
        self.chat_history = []
        self.is_connected = False
        
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
    
    def send_audio(self, audio_data):
        if not self.is_connected or not self.ws:
            return "❌ Non connecté", self.format_chat()
            
        try:
            if audio_data is not None:
                sample_rate, audio_array = audio_data
                audio_bytes = self._array_to_wav_bytes(audio_array, sample_rate)
                audio_b64 = base64.b64encode(audio_bytes).decode()
                
                message = json.dumps({
                    "type": "audio",
                    "data": audio_b64
                })
                print(f"Envoi: {len(message)} caractères")
                self.ws.send(message)
                
                # Attendre les réponses
                start_time = time.time()
                while time.time() - start_time < 10:
                    try:
                        self.ws.settimeout(1)
                        data = self.ws.recv()
                        msg = json.loads(data)
                        
                        if msg["type"] == "transcript":
                            self.chat_history.append([msg["text"], "⏳ Génération..."])
                            return "📝 Transcription reçue", self.format_chat()
                        elif msg["type"] == "response":
                            if self.chat_history and "⏳" in str(self.chat_history[-1][1]):
                                self.chat_history[-1][1] = msg["text"]
                            return "✅ Réponse reçue", self.format_chat()
                            
                    except websocket.WebSocketTimeoutException:
                        continue
                    except Exception:
                        break
                
                return "✅ Message traité", self.format_chat()
                
        except Exception as e:
            return f"❌ Erreur: {e}", self.format_chat()
    
    def _array_to_wav_bytes(self, audio_array, sample_rate):
        audio_array = np.array(audio_array, dtype=np.float32)
        if audio_array.max() > 1.0 or audio_array.min() < -1.0:
            audio_array = audio_array / np.max(np.abs(audio_array))
        audio_int16 = (audio_array * 32767).astype(np.int16)
        
        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF', 36 + len(audio_int16) * 2, b'WAVE', b'fmt ', 16,
            1, 1, sample_rate, sample_rate * 2, 2, 16, b'data', len(audio_int16) * 2)
        
        return header + audio_int16.tobytes()
    
    def format_chat(self):
        return self.chat_history
    
    def clear_chat(self):
        self.chat_history = []
        return self.format_chat()

agent = RealTimeAgent()

with gr.Blocks(title="Agent IA Temps Réel") as demo:
    gr.Markdown("# 🤖 Agent IA - Discussion Temps Réel")
    
    with gr.Row():
        backend_input = gr.Textbox(
            label="URL Backend", 
            placeholder="https://abc123.ngrok.io",
            value=""
        )
        connect_btn = gr.Button("Se connecter", variant="primary")
    
    status_text = gr.Textbox(label="Statut", value="Déconnecté", interactive=False)
    
    chat_display = gr.Chatbot(label="Conversation", height=400)
    
    with gr.Row():
        audio_input = gr.Audio(
            label="🎤 Parlez ici", 
            sources=["microphone"],
            type="numpy"
        )
        clear_btn = gr.Button("Effacer", variant="secondary")
    
    connect_btn.click(
        agent.connect_websocket,
        inputs=[backend_input],
        outputs=[status_text, chat_display]
    )
    
    audio_input.change(
        agent.send_audio,
        inputs=[audio_input],
        outputs=[status_text, chat_display]
    )
    
    clear_btn.click(
        agent.clear_chat,
        outputs=[chat_display]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)