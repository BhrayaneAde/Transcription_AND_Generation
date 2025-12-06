# 🤖 Agent IA - Qwen 2.5 7B + Whisper Large v3

Agent IA intelligent avec architecture **Backend Colab + Frontend React** :
- **STT** : Faster Whisper Large v3
- **LLM** : Qwen 2.5 7B Instruct (4-bit)
- **Backend** : FastAPI sur Google Colab (GPU)
- **Frontend** : React TypeScript
- **Tunnel** : ngrok

## 🚀 Démarrage Rapide

### Backend (Google Colab)
1. **Ouvrez `colab_backend.ipynb` dans Google Colab**
2. **Activez le GPU** (Runtime → Change runtime type → GPU)
3. **Exécutez les cellules** - Les modèles se téléchargent automatiquement
4. **Copiez l'URL ngrok** affichée (ex: `https://abc123.ngrok-free.dev`)

### Frontend (Local)
```bash
cd frontend
npm install
npm start
```

1. **Ouvrez** http://localhost:3000
2. **Collez l'URL ngrok** du backend
3. **Cliquez "Connecter"**
4. **Parlez dans le micro** !

## 🎯 Fonctionnalités

- ✅ **Backend GPU** sur Google Colab (gratuit)
- ✅ **Frontend React** moderne et responsive
- ✅ **Reconnaissance vocale** haute précision (Whisper Large v3)
- ✅ **LLM avancé** (Qwen 2.5 7B quantifié 4-bit)
- ✅ **API REST** FastAPI avec CORS
- ✅ **Tunnel sécurisé** ngrok
- ✅ **Historique** de conversation
- ✅ **Interface TypeScript** intuitive
- ✅ **Décodage HTML** pour caractères spéciaux

## 🏗️ Architecture

```
[Micro Local] → [React Frontend] → [ngrok] → [Colab Backend] → [GPU Models]
     ↓              ↓                 ↓           ↓              ↓
   Audio         TypeScript        Tunnel     FastAPI      Whisper+Qwen
```

## 📋 Utilisation

1. **Parlez dans le micro** du frontend React
2. **L'audio est envoyé** au backend Colab via ngrok
3. **Whisper transcrit** votre parole
4. **Qwen génère** une réponse intelligente
5. **Le chat s'affiche** dans l'interface moderne

### Exemples de questions :
- "Bonjour, comment ça va ?"
- "Explique-moi la photosynthèse"
- "Raconte-moi une blague"
- "Quel temps fait-il aujourd'hui ?"

## 📖 Guide Détaillé

Consultez [DEMARRAGE.md](DEMARRAGE.md) pour un guide complet.

## 🔧 Configuration ngrok

Pour un tunnel stable :
1. Créez un compte sur [ngrok.com](https://ngrok.com)
2. Récupérez votre token
3. Dans le notebook Colab, remplacez :
   ```python
   NGROK_TOKEN = "VOTRE_TOKEN_ICI"
   ```

## 📁 Structure du Projet

```
Transcription_Nafiou/
├── colab_backend.ipynb    # Backend FastAPI + IA
├── frontend/              # Interface React TypeScript
│   ├── src/App.tsx       # Application principale
│   ├── src/App.css       # Styles
│   └── package.json      # Dépendances
├── DEMARRAGE.md          # Guide de démarrage
└── README.md             # Documentation
```

## 🆕 Dernières Améliorations

- ✅ Migration de Gradio vers React TypeScript
- ✅ Interface chat moderne avec bulles
- ✅ Correction du décodage HTML (caractères spéciaux)
- ✅ API REST simplifiée (/chat endpoint)
- ✅ Gestion d'erreurs améliorée
- ✅ Documentation complète