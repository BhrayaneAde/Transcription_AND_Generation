import os
import torch
import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM
from faster_whisper import WhisperModel

# Configuration
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
if torch.cuda.is_available():
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
    if not whisper_model:
        load_models()
    
    try:
        if audio_file is None:
            return ""
        
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
        messages = [
            {"role": "system", "content": "Tu es un agent IA français intelligent. Réponds de manière précise et utile."}
        ]
        messages.extend(conversation_history[-6:])
        messages.append({"role": "user", "content": text})
        
        prompt = qwen_tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        inputs = qwen_tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = inputs.to("cuda")
        
        with torch.no_grad():
            outputs = qwen_model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True,
                pad_token_id=qwen_tokenizer.eos_token_id
            )
        
        response = qwen_tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:], 
            skip_special_tokens=True
        ).strip()
        
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

def process_audio(audio_file):
    """Pipeline: Audio → Texte → Réponse IA"""
    if audio_file is None:
        return "Aucun audio détecté"
    
    transcript = transcribe_audio(audio_file)
    if not transcript:
        return "Transcription échouée"
    
    print(f"👂 Utilisateur: '{transcript}'")
    
    response = generate_response(transcript)
    if not response:
        return f"**Vous:** {transcript}\n\n**Agent IA:** Erreur de génération"
    
    print(f"🤖 Agent IA: '{response}'")
    
    return f"**Vous:** {transcript}\n\n**Agent IA:** {response}"

def clear_history():
    """Effacer l'historique"""
    global conversation_history
    conversation_history.clear()
    return "Historique effacé !"

def create_interface():
    """Interface Gradio"""
    with gr.Blocks(title="Agent IA - Qwen 2.5 7B", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🤖 Agent IA avec Qwen 2.5 7B")
        gr.Markdown("**STT:** Faster Whisper Large v3 | **LLM:** Qwen 2.5 7B")
        
        with gr.Row():
            with gr.Column():
                audio_input = gr.Audio(
                    sources=["microphone"],
                    type="filepath",
                    label="🎙️ Parlez à l'agent IA"
                )
                
                with gr.Row():
                    submit_btn = gr.Button("🤖 Analyser", variant="primary")
                    clear_btn = gr.Button("🗑️ Effacer", variant="secondary")
            
            with gr.Column():
                text_output = gr.Markdown(
                    label="💬 Conversation",
                    value="Agent IA prêt à vous écouter !"
                )
        
        submit_btn.click(
            fn=process_audio,
            inputs=[audio_input],
            outputs=[text_output]
        )
        
        clear_btn.click(
            fn=clear_history,
            outputs=[text_output]
        )
    
    return interface

def main():
    """Lancement de l'agent IA"""
    print("🚀 Initialisation de l'agent IA...")
    print("📋 Chargement des modèles...")
    
    load_models()
    
    print("✅ Modèles prêts !")
    print("🌐 Lancement de l'interface...")
    
    interface = create_interface()
    interface.launch(
        share=False,
        server_name="127.0.0.1",
        server_port=7860,
        show_error=True
    )

if __name__ == "__main__":
    main()