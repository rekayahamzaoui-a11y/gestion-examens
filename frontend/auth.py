# frontend/auth.py
import streamlit as st
from users_db import verify_user


def init_session_state():
    """Initialise les variables de session"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None


def login_page():
    """Page de connexion"""
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background-color: #f0f2f6;
            border-radius: 10px;
            margin-top: 5rem;
        }
        .login-title {
            text-align: center;
            color: #1f77b4;
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<p class="login-title">🔐 Connexion</p>', unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("👤 Nom d'utilisateur", placeholder="Entrez votre identifiant")
            password = st.text_input("🔑 Mot de passe", type="password", placeholder="Entrez votre mot de passe")

            submit = st.form_submit_button("Se connecter", use_container_width=True)

            if submit:
                if username and password:
                    # ✅ CORRECTION: Passer le mot de passe EN CLAIR
                    # verify_user() fait le hash en interne
                    user = verify_user(username.strip(), password.strip())

                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.success(f"✅ Bienvenue {user['prenom']} {user['nom']} !")
                        st.rerun()
                    else:
                        st.error("❌ Identifiants incorrects")
                else:
                    st.warning("⚠️ Veuillez remplir tous les champs")

        st.markdown('</div>', unsafe_allow_html=True)

        # Informations de connexion par défaut
        with st.expander("ℹ️ Comptes de test"):
            st.info("""
            **Administrateur :**
            - Identifiant : `admin`
            - Mot de passe : `admin123`

            **Professeur :**
            - Identifiant : `prof1`
            - Mot de passe : `prof123`

            **Étudiant :**
            - Identifiant : `etu1`
            - Mot de passe : `etu123`
            """)


def logout():
    """Déconnexion"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()


def require_auth(allowed_roles=None):
    """Vérifie l'authentification et les permissions"""
    if not st.session_state.authenticated:
        return False

    if allowed_roles:
        if st.session_state.user['role'] not in allowed_roles:
            st.error(f"❌ Accès refusé. Rôle requis : {', '.join(allowed_roles)}")
            return False

    return True


def get_current_user():
    """Retourne l'utilisateur connecté"""
    return st.session_state.user if st.session_state.authenticated else None


def update_last_login(username):
    """Fonction vide - déjà géré par verify_user()"""
    pass