# 🤖 Agent IA - Qwen 2.5 7B + Whisper Large v3

Agent IA intelligent avec architecture **Backend Colab + Frontend Local** :
- **STT** : Faster Whisper Large v3
- **LLM** : Qwen 2.5 7B Instruct (4-bit)
- **Backend** : FastAPI sur Google Colab (GPU)
- **Frontend** : Gradio local
- **Tunnel** : ngrok

## 🚀 Déploiement Backend (Google Colab)

1. **Ouvrez `colab_backend.ipynb` dans Google Colab**
2. **Activez le GPU** (Runtime → Change runtime type → GPU)
3. **Exécutez la cellule** - Les modèles se téléchargent automatiquement
4. **Copiez l'URL ngrok** affichée (ex: `https://abc123.ngrok.io`)

## 💻 Lancement Frontend (Local)

```bash
# Installation
pip install -r requirements_frontend.txt

# Lancement
python src/gradio_frontend.py
```

1. **Ouvrez** http://127.0.0.1:7860
2. **Collez l'URL ngrok** du backend Colab
3. **Testez la connexion**
4. **Commencez à parler** à l'agent IA !

## 🎯 Fonctionnalités

- ✅ **Backend GPU** sur Google Colab (gratuit)
- ✅ **Frontend local** responsive
- ✅ **Reconnaissance vocale** haute précision (Whisper Large v3)
- ✅ **LLM avancé** (Qwen 2.5 7B quantifié 4-bit)
- ✅ **API REST** FastAPI avec CORS
- ✅ **Tunnel sécurisé** ngrok
- ✅ **Historique** de conversation
- ✅ **Interface intuitive** Gradio

## 🏗️ Architecture

```
[Micro Local] → [Gradio Frontend] → [ngrok] → [Colab Backend] → [GPU Models]
     ↓              ↓                  ↓           ↓              ↓
   Audio         Interface          Tunnel     FastAPI      Whisper+Qwen
```

## 📋 Utilisation

1. **Parlez dans le micro** du frontend local
2. **L'audio est envoyé** au backend Colab via ngrok
3. **Whisper transcrit** votre parole
4. **Qwen génère** une réponse intelligente
5. **Le texte s'affiche** dans l'interface locale

### Exemples de questions :
- "Bonjour, comment ça va ?"
- "Explique-moi la photosynthèse"
- "Raconte-moi une blague"
- "Quel temps fait-il aujourd'hui ?"

## 🔧 Configuration ngrok

Pour un tunnel stable :
1. Créez un compte sur [ngrok.com](https://ngrok.com)
2. Récupérez votre token
3. Dans le notebook Colab, remplacez :
   ```python
   ngrok.set_auth_token("YOUR_NGROK_TOKEN")
   ```