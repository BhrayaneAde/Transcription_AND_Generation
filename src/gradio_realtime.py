import gradio as gr
import websocket
import json
import base64
import threading
import time
from io import BytesIO
import numpy as np

class RealTimeAgent:
    def __init__(self):
        self.ws = None
        self.backend_url = ""
        self.chat_history = []
        self.is_connected = False
        
    def connect_websocket(self, backend_url):
        try:
            self.backend_url = backend_url
            ws_url = backend_url.replace('http', 'ws') + '/ws'
            self.ws = websocket.WebSocket()
            self.ws.connect(ws_url)
            self.is_connected = True
            return "✅ Connecté au backend", self.chat_history
        except Exception as e:
            self.is_connected = False
            return f"❌ Erreur: {e}", self.chat_history
    
    def send_audio(self, audio_data):
        if not self.is_connected or not self.ws:
            return "❌ Non connecté", self.chat_history
            
        try:
            # Convertir audio en base64
            if audio_data is not None:
                # Gradio audio format: (sample_rate, audio_array)
                sample_rate, audio_array = audio_data
                
                # Convertir en bytes WAV
                audio_bytes = self._array_to_wav_bytes(audio_array, sample_rate)
                audio_b64 = base64.b64encode(audio_bytes).decode()
                
                # Envoyer via WebSocket
                self.ws.send(json.dumps({
                    "type": "audio",
                    "data": audio_b64
                }))
                
                # Attendre les réponses
                transcript = ""
                response = ""
                
                # Timeout de 10 secondes
                start_time = time.time()
                while time.time() - start_time < 10:
                    try:
                        self.ws.settimeout(1)
                        data = self.ws.recv()
                        msg = json.loads(data)
                        
                        if msg["type"] == "transcript":
                            transcript = msg["text"]
                            self.chat_history.append(f"👤 Vous: {transcript}")
                        elif msg["type"] == "response":
                            response = msg["text"]
                            self.chat_history.append(f"🤖 IA: {response}")
                            break
                            
                    except websocket.WebSocketTimeoutException:
                        continue
                    except Exception as e:
                        break
                
                return "✅ Message traité", self.chat_history
                
        except Exception as e:
            return f"❌ Erreur: {e}", self.chat_history
    
    def _array_to_wav_bytes(self, audio_array, sample_rate):
        # Conversion simple numpy array vers WAV bytes
        audio_array = np.array(audio_array, dtype=np.float32)
        
        # Normaliser
        if audio_array.max() > 1.0 or audio_array.min() < -1.0:
            audio_array = audio_array / np.max(np.abs(audio_array))
        
        # Convertir en int16
        audio_int16 = (audio_array * 32767).astype(np.int16)
        
        # Header WAV simple
        import struct
        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF', 36 + len(audio_int16) * 2, b'WAVE', b'fmt ', 16,
            1, 1, sample_rate, sample_rate * 2, 2, 16, b'data', len(audio_int16) * 2)
        
        return header + audio_int16.tobytes()
    
    def clear_chat(self):
        self.chat_history = []
        return self.chat_history

# Instance globale
agent = RealTimeAgent()

# Interface Gradio
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
    
    # Events
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