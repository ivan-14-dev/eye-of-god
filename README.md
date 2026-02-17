# 👁️ Eye of God - Device Tracker

Un outil de suivi et de recherche d'appareils mobiles.

## 📋 Fonctionnalités

### Find Lost Device
- Recherche par IMEI
- Localisation par WiFi
- Localisation par tours cellulaires
- Génération de rapports pour la police
- Création de cartes interactives

### Device Tracker
- Authentification utilisateur
- Liste de vos appareils
- Suivi de localisation en temps réel
- Historique des localisations

## 🚀 Installation

```bash
# Cloner le projet
git clone <repo-url>
cd eye_of_go

# Installer les dépendances
pip install -r requirements.txt
```

## 📖 Utilisation

### Menu principal

```bash
python3 main.py
```

### Find Lost Device

```bash
# Rechercher un téléphone perdu
python3 -m core.find_lost_device find --phone +33612345678

# Enregistrer un téléphone perdu
python3 -m core.find_lost_device register \
    --phone +33612345678 \
    --imei 123456789012345 \
    --name "Nom du propriétaire" \
    --device "iPhone 13"

# Générer un rapport pour la police
python3 -m core.find_lost_device report --phone +33612345678

# Créer une carte interactive
python3 -m core.find_lost_device map --phone +33612345678

# Lister les appareils enregistrés
python3 -m core.find_lost_device list
```

### Device Tracker

```bash
# Se connecter
python3 -m core.device_tracker login email@example.com motdepasse

# Lister mes appareils
python3 -m core.device_tracker list

# Tracker un appareil
python3 -m core.device_tracker track 1

# Historique
python3 -m core.device_tracker history 1 --limit 50
```

## ⚙️ Configuration

Le fichier `config.json` est créé automatiquement avec les paramètres par défaut:

```json
{
  "google_api_key": "YOUR_GOOGLE_API_KEY",
  "apple_api_key": "YOUR_APPLE_API_KEY",
  "openstreetmap_api": "https://nominatim.openstreetmap.org",
  "mobilenumber_api": "https://api.mobilenumber.info",
  "imei_api": "https://api.imei.info"
}
```

## 📁 Structure

```
eye_of_go/
├── main.py                   # Point d'entrée
├── requirements.txt          # Dépendances
├── README.md                  # Ce fichier
├── config.json               # Configuration (auto-généré)
├── lost_devices.db          # Base de données (auto-généré)
└── core/
    ├── __init__.py
    ├── logger.py             # Système de logging
    ├── device_tracker.py     # Module de suivi d'appareils
    └── find_lost_device.py   # Module de recherche

# Backend (optionnel)
└── backend/
    ├── __init__.py
    └── app.py                # Serveur API Flask
```

## 🚀 Démarrage Rapide

### Interface Web (Recommandée)

```bash
# Installer les dépendances
pip install -r requirements.txt

# Démarrer le serveur
python3 backend/app.py
```

Ouvrez http://localhost:5000 dans votre navigateur.

**Important**: Remplacez `YOUR_API_KEY` dans [`backend/app.py`](backend/app.py) par votre clé API Google Maps.

### Utilisation CLI

## ⚠️ Avertissements

- Cet outil nécessite une connexion internet pour certaines fonctionnalités
- La localisation par IMEI nécessite un accès aux bases de données appropriée
- Utilisez cet outil de manière responsable et légale

## 📝 License

MIT License
