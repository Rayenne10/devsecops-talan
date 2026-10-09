#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test-openai.py
Script de test unitaire pour valider la connexion à l'API OpenAI.
Chargement du fichier .env corrigé avec un chemin absolu (Correction #8).
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

# calcul du chemin absolu du projet (Correction #8)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# initialisation du client avec la clé récupérée du .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    log_info = "Tentative de connexion à OpenAI..."
    print(log_info)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Dit bonjour en un mot."}],
        max_tokens=10
    )
    print("✅ Connexion OpenAI réussie !")
    print("Réponse de l'IA :", response.choices[0].message.content.strip())
except Exception as e:
    print("❌ Erreur de connexion OpenAI :", e)
