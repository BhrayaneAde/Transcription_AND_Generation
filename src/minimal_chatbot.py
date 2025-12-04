import os
import sys
import tempfile
import wave
import numpy as np
import asyncio
from typing import Generator, Tuple

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports essentiels
from fastrtc import AlgoOptions, ReplyOnPause, Stream
from faster_whisper import WhisperModel
import ollama
import edge_tts
from pydub import AudioSegment
from loguru import logger

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Configuration minimale
WHISPER_MODEL = "medium"
OLLAMA_MODEL = "gemma3:1b"

# Variables globales
whisper_model = None
conversation_history = []

def load_models():
    """Charger les modèles une seule fois"""
    global whisper_model
    if whisper_model is None:
        logger.info("🔄 Chargement des modèles...")
        whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        logger.info("✅ Modèles chargés")

def transcribe_audio(audio_data: tuple[int, np.ndarray]) -> str:
    """STT avec Faster Whisper"""
    load_models()
    
    try:
        sample_rate, audio = audio_data
        
        # Preprocessing minimal
        if audio.ndim > 1 and audio.shape[0] == 1:
            audio = audio[0]
        
        if len(audio) == 0 or len(audio) / sample_rate < 0.1:
            return ""
        
        # Normaliser
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))
        
        # Transcription
        temp_path = f"temp_{int(np.random.random()*1000000)}.wav"
        with wave.open(temp_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            audio_int16 = (audio * 32767).astype(np.int16)
            wav_file.writeframes(audio_int16.tobytes())
        
        segments, _ = whisper_model.transcribe(temp_path, language="fr", vad_filter=False)
        
        transcript = ""
        for segment in segments:
            transcript += segment.text.strip() + " "
        
        os.unlink(temp_path)
        return transcript.strip()
        
    except Exception as e:
        logger.error(f"Erreur STT: {e}")
        return ""

def generate_response(text: str) -> str:
    """LLM avec Ollama"""
    global conversation_history
    
    if not text:
        return ""
    
    try:
        # Construire messages
        messages = [{"role": "system", "content": "Tu es un assistant vocal français. Réponds de manière concise et naturelle."}]
        messages.extend(conversation_history[-6:])  # 3 derniers échanges
        messages.append({"role": "user", "content": text})
        
        # Appel Ollama
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={"temperature": 0.7, "max_tokens": 100}
        )
        
        assistant_response = response['message']['content'].strip()
        
        # Ajouter à l'historique
        conversation_history.extend([
            {"role": "user", "content": text},
            {"role": "assistant", "content": assistant_response}
        ])
        
        # Limiter l'historique
        if len(conversation_history) > 12:
            conversation_history = conversation_history[-12:]
        
        return assistant_response
        
    except Exception as e:
        logger.error(f"Erreur LLM: {e}")
        return "Je rencontre un problème technique."

async def synthesize_speech(text: str) -> str:
    """TTS avec Edge TTS"""
    try:
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        communicate = edge_tts.Communicate(text, "fr-FR-DeniseNeural")
        await communicate.save(temp_path)
        
        return temp_path if os.path.exists(temp_path) else None
        
    except Exception as e:
        logger.error(f"Erreur TTS: {e}")
        return None

def text_to_speech(text: str) -> Generator[Tuple[int, np.ndarray], None, None]:
    """Conversion texte vers audio"""
    try:
        # Edge TTS
        mp3_path = asyncio.run(synthesize_speech(text))
        
        if mp3_path:
            # Convertir MP3 vers WAV
            audio_segment = AudioSegment.from_mp3(mp3_path)
            wav_path = mp3_path.replace('.mp3', '.wav')
            audio_segment.export(wav_path, format="wav")
            
            # Lire WAV
            with wave.open(wav_path, 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                frames = wav_file.readframes(-1)
                audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Nettoyer
            os.unlink(mp3_path)
            os.unlink(wav_path)
            
            yield (sample_rate, audio_data)
        else:
            # Silence en cas d'erreur
            yield (16000, np.zeros(8000, dtype=np.float32))
            
    except Exception as e:
        logger.error(f"Erreur synthèse: {e}")
        yield (16000, np.zeros(8000, dtype=np.float32))

def chat_handler(audio: tuple[int, np.ndarray]) -> Generator[Tuple[int, np.ndarray], None, None]:
    """Handler principal du chatbot"""
    
    # STT
    transcript = transcribe_audio(audio)
    if not transcript:
        return
    
    logger.info(f"👂 '{transcript}'")
    
    # LLM
    response = generate_response(transcript)
    if not response:
        return
    
    logger.info(f"💬 '{response}'")
    
    # TTS
    yield from text_to_speech(response)

def main():
    """Lancement du chatbot minimal"""
    logger.info("🚀 Chatbot vocal minimal")
    logger.info("📋 STT: Faster Whisper | LLM: Ollama | TTS: Edge TTS")
    
    stream = Stream(
        modality="audio",
        mode="send-receive",
        handler=ReplyOnPause(
            chat_handler,
            algo_options=AlgoOptions(speech_threshold=0.6)
        )
    )
    
    logger.info("🌐 Interface: http://127.0.0.1:7862")
    stream.ui.launch()

if __name__ == "__main__":
    main()