# 👁️ Eye of God - Device Tracker

> Application de suivi et recherche d'appareils mobiles en temps réel avec Google Maps

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-orange.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Fonctionnalités

### Interface Web (Temps Réel)
- 🗺️ **Google Maps** - Carte interactive en temps réel
- 📡 **WebSocket** - Mises à jour live des positions
- 📱 **Gestion des appareils** - Ajouter, suivre, localiser
- 🔄 **Simulation GPS** - Test facile sans vrai appareil

### CLI (Ligne de Commande)
- 🔍 **Find Lost Device** - Recherche d'appareils perdus
- 📍 **Localisation IMEI/WiFi/Cellulaire**
- 📋 **Génération de rapports** pour la police

## 🚀 Installation

```bash
# Cloner le projet
git clone https://github.com/ivan-14-dev/eye-of-god.git
cd eye-of-god

# Installer les dépendances
pip install -r requirements.txt
```

## ⚙️ Configuration

1. **Copier le fichier de configuration**
```bash
cp .env.example .env
```

2. **Obtenir une clé Google Maps API**
   - Aller sur [Google Cloud Console](https://console.cloud.google.com/google/maps-apis)
   - Créer un projet et activer "Maps JavaScript API"
   - Générer une clé API

3. **Configurer la clé API**
   
   Dans [`backend/app.py`](backend/app.py), remplacer:
   ```javascript
   // YOUR_API_KEY
   ```
   par votre vraie clé:
   ```javascript
   // AIzaSy.....................
   ```

## 📖 Utilisation

### Interface Web (Recommandée)

```bash
python3 backend/app.py
```

Puis ouvrir: **http://localhost:5000**

| Identifiant | Mot de passe |
|-------------|--------------|
| test@example.com | test123 |

### Ligne de Commande

```bash
# Find Lost Device - Rechercher un téléphone perdu
python3 -m core.find_lost_device find --phone +33612345678

# Enregistrer un téléphone perdu
python3 -m core.find_lost_device register \
    --phone +33612345678 \
    --imei 123456789012345 \
    --name "Jean Dupont" \
    --device "iPhone 13"

# Générer un rapport pour la police
python3 -m core.find_lost_device report --phone +33612345678

# Device Tracker CLI
python3 -m core.device_tracker login test@example.com test123
python3 -m core.device_tracker list
python3 -m core.device_tracker track 1
```

## 📁 Structure du Projet

```
eye_of_go/
├── main.py                      # Point d'entrée principal
├── requirements.txt             # Dépendances Python
├── README.md                    # Ce fichier
├── .env.example                 # Exemple de configuration
├── config.json                  # Configuration API
├── backend/
│   ├── __init__.py
│   └── app.py                   # Serveur Flask + WebSocket
└── core/
    ├── __init__.py
    ├── logger.py                # Système de logging
    ├── device_tracker.py        # Module suivi d'appareils
    └── find_lost_device.py      # Module recherche
```

## 🔧 API Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/auth/login` | Connexion |
| GET | `/api/my-devices` | Liste des appareils |
| GET | `/api/device/{id}/location` | Localisation actuelle |
| POST | `/api/device/{id}/location` | Mettre à jour position |
| GET | `/api/device/{id}/history` | Historique |
| WebSocket | `/socket.io` | Temps réel |

## ⚠️ Avertissements

- Ce projet est à des fins éducatives
- L'utilisation doit être légale et respectueuse de la vie privée
- Certaines fonctionnalités nécessitent un appareil mobile réel

## 📝 License

MIT License - Voir [LICENSE](LICENSE)

---

Développé avec  par Ivan
