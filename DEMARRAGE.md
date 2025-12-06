# 🚀 Guide de Démarrage - Agent IA

## 📋 Prérequis
- Compte Google (pour Colab)
- Node.js installé localement
- Navigateur web moderne

## 🔧 Démarrage Backend (Google Colab)

### 1. Ouvrir le Backend
1. Allez sur [Google Colab](https://colab.research.google.com)
2. Ouvrez `colab_backend.ipynb`
3. **Activez le GPU** : Runtime → Change runtime type → GPU

### 2. Lancer le Backend
1. Exécutez la première cellule (installation)
2. Exécutez la deuxième cellule (serveur)
3. **Copiez l'URL ngrok** affichée (ex: `https://abc123.ngrok-free.dev`)

## 💻 Démarrage Frontend (Local)

### 1. Installation
```bash
cd frontend
npm install
```

### 2. Lancement
```bash
npm run dev
```

### 3. Configuration
1. Ouvrez http://localhost:3000
2. **Collez l'URL ngrok** du backend
3. Cliquez sur "Connecter"
4. **Testez** en parlant dans le micro !

## 🎯 Utilisation

1. **Parlez** dans le microphone
2. **Attendez** la transcription
3. **Lisez** la réponse de l'IA

### Exemples de questions :
- "Bonjour, comment ça va ?"
- "Explique-moi la photosynthèse"
- "Raconte-moi une blague"

## 🔧 Dépannage

### Backend ne démarre pas
- Vérifiez que le GPU est activé dans Colab
- Redémarrez le runtime si nécessaire

### Frontend ne se connecte pas
- Vérifiez que l'URL ngrok est correcte
- Testez l'URL dans le navigateur (doit afficher un JSON)

### Audio ne fonctionne pas
- Autorisez l'accès au microphone
- Vérifiez que votre micro fonctionne

## 📁 Structure du Projet
```
Transcription_Nafiou/
├── colab_backend.ipynb    # Backend FastAPI + IA
├── frontend/              # Interface React
│   ├── src/App.tsx       # Application principale
│   └── package.json      # Dépendances
└── README.md             # Documentation
```

## 🆘 Support
Si vous rencontrez des problèmes, vérifiez :
1. Les logs dans Colab
2. La console du navigateur (F12)
3. Que l'URL ngrok est bien copiée