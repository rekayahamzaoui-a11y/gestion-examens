# frontend/db_utils.py
import streamlit as st
import psycopg2
from psycopg2 import Error
import time


def get_connection(retry=3):
    """Connexion à PostgreSQL avec retry automatique"""
    for attempt in range(retry):
        try:
            # En production sur Streamlit Cloud, utilise st.secrets
            if hasattr(st, 'secrets') and 'DB_HOST' in st.secrets:
                conn = psycopg2.connect(
                    host=st.secrets["DB_HOST"],
                    database=st.secrets["DB_NAME"],
                    user=st.secrets["DB_USER"],
                    password=st.secrets["DB_PASSWORD"],
                    port=st.secrets.get("DB_PORT", "5432"),
                    connect_timeout=10,
                    keepalives=1,
                    keepalives_idle=30,
                    keepalives_interval=10,
                    keepalives_count=5
                )
            else:
                # En local, utilise localhost
                conn = psycopg2.connect(
                    host="localhost",
                    database="gestion_examens_db",
                    user="postgres",
                    password="rekaya22",
                    port="5432"
                )
            return conn
        except Exception as e:
            if attempt < retry - 1:
                time.sleep(1)
                continue
            else:
                st.error(f"❌ Impossible de se connecter à la base après {retry} tentatives: {e}")
                return None


def test_connection():
    """Test de connexion"""
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            cur.close()
            conn.close()
            return True
        except:
            if conn:
                conn.close()
            return False
    return False


def execute_query(query, params=None, fetch=False):
    """
    Exécute une requête SQL avec gestion d'erreur

    Args:
        query: Requête SQL
        params: Paramètres de la requête (tuple)
        fetch: True pour SELECT, False pour INSERT/UPDATE/DELETE

    Returns:
        Résultats si fetch=True, sinon True/False
    """
    conn = get_connection()
    if not conn:
        return None if fetch else False

    try:
        cur = conn.cursor()

        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)

        if fetch:
            result = cur.fetchall()
            cur.close()
            conn.close()
            return result
        else:
            conn.commit()
            cur.close()
            conn.close()
            return True

    except Exception as e:
        st.error(f"❌ Erreur SQL: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return None if fetch else False