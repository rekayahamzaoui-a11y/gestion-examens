# main.py
import psycopg2
import time
import os
import streamlit as st
from collections import defaultdict
from datetime import date

from benchmark.test_performance import benchmark


# ==========================================
# CONNEXION À LA BASE DE DONNÉES
# ==========================================
def get_connection():
    """
    Connexion à PostgreSQL qui fonctionne partout

    - En LOCAL: Utilise variables d'environnement ou valeurs par défaut
    - Sur STREAMLIT CLOUD: Utilise st.secrets
    """
    try:
        # MODE STREAMLIT (secrets.toml)
        if "database" in st.secrets:
            conn = psycopg2.connect(
                host=st.secrets["database"]["host"],
                port=int(st.secrets["database"]["port"]),
                database=st.secrets["database"]["database"],
                user=st.secrets["database"]["user"],
                password=st.secrets["database"]["password"],
                sslmode=st.secrets["database"].get("sslmode", "require"),
                connect_timeout=10
            )
            return conn

        # MODE LOCAL
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME", "gestion_examens_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            connect_timeout=5
        )
        return conn

    except psycopg2.OperationalError as e:
        st.error(f"❌ Erreur de connexion PostgreSQL : {e}")
        return None

    except Exception as e:
        st.error(f"❌ Erreur inattendue : {type(e).__name__} - {e}")
        return None


# ==========================================
# INSERTION DES DONNÉES
# ==========================================
def insert_initial_data():
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO DEPARTEMENT (nom, code) VALUES
        ('Informatique', 'INFO'),
        ('Mathématiques', 'MATH'),
        ('Physique', 'PHYS')
        ON CONFLICT DO NOTHING;
        """)

        cur.execute("""
        INSERT INTO FORMATION (nom, niveau, id_dept) VALUES
        ('Licence Info', 'L1', 1),
        ('Licence Math', 'L1', 2),
        ('Master Physique', 'M2', 3)
        ON CONFLICT DO NOTHING;
        """)

        cur.execute("""
        INSERT INTO ETUDIANT (nom, prenom, email, promo, id_form) VALUES
        ('Ali', 'Benali', 'ali@mail.com', '2025', 1),
        ('Sara', 'Khaled', 'sara@mail.com', '2025', 1),
        ('Omar', 'Ahmed', 'omar@mail.com', '2025', 2)
        ON CONFLICT DO NOTHING;
        """)

        cur.execute("""
        INSERT INTO MODULE (nom, credits, coefficient, id_form) VALUES
        ('Algorithmique', 5, 1.5, 1),
        ('Base de données', 4, 1.2, 1),
        ('Analyse', 6, 1.8, 2)
        ON CONFLICT DO NOTHING;
        """)

        cur.execute("""
        INSERT INTO PROFESSEUR (nom, prenom, email, specialite, id_dept) VALUES
        ('Fares', 'Slim', 'fares@mail.com', 'Info', 1),
        ('Nadia', 'Ali', 'nadia@mail.com', 'Math', 2)
        ON CONFLICT DO NOTHING;
        """)

        cur.execute("""
        INSERT INTO LIEU_EXAMEN (nom, capacite, type_lieu, batiment, equipements) VALUES
        ('Amphi A', 50, 'amphi', 'Batiment 1', 'Projecteur, Tableau'),
        ('Salle TD 1', 30, 'salle_TD', 'Batiment 2', 'Tableau, Ordinateurs')
        ON CONFLICT DO NOTHING;
        """)

        cur.execute("""
        INSERT INTO EXAMEN (date_exam, duree_min, type_examen, session_examen, id_mod, id_lieu) VALUES
        ('2025-12-27 09:00', 90, 'partiel', 'S1', 1, 1),
        ('2025-12-28 14:00', 120, 'partiel', 'S1', 2, 1),
        ('2025-12-29 10:00', 60, 'partiel', 'S1', 3, 2)
        ON CONFLICT DO NOTHING;
        """)

        cur.execute("""
        INSERT INTO INSCRIPTION (id_etu, id_mod, note, statut) VALUES
        (1, 1, NULL, 'inscrit'),
        (2, 1, NULL, 'inscrit'),
        (3, 3, NULL, 'inscrit')
        ON CONFLICT DO NOTHING;
        """)

        cur.execute("""
        INSERT INTO SURVEILLANCE (id_prof, id_exam, role) VALUES
        (1, 1, 'principal'),
        (1, 2, 'assistant'),
        (2, 3, 'principal')
        ON CONFLICT DO NOTHING;
        """)

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        st.error(f"❌ Erreur insertion : {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()


# ==========================================
# PROGRAMME PRINCIPAL STREAMLIT
# ==========================================
def main():
    st.title("📘 Système de gestion des examens")

    if st.button("🔌 Tester la connexion"):
        conn = get_connection()
        if conn:
            st.success("✅ Connexion réussie")
            conn.close()

    if st.button("📝 Insérer les données initiales"):
        insert_initial_data()
        st.success("✅ Données insérées")

    if st.button("📊 Benchmark"):
        benchmark()
        st.success("✅ Benchmark terminé")


if __name__ == "__main__":
    main()
