# main.py - VERSION FINALE COMPLÈTE
"""
Système de Gestion des Examens Universitaires
Avec pagination complète pour données lourdes
"""

import streamlit as st
import psycopg2
import pandas as pd
import os
import time
from datetime import datetime, timedelta

# ==========================================
# CONFIGURATION PAGE
# ==========================================
st.set_page_config(
    page_title="Gestion Examens",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================
# CONNEXION À LA BASE DE DONNÉES
# ==========================================
@st.cache_resource
def get_database_connection():
    """Connexion PostgreSQL (local ou Neon.tech)"""
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            # MODE PRODUCTION (Streamlit Cloud)
            if hasattr(st, 'secrets') and 'database' in st.secrets:
                conn = psycopg2.connect(
                    host=st.secrets["database"]["host"],
                    port=int(st.secrets["database"]["port"]),
                    database=st.secrets["database"]["dbname"],
                    user=st.secrets["database"]["user"],
                    password=st.secrets["database"]["password"],
                    sslmode=st.secrets["database"].get("sslmode", "require"),
                    connect_timeout=10
                )

                # Test connexion
                cur = conn.cursor()
                cur.execute("SELECT 1")
                cur.close()

                return conn

            # MODE LOCAL
            else:
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="gestion_examens_db",
                    user="postgres",
                    password="postgres",
                    connect_timeout=5
                )
                return conn

        except Exception as e:
            if attempt < max_retries:
                time.sleep(2)
            else:
                st.error(f"❌ Connexion impossible après {max_retries} tentatives: {e}")
                return None

    return None


# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================

def create_pagination(total_items, items_per_page, page_key="page"):
    """Crée les contrôles de pagination"""
    nb_pages = max(1, (total_items + items_per_page - 1) // items_per_page)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        page_actuelle = st.number_input(
            f"Page (sur {nb_pages})",
            min_value=1,
            max_value=nb_pages,
            value=st.session_state.get(page_key, 1),
            key=f"page_{page_key}"
        )

    st.session_state[page_key] = page_actuelle
    offset = (page_actuelle - 1) * items_per_page

    # Boutons navigation
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if page_actuelle > 1 and st.button("⏮️ Première", key=f"first_{page_key}"):
            st.session_state[page_key] = 1
            st.rerun()

    with col2:
        if page_actuelle > 1 and st.button("◀️ Préc", key=f"prev_{page_key}"):
            st.session_state[page_key] = page_actuelle - 1
            st.rerun()

    with col3:
        if page_actuelle < nb_pages and st.button("Suiv ▶️", key=f"next_{page_key}"):
            st.session_state[page_key] = page_actuelle + 1
            st.rerun()

    with col4:
        if page_actuelle < nb_pages and st.button("Dernière ⏭️", key=f"last_{page_key}"):
            st.session_state[page_key] = nb_pages
            st.rerun()

    return page_actuelle, offset, nb_pages


@st.cache_data(ttl=600)
def get_departements(_conn):
    """Liste des départements"""
    try:
        df = pd.read_sql("SELECT DISTINCT nom FROM DEPARTEMENT ORDER BY nom", _conn)
        return ["Tous"] + df['nom'].tolist()
    except:
        return ["Tous"]


# ==========================================
# PAGE ÉTUDIANTS (AVEC PAGINATION)
# ==========================================

@st.cache_data(ttl=300)
def count_etudiants(_conn, dept="Tous", statut="Tous"):
    """Compte les étudiants"""
    query = """
        SELECT COUNT(*) FROM ETUDIANT e
        JOIN FORMATION f ON f.id_form = e.id_form
        JOIN DEPARTEMENT d ON d.id_dept = f.id_dept
        WHERE 1=1
    """
    params = []

    if dept != "Tous":
        query += " AND d.nom = %s"
        params.append(dept)

    if statut != "Tous":
        query += " AND e.statut = %s"
        params.append(statut)

    cur = _conn.cursor()
    cur.execute(query, params)
    total = cur.fetchone()[0]
    cur.close()
    return total


@st.cache_data(ttl=300)
def get_etudiants(_conn, dept, statut, limit, offset):
    """Charge UNE PAGE d'étudiants"""
    query = """
        SELECT 
            e.id_etu,
            e.nom,
            e.prenom,
            e.email,
            e.promo,
            f.nom as formation,
            d.nom as departement
        FROM ETUDIANT e
        JOIN FORMATION f ON f.id_form = e.id_form
        JOIN DEPARTEMENT d ON d.id_dept = f.id_dept
        WHERE 1=1
    """
    params = []

    if dept != "Tous":
        query += " AND d.nom = %s"
        params.append(dept)

    if statut != "Tous":
        query += " AND e.statut = %s"
        params.append(statut)

    query += " ORDER BY e.nom LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    return pd.read_sql(query, _conn, params=params)


