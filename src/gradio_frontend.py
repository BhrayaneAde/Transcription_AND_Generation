import gradio as gr
import requests
import tempfile
import os
import wave
import numpy as np

# Configuration
API_BASE_URL = "https://your-new-ngrok-url.ngrok.io"  # Remplacez par la nouvelle URL

def process_audio_with_api(audio_file, api_url):
    """Envoyer l'audio à l'API et récupérer la réponse"""
    if audio_file is None or audio_file == "":
        return "Aucun audio détecté. Essayez de recharger la page."
    
    try:
        # Gradio peut retourner un tuple (sample_rate, audio_data) ou un chemin
        if isinstance(audio_file, tuple):
            # Convertir le tuple en fichier WAV temporaire
            import wave
            import numpy as np
            
            sample_rate, audio_data = audio_file
            
            # Créer un fichier WAV temporaire
            temp_path = f"temp_audio_{int(np.random.random()*1000000)}.wav"
            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                if audio_data.dtype != np.int16:
                    audio_data = (audio_data * 32767).astype(np.int16)
                wav_file.writeframes(audio_data.tobytes())
            
            audio_file = temp_path
        
        # Vérifier que le fichier existe et n'est pas vide
        if not os.path.exists(audio_file):
            return "Fichier audio introuvable"
        
        file_size = os.path.getsize(audio_file)
        if file_size < 1000:  # Moins de 1KB
            return "Audio trop court ou vide. Vérifiez votre micro et réessayez."
        
        # Préparer le fichier pour l'envoi
        with open(audio_file, 'rb') as f:
            # Déterminer le type MIME basé sur l'extension
            if audio_file.endswith('.wav'):
                mime_type = 'audio/wav'
            elif audio_file.endswith('.mp3'):
                mime_type = 'audio/mpeg'
            else:
                mime_type = 'audio/wav'  # Par défaut
            
            files = {'file': (os.path.basename(audio_file), f, mime_type)}
            
            # Envoyer la requête à l'API
            response = requests.post(f"{api_url}/chat", files=files, timeout=60)
            
            # Nettoyer le fichier temporaire si créé
            if isinstance(audio_file, str) and audio_file.startswith("temp_audio_"):
                try:
                    os.unlink(audio_file)
                except:
                    pass
            
            if response.status_code == 200:
                data = response.json()
                transcript = data.get('transcript', '')
                ai_response = data.get('response', '')
                
                return f"**Vous:** {transcript}\n\n**Agent IA:** {ai_response}"
            else:
                return f"Erreur API: {response.status_code} - {response.text}"
                
    except requests.exceptions.RequestException as e:
        return f"Erreur de connexion: {str(e)}"
    except Exception as e:
        return f"Erreur: {str(e)}"

def clear_history_api(api_url):
    """Effacer l'historique via l'API"""
    try:
        response = requests.post(f"{api_url}/clear", timeout=10)
        if response.status_code == 200:
            return "Historique effacé !"
        else:
            return "Erreur lors de l'effacement"
    except:
        return "Erreur de connexion"

def update_api_url(new_url):
    """Mettre à jour l'URL de l'API"""
    global API_BASE_URL
    API_BASE_URL = new_url.strip().rstrip('/')
    return f"URL mise à jour: {API_BASE_URL}"

def test_connection(api_url):
    """Tester la connexion à l'API"""
    try:
        response = requests.get(f"{api_url}/", timeout=5)
        if response.status_code == 200:
            return "✅ Connexion réussie !"
        else:
            return f"❌ Erreur: {response.status_code}"
    except:
        return "❌ Impossible de se connecter"

def create_interface():
    """Interface Gradio pour le frontend"""
    
    with gr.Blocks(title="Agent IA Frontend") as interface:
        gr.Markdown("# 🤖 Agent IA - Frontend Local")
        gr.Markdown("**Frontend Gradio** connecté au **Backend Colab** (Qwen 2.5 7B + Whisper Large v3)")
        
        # Configuration de l'API
        with gr.Row():
            with gr.Column():
                gr.Markdown("### ⚙️ Configuration")
                api_url_input = gr.Textbox(
                    value=API_BASE_URL,
                    label="🌐 URL du serveur Colab",
                    placeholder="https://unoffensive-mana-eustatically.ngrok-free.dev"
                )
                
                with gr.Row():
                    update_btn = gr.Button("🔄 Mettre à jour", size="sm")
                    test_btn = gr.Button("🔍 Tester", size="sm")
                
                status_output = gr.Textbox(
                    label="📊 Statut",
                    value="✅ Backend configuré ! Cliquez sur 'Tester' pour vérifier",
                    interactive=False
                )
        
        gr.Markdown("---")
        
        # Interface principale
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 🎙️ Conversation")
                audio_input = gr.Audio(
                    label="🎙️ Enregistrez votre message"
                )
                
                with gr.Row():
                    submit_btn = gr.Button("🤖 Envoyer", variant="primary")
                    clear_btn = gr.Button("🗑️ Effacer", variant="secondary")
            
            with gr.Column():
                gr.Markdown("### 💬 Réponse")
                text_output = gr.Markdown(
                    label="Conversation",
                    value="Agent IA prêt à vous écouter !\n\n*Backend Colab connecté. Testez la connexion puis commencez à parler.*"
                )
        
        # Actions
        update_btn.click(
            fn=update_api_url,
            inputs=[api_url_input],
            outputs=[status_output]
        )
        
        test_btn.click(
            fn=test_connection,
            inputs=[api_url_input],
            outputs=[status_output]
        )
        
        submit_btn.click(
            fn=process_audio_with_api,
            inputs=[audio_input, api_url_input],
            outputs=[text_output]
        )
        
        clear_btn.click(
            fn=clear_history_api,
            inputs=[api_url_input],
            outputs=[text_output]
        )
    
    return interface

def main():
    """Lancement du frontend"""
    print("🚀 Lancement du frontend Agent IA...")
    print("🌐 Interface disponible sur: http://127.0.0.1:7860")
    print("📋 Configurez l'URL de votre serveur Colab dans l'interface")
    
    interface = create_interface()
    interface.launch(
        server_name="127.0.0.1",
        server_port=7860,
        show_error=True,
        share=False
    )

if __name__ == "__main__":
    main()