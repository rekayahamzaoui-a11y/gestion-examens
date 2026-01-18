# 📚 Système de Gestion d'Examens Universitaires

Application web pour la planification automatique des emplois du temps d'examens.

##  Fonctionnalités

-  Génération automatique d'emplois du temps avec OR-Tools
- Gestion des étudiants (1300+), professeurs, salles
-  Respect automatique des contraintes métier
-  Tableaux de bord et statistiques interactifs
-  Authentification multi-rôles (Admin, Prof, Étudiant)
-  Export des plannings en CSV

##  Identifiants de Test

### 👑 Administrateur
- **Identifiant :** `admin`
- **Mot de passe :** `admin123`
- **Accès :** Toutes les fonctionnalités

### 👨‍🏫 Professeur
- **Identifiant :** `prof1`
- **Mot de passe :** `prof123`
- **Accès :** Consultation des examens et étudiants

### 👨‍🎓 Étudiant
- **Identifiant :** `etu1`
- **Mot de passe :** `etu123`
- **Accès :** Consultation de ses propres examens et notes

## 🚀 Installation Locale
```bash
# Cloner le projet
git clone https://github.com/VOTRE_USERNAME/gestion-examens.git
cd gestion-examens

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run streamlit_app.py
```

##  Base de Données

- **SGBD :** PostgreSQL 16
- **Tables :** 10 tables (étudiants, professeurs, salles, examens, etc.)
- **Données :** 
  - 1300+ étudiants
  - 100 modules
  - 30 salles
  - 40 professeurs
  - 4 départements (Informatique, Mathématiques, Biologie, Physique)

##  Technologies Utilisées

- **Frontend :** Streamlit
- **Backend :** Python 3.10+
- **Base de données :** PostgreSQL
- **Optimisation :** OR-Tools (Google)
- **Visualisation :** Plotly, Matplotlib, Seaborn

##  Architecture
```
projet_examens/
├── frontend/           # Interface utilisateur
│   ├── app.py         # Application principale
│   ├── auth.py        # Authentification
│   ├── db.py          # Connexion BDD
│   ├── queries.py     # Requêtes SQL
│   ├── dashboards.py  # Graphiques
│   ├── users_db.py    # Gestion utilisateurs
│   └── scheduler_engine.py  # Moteur de planification
├── .streamlit/
│   └── config.toml    # Configuration Streamlit
└── streamlit_app.py   # Point d'entrée
```

##  Auteur

Projet réalisé dans le cadre du module BDDA par Hamzaoui Rekaya,Sarah et Hamlil Friel.

##  Licence

MIT License