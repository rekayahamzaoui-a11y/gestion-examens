# frontend/db_utils.py
import streamlit as st
import psycopg2
from psycopg2 import Error, OperationalError
import time
import os


def get_connection(retry=3):
    """
    Connexion à PostgreSQL avec retry automatique
    Compatible avec : Neon, Supabase, Render, localhost
    """

    for attempt in range(retry):
        try:
            # PRIORITÉ 1 : Streamlit Secrets (Cloud)
            if hasattr(st, 'secrets') and 'database' in st.secrets:

                # Méthode A : URL complète (Neon, Render)
                if 'url' in st.secrets['database']:
                    conn = psycopg2.connect(
                        st.secrets['database']['url'],
                        connect_timeout=15,
                        keepalives=1,
                        keepalives_idle=30,
                        keepalives_interval=10,
                        keepalives_count=5
                    )
                    if attempt == 0:
                        print(f"✅ Connexion via URL Streamlit Secrets")
                    return conn

                # Méthode B : Paramètres séparés
                else:
                    conn = psycopg2.connect(
                        host=st.secrets['database']['host'],
                        database=st.secrets['database']['database'],
                        user=st.secrets['database']['user'],
                        password=st.secrets['database']['password'],
                        port=st.secrets['database'].get('port', '5432'),
                        sslmode=st.secrets['database'].get('sslmode', 'require'),
                        connect_timeout=15,
                        keepalives=1,
                        keepalives_idle=30,
                        keepalives_interval=10,
                        keepalives_count=5
                    )
                    if attempt == 0:
                        print(f"✅ Connexion via paramètres Streamlit Secrets")
                    return conn

            # PRIORITÉ 2 : Variables d'environnement
            elif os.getenv('DATABASE_URL'):
                conn = psycopg2.connect(
                    os.getenv('DATABASE_URL'),
                    connect_timeout=15,
                    keepalives=1,
                    keepalives_idle=30,
                    keepalives_interval=10,
                    keepalives_count=5
                )
                if attempt == 0:
                    print(f"✅ Connexion via DATABASE_URL")
                return conn

            # PRIORITÉ 3 : Localhost (développement local)
            else:
                conn = psycopg2.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    database=os.getenv('DB_NAME', 'gestion_examens_db'),
                    user=os.getenv('DB_USER', 'postgres'),
                    password=os.getenv('DB_PASSWORD', 'rekaya22'),
                    port=os.getenv('DB_PORT', '5432'),
                    connect_timeout=10
                )
                if attempt == 0:
                    print(f"✅ Connexion locale")
                return conn

        except OperationalError as e:
            error_msg = str(e)

            if any(x in error_msg.lower() for x in
                   ['password', 'authentication', 'role', 'database', 'does not exist']):
                st.error(f"❌ Erreur de configuration : {e}")
                return None

            if attempt < retry - 1:
                wait_time = (attempt + 1) * 2
                print(f"⚠️ Tentative {attempt + 1}/{retry} échouée. Nouvelle tentative dans {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                st.error(f"❌ Impossible de se connecter après {retry} tentatives")
                st.error(f"Détails : {e}")
                return None

        except Exception as e:
            st.error(f"❌ Erreur inattendue : {e}")
            return None

    return None


def test_connection():
    """Test de connexion basique - VERSION SIMPLE"""
    conn = get_connection()
    if conn:
        print("✅ Connexion PostgreSQL réussie")
        conn.close()
        return True
    return False


def show_connection_config():
    """Affiche la configuration de connexion (sans mot de passe)"""

    st.subheader("🔧 Configuration de connexion")

    if hasattr(st, 'secrets') and 'database' in st.secrets:
        if 'url' in st.secrets['database']:
            url = st.secrets['database']['url']
            try:
                host = url.split('@')[1].split('/')[0]
                st.info(f"**Source:** Streamlit Secrets (URL)\n\n**Host:** `{host}`")
            except:
                st.info("**Source:** Streamlit Secrets (URL)")
        else:
            st.info(f"""
            **Source:** Streamlit Secrets (Paramètres)

            **Host:** `{st.secrets['database']['host']}`  
            **Database:** `{st.secrets['database']['database']}`  
            **User:** `{st.secrets['database']['user']}`  
            **SSL:** `{st.secrets['database'].get('sslmode', 'require')}`
            """)

    elif os.getenv('DATABASE_URL'):
        url = os.getenv('DATABASE_URL')
        try:
            host = url.split('@')[1].split('/')[0]
            st.info(f"**Source:** DATABASE_URL\n\n**Host:** `{host}`")
        except:
            st.info("**Source:** DATABASE_URL")

    else:
        st.info("""
        **Source:** Localhost (développement)

        **Host:** `localhost`  
        **Database:** `gestion_examens_db`
        """)