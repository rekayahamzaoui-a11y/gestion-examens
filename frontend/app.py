# frontend/app.py
import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import traceback

# ⚠️ CETTE LIGNE DOIT ÊTRE LA TOUTE PREMIÈRE COMMANDE STREAMLIT
st.set_page_config(
    page_title="Gestion des Examens",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Imports après set_page_config
from auth import init_session_state, login_page, logout, require_auth, get_current_user
from users_db import init_users_table, get_all_users, create_user, delete_user
from queries import (
    load_students_by_department,
    load_exams_per_professor,
    load_students_per_module,
    load_exam_schedule,
    load_room_occupancy,
    get_constraint_violations,
    get_dashboard_stats,
    get_available_rooms,
    get_all_modules,
    get_all_professors,
    create_exam,
    assign_surveillance,
    update_exam,
    delete_exam,
    load_student_own_exams,
    get_student_id_from_username,
    get_exam_details,
    load_professor_surveillances,
    get_professor_id_from_username,
    get_all_rooms
)
from dashboards import (
    chart_students_per_module,
    chart_exams_per_professor,
    chart_room_occupancy,
    plotly_exam_timeline,
    plotly_students_per_department
)
from db_utils import test_connection, get_connection

# Options Streamlit
st.set_option('client.showErrorDetails', True)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .user-info {
        background-color: #e8f4f8;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# Wrapper pour capturer les erreurs
def safe_execute(func):
    """Décorateur pour capturer les erreurs"""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"❌ ERREUR : {type(e).__name__}")
            st.error(f"**Message:** {str(e)}")
            with st.expander("📋 Détails techniques"):
                st.code(traceback.format_exc())
            print(f"❌ ERREUR PAGE: {type(e).__name__}")
            print(traceback.format_exc())

    return wrapper


# ==========================================
# INITIALISATION
# ==========================================
init_session_state()
init_users_table()

# Test connexion DB
if not test_connection():
    st.error("❌ Impossible de se connecter à PostgreSQL")
    st.info("Vérifiez vos secrets Streamlit Cloud")
    st.stop()

# ==========================================
# PAGE DE CONNEXION
# ==========================================
if not st.session_state.authenticated:
    login_page()
    st.stop()

# ==========================================
# INTERFACE PRINCIPALE
# ==========================================
user = get_current_user()

# Sidebar
st.sidebar.markdown(f"""
<div class="user-info">
    <strong>👤 {user['prenom']} {user['nom']}</strong><br>
    <small>🎭 Rôle : {user['role'].capitalize()}</small>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
    logout()

st.sidebar.markdown("---")
st.sidebar.title("📚 Navigation")

# ==========================================
# MENU SELON LE RÔLE
# ==========================================
if user['role'] == 'admin':
    menu_options = [
        "🏠 Dashboard",
        "👥 Étudiants",
        "👨‍🏫 Professeurs",
        "📊 Statistiques",
        "📅 Planning Examens",
        "➕ Planifier un Examen",
        "🏫 Salles",
        "⚠️ Vérification Contraintes",
        "🔐 Gestion Utilisateurs"
    ]
elif user['role'] == 'professeur':
    menu_options = [
        "🏠 Dashboard",
        "👥 Étudiants",
        "📅 Mes Examens",
        "📊 Statistiques"
    ]
else:  # etudiant
    menu_options = [
        "🏠 Accueil",
        "📅 Mes Examens",
        "📊 Mes Notes"
    ]

menu = st.sidebar.radio("Choisissez une section :", menu_options)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Astuce** : Utilisez les filtres pour affiner vos recherches")


# ==========================================
# PAGES
# ==========================================

@safe_execute
def render_dashboard():
    st.markdown('<p class="main-header">📊 Tableau de Bord</p>', unsafe_allow_html=True)

    stats = get_dashboard_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Étudiants", stats.get('total_students', 0))
    with col2:
        st.metric("📝 Examens", stats.get('total_exams', 0))
    with col3:
        st.metric("👨‍🏫 Professeurs", stats.get('total_professors', 0))
    with col4:
        st.metric("🏫 Salles", stats.get('total_rooms', 0))

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📚 Étudiants par module")
        df_modules = load_students_per_module()
        if not df_modules.empty:
            chart_students_per_module(df_modules)
        else:
            st.info("Aucune donnée disponible")

    with col_right:
        st.subheader("🎓 Répartition par département")
        df_students = load_students_by_department()
        if not df_students.empty:
            plotly_students_per_department(df_students)
        else:
            st.info("Aucune donnée disponible")


@safe_execute
def render_students():
    if not require_auth(['admin', 'professeur']):
        st.stop()

    st.markdown('<p class="main-header">👥 Gestion des Étudiants</p>', unsafe_allow_html=True)

    with st.spinner("Chargement des étudiants..."):
        df = load_students_by_department()

    if not df.empty:
        # Pagination
        per_page = st.selectbox("Lignes par page", [25, 50, 100], index=1)

        col1, col2 = st.columns(2)

        with col1:
            dept_filter = st.multiselect(
                "Filtrer par département :",
                options=sorted(df['departement'].unique()),
                default=[]
            )

        with col2:
            niveau_filter = st.multiselect(
                "Filtrer par niveau :",
                options=sorted(df['niveau'].unique()),
                default=[]
            )

        # Recherche
        search = st.text_input("🔍 Rechercher (nom/prénom/email)", "")

        # Filtrage
        df_filtered = df.copy()

        if dept_filter:
            df_filtered = df_filtered[df_filtered['departement'].isin(dept_filter)]

        if niveau_filter:
            df_filtered = df_filtered[df_filtered['niveau'].isin(niveau_filter)]

        if search:
            search_lower = search.lower()
            df_filtered = df_filtered[
                df_filtered['nom'].str.lower().str.contains(search_lower, na=False) |
                df_filtered['prenom'].str.lower().str.contains(search_lower, na=False) |
                df_filtered['email'].str.lower().str.contains(search_lower, na=False)
                ]

        # Pagination
        total_rows = len(df_filtered)
        total_pages = (total_rows - 1) // per_page + 1 if total_rows > 0 else 1

        # État de page
        if 'page_students' not in st.session_state:
            st.session_state.page_students = 1

        # Navigation
        col_prev, col_info, col_next = st.columns([1, 2, 1])

        with col_prev:
            if st.button("⬅️ Précédent", disabled=st.session_state.page_students <= 1):
                st.session_state.page_students -= 1
                st.rerun()

        with col_info:
            st.markdown(f"**Page {st.session_state.page_students}/{total_pages}** ({total_rows} étudiants)")

        with col_next:
            if st.button("Suivant ➡️", disabled=st.session_state.page_students >= total_pages):
                st.session_state.page_students += 1
                st.rerun()

        # Affichage
        start_idx = (st.session_state.page_students - 1) * per_page
        end_idx = min(start_idx + per_page, total_rows)

        if total_rows > 0:
            st.dataframe(
                df_filtered.iloc[start_idx:end_idx],
                use_container_width=True,
                height=500
            )

            # Export CSV
            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Télécharger {total_rows} étudiants (CSV)",
                data=csv,
                file_name="etudiants.csv",
                mime="text/csv"
            )
        else:
            st.info("Aucun étudiant trouvé")
    else:
        st.warning("Aucun étudiant dans la base de données")


@safe_execute
def render_professors():
    if not require_auth(['admin']):
        st.stop()

    st.markdown('<p class="main-header">👨‍🏫 Surveillance des Examens</p>', unsafe_allow_html=True)

    df = load_exams_per_professor()

    if not df.empty:
        st.dataframe(df, use_container_width=True, height=400)
        st.markdown("---")
        chart_exams_per_professor(df)

        overloaded = df[df['nb_examens'] > 3]
        if not overloaded.empty:
            st.error("⚠️ **Attention** : Certains professeurs dépassent 3 examens/jour")
            st.dataframe(overloaded)
    else:
        st.info("Aucune surveillance enregistrée")


@safe_execute
def render_statistics():
    if not require_auth(['admin', 'professeur']):
        st.stop()

    st.markdown('<p class="main-header">📊 Statistiques Détaillées</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📚 Modules", "🏫 Salles", "📅 Examens"])

    with tab1:
        df = load_students_per_module()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            chart_students_per_module(df)
        else:
            st.info("Aucune donnée")

    with tab2:
        df = load_room_occupancy()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            chart_room_occupancy(df)
        else:
            st.info("Aucune donnée")

    with tab3:
        df = load_exam_schedule()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun examen planifié")


# ==========================================
# ROUTAGE DES PAGES
# ==========================================

if menu == "🏠 Dashboard" or menu == "🏠 Accueil":
    render_dashboard()

elif menu == "👥 Étudiants":
    render_students()

elif menu == "👨‍🏫 Professeurs":
    render_professors()

elif menu == "📊 Statistiques":
    render_statistics()

elif menu == "📅 Planning Examens":
    @safe_execute
    def render_planning():
        st.markdown('<p class="main-header">📅 Planning des Examens</p>', unsafe_allow_html=True)
        df = load_exam_schedule()
        if not df.empty:
            st.dataframe(df, use_container_width=True, height=500)
        else:
            st.warning("Aucun examen planifié")


    render_planning()

else:
    st.info(f"Page '{menu}' en cours de développement")

# ==========================================
# FOOTER
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown("**🎓 Système de Gestion d'Examens**")
st.sidebar.markdown("Version 2.0 - Optimisé")