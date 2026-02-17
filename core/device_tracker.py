#!/usr/bin/env python3

import argparse
import requests
import json
from tabulate import tabulate
from datetime import datetime

class LegalTrackerCLI:
    """Interface CLI pour tracker consensuel"""
    
    def __init__(self, api_url="http://localhost:5000"):
        self.api_url = api_url
        self.token = None
    
    def login(self, email: str, password: str) -> bool:
        """
        Étape 1: Se connecter
        (Identifiez-vous AVANT de pouvoir accéder à des appareils)
        """
        print("🔐 Connexion...")
        
        response = requests.post(
            f"{self.api_url}/api/auth/login",
            json={'email': email, 'password': password}
        )
        
        if response.status_code == 200:
            self.token = response.json()['token']
            print(f"✅ Connecté en tant que {email}")
            return True
        else:
            print("❌ Email ou mot de passe incorrect")
            return False
    
    def list_devices(self) -> list:
        """
        Étape 2: Voir MES appareils
        (Vous ne voyez QUE vos propres appareils)
        """
        if not self.token:
            print("❌ Vous devez vous connecter d'abord")
            return []
        
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(
            f"{self.api_url}/api/my-devices",
            headers=headers
        )
        
        if response.status_code == 200:
            devices = response.json()['devices']
            
            print("\n📱 Vos appareils:")
            for device in devices:
                print(f"  ID: {device['id']}")
                print(f"    Nom: {device['name']}")
                print(f"    Type: {device['type']}\n")
            
            return devices
        else:
            print("❌ Erreur lors de la récupération des appareils")
            return []
    
    def track_device(self, device_id: int):
        """
        Étape 3: Tracker UN de mes appareils
        """
        if not self.token:
            print("❌ Vous devez vous connecter d'abord")
            return
        
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(
            f"{self.api_url}/api/device/{device_id}/location",
            headers=headers
        )
        
        if response.status_code == 200:
            location = response.json()
            
            print(f"\n📍 Localisation:")
            print(f"   Latitude: {location['latitude']}")
            print(f"   Longitude: {location['longitude']}")
            print(f"   Précision: {location['accuracy']}m")
            print(f"   Heure: {location['timestamp']}")
            
        elif response.status_code == 403:
            print("❌ Accès refusé")
            print("   Le propriétaire doit partager cet appareil avec vous")
        else:
            print("❌ Erreur:", response.json()['error'])
    
    def get_history(self, device_id: int, limit: int = 50):
        """Historique de localisation"""
        if not self.token:
            print("❌ Vous devez vous connecter d'abord")
            return
        
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(
            f"{self.api_url}/api/device/{device_id}/history?limit={limit}",
            headers=headers
        )
        
        if response.status_code == 200:
            history = response.json()['history']
            
            print(f"\n📜 Historique ({len(history)} entrées):")
            
            table = [
                [
                    h['timestamp'],
                    f"{h['latitude']:.4f}",
                    f"{h['longitude']:.4f}",
                    f"{h['accuracy']}m"
                ]
                for h in history[:10]
            ]
            
            print(tabulate(
                table,
                headers=['Heure', 'Latitude', 'Longitude', 'Précision']
            ))
        else:
            print("❌ Erreur:", response.json()['error'])

# ============ CLI ============

def main():
    parser = argparse.ArgumentParser(
        description="🔒 Device Tracker - Suivi d'appareils"
    )
    
    subparsers = parser.add_subparsers(dest='command')
    
    # Commande: login
    login_parser = subparsers.add_parser('login', help='Se connecter')
    login_parser.add_argument('email', help='Email')
    login_parser.add_argument('password', help='Mot de passe')
    
    # Commande: list
    subparsers.add_parser('list', help='Lister mes appareils')
    
    # Commande: track
    track_parser = subparsers.add_parser('track', help='Tracker un appareil')
    track_parser.add_argument('device_id', type=int, help='ID de l\'appareil')
    
    # Commande: history
    history_parser = subparsers.add_parser('history', help='Historique')
    history_parser.add_argument('device_id', type=int)
    history_parser.add_argument('--limit', type=int, default=50)
    
    args = parser.parse_args()
    
    tracker = LegalTrackerCLI()
    
    if args.command == 'login':
        tracker.login(args.email, args.password)
    
    elif args.command == 'list':
        tracker.list_devices()
    
    elif args.command == 'track':
        tracker.track_device(args.device_id)
    
    elif args.command == 'history':
        tracker.get_history(args.device_id, args.limit)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()