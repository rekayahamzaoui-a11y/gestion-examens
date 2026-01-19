# streamlit_app.py
import sys
import os

# Ajouter frontend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'frontend'))

# Exécuter app.py
exec(open('frontend/app.py').read())