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

# Importer et lancer l'application
if __name__ == "__main__":
    import app