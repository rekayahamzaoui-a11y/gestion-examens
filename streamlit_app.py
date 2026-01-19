# streamlit_app.py
"""
Point d'entrée pour le déploiement Streamlit Cloud
"""
import sys
import os

# Ajouter le dossier frontend au path Python
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.join(current_dir, 'frontend')
sys.path.insert(0, frontend_path)

# ⚠️ CORRECTION : Exécuter le module app
import importlib
app = importlib.import_module('app')