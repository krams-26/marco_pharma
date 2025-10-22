#!/usr/bin/env python3
"""
Script pour générer une SECRET_KEY sécurisée pour Flask
Utilisez cette clé dans votre fichier .env
"""

import secrets

def generate_secret_key(length=50):
    """Génère une clé secrète sécurisée"""
    return secrets.token_urlsafe(length)

if __name__ == '__main__':
    print("=" * 70)
    print("GÉNÉRATION D'UNE SECRET_KEY SÉCURISÉE POUR FLASK")
    print("=" * 70)
    print()
    print("Copiez cette clé dans votre fichier .env :")
    print()
    print(f"SECRET_KEY={generate_secret_key()}")
    print()
    print("=" * 70)
    print("⚠️  IMPORTANT : Ne partagez JAMAIS cette clé avec personne !")
    print("=" * 70)

