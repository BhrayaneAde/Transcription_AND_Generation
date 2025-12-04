import os
import tempfile
import wave
import numpy as np
import asyncio
import torch
from typing import Generator, Tuple
import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM
from faster_whisper import WhisperModel
import edge_tts
from pydub import AudioSegment

# Configuration pour Colab
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
torch.cuda.empty_cache()

# Configuration des modèles
WHISPER_MODEL = "large-v3"
QWEN_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# Variables globales
whisper_model = None
qwen_tokenizer = None
qwen_model = None
conversation_history = []

def load_models():
    """Charger les modèles une seule fois"""
    global whisper_model, qwen_tokenizer, qwen_model
    
    if whisper_model is None:
        print("🔄 Chargement Whisper Large v3...")
        whisper_model = WhisperModel(
            WHISPER_MODEL, 
            device="cuda" if torch.cuda.is_available() else "cpu",
            compute_type="float16" if torch.cuda.is_available() else "int8"
        )
        print("✅ Whisper chargé")
    
    if qwen_tokenizer is None or qwen_model is None:
        print("🔄 Chargement Qwen 2.5 7B...")
        qwen_tokenizer = AutoTokenizer.from_pretrained(QWEN_MODEL)
        qwen_model = AutoModelForCausalLM.from_pretrained(
            QWEN_MODEL,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True
        )
        print("✅ Qwen chargé")

def transcribe_audio(audio_file) -> str:
    """STT avec Faster Whisper Large v3"""
    load_models()
    
    try:
        if audio_file is None:
            return ""
        
        # Transcription directe du fichier
        segments, _ = whisper_model.transcribe(
            audio_file, 
            language="fr", 
            vad_filter=True,
            beam_size=5
        )
        
        transcript = ""
        for segment in segments:
            transcript += segment.text.strip() + " "
        
        return transcript.strip()
        
    except Exception as e:
        print(f"Erreur STT: {e}")
        return ""

def generate_response(text: str) -> str:
    """LLM avec Qwen 2.5 7B"""
    global conversation_history
    
    if not text:
        return ""
    
    try:
        # Construire le prompt
        messages = [
            {"role": "system", "content": "Tu es un assistant vocal français. Réponds de manière concise et naturelle."}
        ]
        messages.extend(conversation_history[-6:])
        messages.append({"role": "user", "content": text})
        
        # Formatage du prompt
        prompt = qwen_tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        # Tokenisation
        inputs = qwen_tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")
        
        # Génération
        with torch.no_grad():
            outputs = qwen_model.generate(
                **inputs,
                max_new_tokens=150,
                temperature=0.7,
                do_sample=True,
                pad_token_id=qwen_tokenizer.eos_token_id
            )
        
        # Décodage
        response = qwen_tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:], 
            skip_special_tokens=True
        ).strip()
        
        # Mise à jour historique
        conversation_history.extend([
            {"role": "user", "content": text},
            {"role": "assistant", "content": response}
        ])
        
        if len(conversation_history) > 12:
            conversation_history = conversation_history[-12:]
        
        return response
        
    except Exception as e:
        print(f"Erreur LLM: {e}")
        return "Je rencontre un problème technique."

async def synthesize_speech(text: str) -> str:
    """TTS avec Edge TTS"""
    try:
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        communicate = edge_tts.Communicate(text, "fr-FR-DeniseNeural")
        await communicate.save(temp_path)
        
        return temp_path if os.path.exists(temp_path) else None
        
    except Exception as e:
        print(f"Erreur TTS: {e}")
        return None

def process_audio(audio_file):
    """Pipeline principal: Audio → Texte → Réponse → Audio"""
    if audio_file is None:
        return None, "Aucun audio détecté"
    
    # STT
    transcript = transcribe_audio(audio_file)
    if not transcript:
        return None, "Transcription échouée"
    
    print(f"👂 Utilisateur: '{transcript}'")
    
    # LLM
    response = generate_response(transcript)
    if not response:
        return None, transcript
    
    print(f"💬 Assistant: '{response}'")
    
    # TTS
    try:
        audio_path = asyncio.run(synthesize_speech(response))
        return audio_path, f"**Vous:** {transcript}\n\n**Assistant:** {response}"
    except Exception as e:
        print(f"Erreur synthèse: {e}")
        return None, f"**Vous:** {transcript}\n\n**Assistant:** {response}"

def create_interface():
    """Interface Gradio pour Colab"""
    
    with gr.Blocks(title="Chatbot Vocal - Qwen 2.5 7B", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🎤 Chatbot Vocal avec Qwen 2.5 7B")
        gr.Markdown("**STT:** Faster Whisper Large v3 | **LLM:** Qwen 2.5 7B | **TTS:** Edge TTS")
        
        with gr.Row():
            with gr.Column():
                audio_input = gr.Audio(
                    sources=["microphone"],
                    type="filepath",
                    label="🎙️ Enregistrez votre message"
                )
                
                submit_btn = gr.Button("💬 Traiter", variant="primary")
                clear_btn = gr.Button("🗑️ Effacer historique", variant="secondary")
            
            with gr.Column():
                audio_output = gr.Audio(
                    label="🔊 Réponse audio",
                    autoplay=True
                )
                
                text_output = gr.Markdown(
                    label="📝 Conversation",
                    value="Prêt à discuter !"
                )
        
        # Actions
        submit_btn.click(
            fn=process_audio,
            inputs=[audio_input],
            outputs=[audio_output, text_output]
        )
        
        clear_btn.click(
            fn=lambda: (None, "Historique effacé !"),
            outputs=[audio_output, text_output]
        ).then(
            fn=lambda: conversation_history.clear()
        )
    
    return interface

def main():
    """Lancement pour Google Colab"""
    print("🚀 Initialisation du chatbot vocal...")
    print("📋 Chargement des modèles (peut prendre quelques minutes)...")
    
    # Pré-chargement des modèles
    load_models()
    
    print("✅ Modèles prêts !")
    print("🌐 Lancement de l'interface Gradio...")
    
    # Interface Gradio
    interface = create_interface()
    
    # Lancement public pour Colab
    interface.launch(
        share=True,
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True
    )

if __name__ == "__main__":
    main()