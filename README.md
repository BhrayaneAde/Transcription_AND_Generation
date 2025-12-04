# 🎤 Chatbot Vocal - Qwen 2.5 7B + Whisper Large v3

Chatbot vocal intelligent utilisant les derniers modèles open-source :
- **STT** : Faster Whisper Large v3
- **LLM** : Qwen 2.5 7B Instruct (Hugging Face)
- **TTS** : Edge TTS
- **Interface** : Gradio

## 🚀 Lancement sur Google Colab

### Option 1 : Notebook Colab (Recommandé)
1. Ouvrez `colab_setup.ipynb` dans Google Colab
2. Exécutez les cellules dans l'ordre
3. L'interface Gradio se lancera automatiquement

### Option 2 : Script Python
1. Uploadez `colab_voice_chatbot.py` sur Colab
2. Installez les dépendances :
   ```python
   !pip install -r colab_requirements.txt
   ```
3. Lancez le script :
   ```python
   !python colab_voice_chatbot.py
   ```

## 💻 Installation Locale

```bash
pip install torch transformers faster-whisper gradio edge-tts pydub accelerate
python src/colab_voice_chatbot.py
```

## 🎯 Fonctionnalités

- ✅ Reconnaissance vocale haute précision (Whisper Large v3)
- ✅ Génération de texte avancée (Qwen 2.5 7B)
- ✅ Synthèse vocale naturelle (Edge TTS français)
- ✅ Interface web intuitive (Gradio)
- ✅ Historique de conversation
- ✅ Support GPU/CPU automatique

## 📋 Exemples d'utilisation

- "Bonjour, comment ça va ?"
- "Explique-moi la photosynthèse"
- "Raconte-moi une blague"
- "Quel temps fait-il aujourd'hui ?"