import psycopg2
import streamlit as st


def get_connection():
    """
    Établit une connexion à la base de données Neon PostgreSQL
    """
    try:
        conn = psycopg2.connect(
            host="ep-proud-silence-ahl7y2ul-pooler.c-3.us-east-1.aws.neon.tech",
            database="neondb",
            user="neondb_owner",
            password="npg_JR3ivIt9yMQK",
            port=5432,
            sslmode="require"  # IMPORTANT pour Neon
        )
        return conn
    except Exception as e:
        st.error(f"❌ Erreur de connexion PostgreSQL: {e}")
        return None


def test_connection():
    """
    Teste la connexion à la base de données
    """
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            cur.close()
            conn.close()
            return True
        except Exception as e:
            st.error(f"❌ Erreur lors du test: {e}")
            return False
    return False


def execute_query(query, params=None, fetch=False):
    """
    Exécute une requête SQL

    Args:
        query: Requête SQL
        params: Paramètres de la requête
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
            conn.close()
        return None if fetch else False