def page_etudiants(conn):
    """PAGE ÉTUDIANTS"""
    st.header("👥 Gestion des Étudiants")

    # Filtres
    col1, col2, col3 = st.columns(3)

    with col1:
        dept = st.selectbox("Département", get_departements(conn), key="dept_etu")

    with col2:
        statut = st.selectbox("Statut", ["Tous", "actif", "diplômé"], key="statut_etu")

    with col3:
        items_pp = st.selectbox("Par page", [25, 50, 100], index=1, key="ipp_etu")

    st.markdown("---")

    # Comptage
    total = count_etudiants(conn, dept, statut)

    if total == 0:
        st.warning("Aucun étudiant trouvé.")
        return

    st.info(f"📊 **{total:,} étudiants** trouvés")

    # Pagination
    page, offset, nb_pages = create_pagination(total, items_pp, "page_etu")

    # Chargement
    with st.spinner(f"Chargement page {page}/{nb_pages}..."):
        df = get_etudiants(conn, dept, statut, items_pp, offset)

    # Affichage
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Export
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Exporter cette page",
            csv,
            f"etudiants_page_{page}.csv",
            "text/csv"
        )


# ==========================================
# PAGE PROFESSEURS (AVEC PAGINATION)
# ==========================================

@st.cache_data(ttl=300)
def count_professeurs(_conn, dept="Tous"):
    """Compte les professeurs"""
    query = """
        SELECT COUNT(*) FROM PROFESSEUR p
        JOIN DEPARTEMENT d ON d.id_dept = p.id_dept
        WHERE 1=1
    """
    params = []

    if dept != "Tous":
        query += " AND d.nom = %s"
        params.append(dept)

    cur = _conn.cursor()
    cur.execute(query, params)
    total = cur.fetchone()[0]
    cur.close()
    return total


@st.cache_data(ttl=300)
def get_professeurs(_conn, dept, limit, offset):
    """Charge UNE PAGE de professeurs"""
    query = """
        SELECT 
            p.id_prof,
            p.nom,
            p.prenom,
            p.email,
            p.specialite,
            d.nom as departement
        FROM PROFESSEUR p
        JOIN DEPARTEMENT d ON d.id_dept = p.id_dept
        WHERE 1=1
    """
    params = []

    if dept != "Tous":
        query += " AND d.nom = %s"
        params.append(dept)

    query += " ORDER BY p.nom LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    return pd.read_sql(query, _conn, params=params)


def page_professeurs(conn):
    """PAGE PROFESSEURS"""
    st.header("👨‍🏫 Gestion des Professeurs")

    # Filtres
    col1, col2 = st.columns(2)

    with col1:
        dept = st.selectbox("Département", get_departements(conn), key="dept_prof")

    with col2:
        items_pp = st.selectbox("Par page", [25, 50, 100], index=1, key="ipp_prof")

    st.markdown("---")

    # Comptage
    total = count_professeurs(conn, dept)

    if total == 0:
        st.warning("Aucun professeur trouvé.")
        return

    st.info(f"📊 **{total} professeurs** trouvés")

    # Pagination
    page, offset, nb_pages = create_pagination(total, items_pp, "page_prof")

    # Chargement
    with st.spinner(f"Chargement page {page}/{nb_pages}..."):
        df = get_professeurs(conn, dept, items_pp, offset)

    # Affichage
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)


# ==========================================
# PAGE EXAMENS (AVEC PAGINATION)
# ==========================================

@st.cache_data(ttl=300)
def count_examens(_conn, date_debut, date_fin):
    """Compte les examens"""
    query = "SELECT COUNT(*) FROM EXAMEN WHERE date_exam BETWEEN %s AND %s"
    cur = _conn.cursor()
    cur.execute(query, (date_debut, date_fin))
    total = cur.fetchone()[0]
    cur.close()
    return total


@st.cache_data(ttl=300)
def get_examens(_conn, date_debut, date_fin, limit, offset):
    """Charge UNE PAGE d'examens"""
    query = """
        SELECT 
            e.id_exam,
            m.nom as module,
            e.date_exam,
            e.duree_min,
            l.nom as salle,
            e.session_examen
        FROM EXAMEN e
        JOIN MODULE m ON m.id_mod = e.id_mod
        JOIN LIEU_EXAMEN l ON l.id_lieu = e.id_lieu
        WHERE e.date_exam BETWEEN %s AND %s
        ORDER BY e.date_exam
        LIMIT %s OFFSET %s
    """
    df = pd.read_sql(query, _conn, params=(date_debut, date_fin, limit, offset))

    if not df.empty:
        df['date_exam'] = pd.to_datetime(df['date_exam']).dt.strftime('%Y-%m-%d %H:%M')

    return df


