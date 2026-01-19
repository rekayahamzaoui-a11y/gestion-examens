# test_db_simple.py
import streamlit as st
from db_utils import get_connection

st.title("🧪 Test Connexion Neon")

if st.button("Tester"):
    conn = get_connection()

    if conn:
        st.success("✅ CONNEXION RÉUSSIE !")

        cur = conn.cursor()

        # Compter les tables
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        nb_tables = cur.fetchone()[0]

        # Compter les étudiants
        try:
            cur.execute("SELECT COUNT(*) FROM ETUDIANT;")
            nb_etu = cur.fetchone()[0]
        except:
            nb_etu = 0

        col1, col2 = st.columns(2)
        col1.metric("📊 Tables", nb_tables)
        col2.metric("👥 Étudiants", nb_etu)

        cur.close()
        conn.close()
    else:
        st.error("❌ ÉCHEC CONNEXION")

        st.warning("Vérifiez votre fichier `.streamlit/secrets.toml`")