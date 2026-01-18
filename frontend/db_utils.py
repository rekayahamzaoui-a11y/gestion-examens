# frontend/db_utils.py
import streamlit as st
import psycopg2
from psycopg2 import Error

def get_connection():
    """Connexion à PostgreSQL (Neon en production, local en dev)"""
    try:
        # En production sur Streamlit Cloud, utilise st.secrets
        if hasattr(st, 'secrets') and 'DB_HOST' in st.secrets:
            conn = psycopg2.connect(
                host=st.secrets["DB_HOST"],
                database=st.secrets["DB_NAME"],
                user=st.secrets["DB_USER"],
                password=st.secrets["DB_PASSWORD"],
                port=st.secrets.get("DB_PORT", "5432")
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
    except Error as e:
        st.error(f"❌ Erreur de connexion PostgreSQL: {e}")
        return None

def test_connection():
    """Test de connexion"""
    conn = get_connection()
    if conn:
        conn.close()
        return True
    return False