def page_examens(conn):
    """PAGE EXAMENS"""
    st.header("📝 Planning des Examens")

    # Filtres
    col1, col2, col3 = st.columns(3)

    with col1:
        date_debut = st.date_input("Date début", datetime.now().date())

    with col2:
        date_fin = st.date_input("Date fin", datetime.now().date() + timedelta(days=30))

    with col3:
        items_pp = st.selectbox("Par page", [25, 50, 100], index=1, key="ipp_exam")

    st.markdown("---")

    # Vérifier période
    if (date_fin - date_debut).days > 90:
        st.warning("⚠️ Période trop grande ! Max 90 jours.")
        return

    # Comptage
    total = count_examens(conn, date_debut, date_fin)

    if total == 0:
        st.info("Aucun examen dans cette période.")
        return

    st.info(f"📊 **{total} examens** trouvés")

    # Pagination
    page, offset, nb_pages = create_pagination(total, items_pp, "page_exam")

    # Chargement
    with st.spinner(f"Chargement page {page}/{nb_pages}..."):
        df = get_examens(conn, date_debut, date_fin, items_pp, offset)

    # Affichage
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)


# ==========================================
# PAGE ACCUEIL
# ==========================================

def page_accueil(conn):
    """PAGE D'ACCUEIL avec stats globales"""
    st.header("🏠 Tableau de Bord")

    try:
        # Stats légères (pas de pagination nécessaire)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM ETUDIANT WHERE statut = 'actif'")
        nb_etu = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM PROFESSEUR")
        nb_prof = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM EXAMEN")
        nb_exam = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM DEPARTEMENT")
        nb_dept = cur.fetchone()[0]

        cur.close()

        # Affichage des métriques
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("👥 Étudiants Actifs", f"{nb_etu:,}")
        col2.metric("👨‍🏫 Professeurs", nb_prof)
        col3.metric("📝 Examens", nb_exam)
        col4.metric("🏢 Départements", nb_dept)

        st.markdown("---")
        st.success("✅ Système opérationnel")

        # Informations
        st.info("""
        **Fonctionnalités disponibles:**
        - 👥 **Étudiants** : Gestion avec pagination (évite surcharge mémoire)
        - 👨‍🏫 **Professeurs** : Liste paginée par département
        - 📝 **Examens** : Planning avec filtres par date
        - 📊 **Statistiques** : KPIs et métriques globales
        """)

    except Exception as e:
        st.error(f"❌ Erreur chargement stats: {e}")


# ==========================================
# PAGE STATISTIQUES
# ==========================================

def page_statistiques(conn):
    """PAGE STATISTIQUES (pas de pagination, données agrégées)"""
    st.header("📊 Statistiques Avancées")

    try:
        # Répartition par département (données agrégées = légères)
        query = """
            SELECT 
                d.nom as departement,
                COUNT(DISTINCT e.id_etu) as nb_etudiants,
                COUNT(DISTINCT p.id_prof) as nb_professeurs
            FROM DEPARTEMENT d
            LEFT JOIN FORMATION f ON f.id_dept = d.id_dept
            LEFT JOIN ETUDIANT e ON e.id_form = f.id_form
            LEFT JOIN PROFESSEUR p ON p.id_dept = d.id_dept
            GROUP BY d.nom
            ORDER BY nb_etudiants DESC
        """
        df = pd.read_sql(query, conn)

        if not df.empty:
            st.subheader("Répartition par Département")
            st.bar_chart(df.set_index('departement')['nb_etudiants'])
            st.dataframe(df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"❌ Erreur: {e}")


# ==========================================
# MENU PRINCIPAL
# ==========================================

def main():
    """FONCTION PRINCIPALE"""

    # Titre
    st.title("📚 Système de Gestion des Examens Universitaires")

    # Connexion BD
    conn = get_database_connection()

    if conn is None:
        st.error("❌ Impossible de se connecter à la base de données")
        st.info("""
        **Vérifiez:**
        1. Configuration des Secrets Streamlit (Settings → Secrets)
        2. Base de données Neon.tech active
        3. Credentials corrects
        """)
        st.stop()

    st.success("✅ Connecté à la base de données")

    # Menu de navigation
    st.sidebar.title("📋 Navigation")

    page = st.sidebar.radio(
        "Menu Principal",
        [
            "🏠 Accueil",
            "👥 Étudiants",
            "👨‍🏫 Professeurs",
            "📝 Examens",
            "📊 Statistiques"
        ]
    )

    st.sidebar.markdown("---")
    st.sidebar.info("""
    **💡 Info:**
    Toutes les pages utilisent
    la pagination pour éviter
    les crashs mémoire.
    """)

    # Routing des pages
    if page == "🏠 Accueil":
        page_accueil(conn)

    elif page == "👥 Étudiants":
        page_etudiants(conn)

    elif page == "👨‍🏫 Professeurs":
        page_professeurs(conn)

    elif page == "📝 Examens":
        page_examens(conn)

    elif page == "📊 Statistiques":
        page_statistiques(conn)

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("Projet BD Avancées 2025")


# ==========================================
# POINT D'ENTRÉE
# ==========================================

if __name__ == "__main__":
    main()