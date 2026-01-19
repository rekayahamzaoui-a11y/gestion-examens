# frontend/app.py
import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
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
import traceback
st.set_page_config(page_title="Gestion des Examens", page_icon="📚", layout="wide")
st.set_option('client.showErrorDetails', True)

from auth import init_session_state, login_page, logout, require_auth, get_current_user

#st.set_page_config(page_title="Gestion des Examens", page_icon="📚", layout="wide")
# ==========================================
# CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Gestion des Examens",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# ==========================================
# INITIALISATION
# ==========================================
init_session_state()
init_users_table()

# Test connexion DB
if not test_connection():
    st.error("❌ Impossible de se connecter à PostgreSQL")
    st.stop()

# ==========================================
# PAGE DE CONNEXION
# ==========================================
if not st.session_state.authenticated:
    login_page()
    st.stop()

# ==========================================
# INTERFACE PRINCIPALE (UTILISATEUR CONNECTÉ)
# ==========================================
user = get_current_user()

# Sidebar avec infos utilisateur
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
        "🤖 Génération Automatique",
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
# PAGES COMMUNES
# ==========================================

if menu == "🏠 Dashboard" or menu == "🏠 Accueil":
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
        chart_students_per_module(df_modules)

    with col_right:
        st.subheader("🎓 Répartition par département")
        df_students = load_students_by_department()
        plotly_students_per_department(df_students)

elif menu == "👥 Étudiants":
    if not require_auth(['admin', 'professeur']):
        st.stop()

    st.markdown('<p class="main-header">👥 Gestion des Étudiants</p>', unsafe_allow_html=True)

    df = load_students_by_department()

    if not df.empty:
        col1, col2 = st.columns(2)

        with col1:
            dept_filter = st.multiselect(
                "Filtrer par département :",
                options=df['departement'].unique(),
                default=df['departement'].unique()
            )

        with col2:
            niveau_filter = st.multiselect(
                "Filtrer par niveau :",
                options=df['niveau'].unique(),
                default=df['niveau'].unique()
            )

        df_filtered = df[
            (df['departement'].isin(dept_filter)) &
            (df['niveau'].isin(niveau_filter))
            ]

        st.markdown(f"**{len(df_filtered)} étudiants trouvés**")
        st.dataframe(df_filtered, use_container_width=True, height=500)

        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name="etudiants.csv",
            mime="text/csv"
        )
    else:
        st.warning("Aucun étudiant trouvé")

elif menu == "👨‍🏫 Professeurs":
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

# Remplacez cette section (vers la ligne 250-260)
elif menu == "📅 Planning Examens" or menu == "📅 Mes Examens" or menu == "📅 Mes Surveillances":
    # Différencier selon le rôle
    if user['role'] == 'etudiant':
        # ==========================================
        # VUE ÉTUDIANT : Uniquement ses examens
        # ==========================================
        st.markdown('<p class="main-header">📅 Mes Examens</p>', unsafe_allow_html=True)
        st.info(f"👨‍🎓 **{user['prenom']} {user['nom']}** - Vos examens à venir")

        # Récupérer les infos de l'étudiant
        student_info = get_student_id_from_username(user['username'])

        if student_info:
            st.markdown(f"**Formation :** {student_info['formation']}")
            st.markdown("---")

            # Charger les examens de l'étudiant
            df = load_student_own_exams(user['username'])

            if not df.empty:
                # Statistiques personnelles
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("📝 Examens", len(df))

                with col2:
                    examens_passes = len(df[df['date_exam'] < pd.Timestamp.now()])
                    st.metric("✅ Passés", examens_passes)

                with col3:
                    examens_futurs = len(df[df['date_exam'] >= pd.Timestamp.now()])
                    st.metric("📅 À venir", examens_futurs)

                with col4:
                    notes_disponibles = df['note'].notna().sum()
                    st.metric("📊 Notes", notes_disponibles)

                st.markdown("---")

                # Onglets pour organiser l'information
                tab1, tab2, tab3 = st.tabs(["📅 Tous les examens", "⏰ À venir", "📊 Résultats"])

                with tab1:
                    st.subheader("📋 Planning complet de vos examens")

                    # Formater l'affichage
                    df_display = df.copy()
                    df_display['date_exam'] = pd.to_datetime(df_display['date_exam']).dt.strftime('%d/%m/%Y %H:%M')

                    # Colonnes à afficher
                    cols_to_show = ['date_exam', 'module', 'type_examen', 'duree_min',
                                    'salle', 'batiment', 'surveillants', 'statut']

                    st.dataframe(
                        df_display[cols_to_show],
                        use_container_width=True,
                        height=400,
                        column_config={
                            "date_exam": "Date et Heure",
                            "module": "Module",
                            "type_examen": "Type",
                            "duree_min": "Durée (min)",
                            "salle": "Salle",
                            "batiment": "Bâtiment",
                            "surveillants": "Surveillants",
                            "statut": "Statut"
                        }
                    )

                    # Export CSV personnel
                    csv = df_display.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Télécharger mon planning",
                        data=csv,
                        file_name=f"planning_{user['username']}.csv",
                        mime="text/csv"
                    )

                with tab2:
                    st.subheader("⏰ Examens à venir")

                    # Filtrer les examens futurs
                    df_futurs = df[df['date_exam'] >= pd.Timestamp.now()].copy()

                    if not df_futurs.empty:
                        # Compter les jours restants
                        df_futurs['jours_restants'] = (
                                pd.to_datetime(df_futurs['date_exam']) - pd.Timestamp.now()
                        ).dt.days

                        # Afficher les examens urgents (< 7 jours)
                        df_urgents = df_futurs[df_futurs['jours_restants'] < 7]

                        if not df_urgents.empty:
                            st.warning(f"⚠️ **{len(df_urgents)} examen(s) dans moins de 7 jours !**")

                            for _, exam in df_urgents.iterrows():
                                with st.expander(f"🔴 {exam['module']} - {exam['jours_restants']} jour(s)"):
                                    col1, col2 = st.columns(2)

                                    with col1:
                                        st.write(f"📅 **Date :** {exam['date_exam'].strftime('%d/%m/%Y à %H:%M')}")
                                        st.write(f"⏱️ **Durée :** {exam['duree_min']} minutes")
                                        st.write(f"📝 **Type :** {exam['type_examen']}")

                                    with col2:
                                        st.write(f"🏫 **Salle :** {exam['salle']}")
                                        st.write(f"🏢 **Bâtiment :** {exam['batiment']}")
                                        st.write(f"👨‍🏫 **Surveillant(s) :** {exam['surveillants']}")

                        # Afficher tous les examens à venir
                        st.markdown("---")
                        st.markdown("**📅 Calendrier complet**")

                        df_display_futurs = df_futurs.copy()
                        df_display_futurs['date_exam'] = pd.to_datetime(df_display_futurs['date_exam']).dt.strftime(
                            '%d/%m/%Y %H:%M')

                        st.dataframe(
                            df_display_futurs[['date_exam', 'module', 'type_examen',
                                               'salle', 'jours_restants']],
                            use_container_width=True,
                            column_config={
                                "date_exam": "Date et Heure",
                                "module": "Module",
                                "type_examen": "Type",
                                "salle": "Salle",
                                "jours_restants": st.column_config.NumberColumn(
                                    "Jours restants",
                                    format="%d j"
                                )
                            }
                        )
                    else:
                        st.info("✅ Aucun examen à venir pour le moment")

                with tab3:
                    st.subheader("📊 Résultats et notes")

                    # Filtrer les examens avec notes
                    df_notes = df[df['note'].notna()].copy()

                    if not df_notes.empty:
                        # Statistiques
                        moyenne = df_notes['note'].mean()
                        note_max = df_notes['note'].max()
                        note_min = df_notes['note'].min()

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("📊 Moyenne", f"{moyenne:.2f}/20")

                        with col2:
                            st.metric("🏆 Meilleure note", f"{note_max:.2f}/20")

                        with col3:
                            st.metric("📉 Note minimale", f"{note_min:.2f}/20")

                        st.markdown("---")

                        # Tableau des notes
                        df_display_notes = df_notes.copy()
                        df_display_notes['date_exam'] = pd.to_datetime(df_display_notes['date_exam']).dt.strftime(
                            '%d/%m/%Y')

                        st.dataframe(
                            df_display_notes[['module', 'date_exam', 'type_examen', 'note', 'credits', 'coefficient']],
                            use_container_width=True,
                            column_config={
                                "module": "Module",
                                "date_exam": "Date",
                                "type_examen": "Type",
                                "note": st.column_config.NumberColumn(
                                    "Note",
                                    format="%.2f/20"
                                ),
                                "credits": "Crédits",
                                "coefficient": "Coeff"
                            }
                        )

                        # Graphique des notes
                        fig = px.bar(
                            df_notes,
                            x='module',
                            y='note',
                            title="📊 Vos notes par module",
                            labels={'note': 'Note (/20)', 'module': 'Module'},
                            color='note',
                            color_continuous_scale=['red', 'orange', 'yellow', 'lightgreen', 'green'],
                            range_color=[0, 20]
                        )

                        fig.add_hline(y=10, line_dash="dash", line_color="red",
                                      annotation_text="Moyenne")

                        st.plotly_chart(fig, use_container_width=True)

                    else:
                        st.info("📋 Aucune note disponible pour le moment")

            else:
                st.warning("⚠️ Aucun examen trouvé pour votre compte")
                st.info("💡 Vérifiez que votre email correspond à celui de votre inscription")
        else:
            st.error("❌ Impossible de récupérer vos informations d'étudiant")
            st.info("💡 Contactez l'administrateur pour lier votre compte utilisateur à votre dossier étudiant")

    elif user['role'] == 'professeur':
        # ==========================================
        # VUE PROFESSEUR : Uniquement ses surveillances
        # ==========================================
        st.markdown('<p class="main-header">👨‍🏫 Mes Surveillances</p>', unsafe_allow_html=True)

        prof_info = get_professor_id_from_username(user['username'])

        if prof_info:
            st.info(f"👨‍🏫 **{prof_info['prenom']} {prof_info['nom']}** - {prof_info['specialite']}")
            st.markdown(f"**Département :** {prof_info['departement']}")
            st.markdown("---")

            # Charger les surveillances
            df = load_professor_surveillances(user['username'])

            if not df.empty:
                # Statistiques personnelles
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("📝 Surveillances", len(df))

                with col2:
                    surveillances_passees = len(df[df['date_exam'] < pd.Timestamp.now()])
                    st.metric("✅ Passées", surveillances_passees)

                with col3:
                    surveillances_futures = len(df[df['date_exam'] >= pd.Timestamp.now()])
                    st.metric("📅 À venir", surveillances_futures)

                with col4:
                    surveillances_principales = len(df[df['role'] == 'principal'])
                    st.metric("👑 Principal", surveillances_principales)

                st.markdown("---")

                # Onglets
                tab1, tab2, tab3 = st.tabs(["📅 Toutes les surveillances", "⏰ À venir", "📊 Statistiques"])

                with tab1:
                    st.subheader("📋 Planning complet de vos surveillances")

                    df_display = df.copy()
                    df_display['date_exam'] = pd.to_datetime(df_display['date_exam']).dt.strftime('%d/%m/%Y %H:%M')

                    st.dataframe(
                        df_display[['date_exam', 'module', 'formation', 'niveau',
                                    'salle', 'nb_inscrits', 'role', 'autres_surveillants']],
                        use_container_width=True,
                        height=500,
                        column_config={
                            "date_exam": "Date et Heure",
                            "module": "Module",
                            "formation": "Formation",
                            "niveau": "Niveau",
                            "salle": "Salle",
                            "nb_inscrits": "Étudiants",
                            "role": "Rôle",
                            "autres_surveillants": "Co-surveillants"
                        }
                    )

                    # Export CSV
                    csv = df_display.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Télécharger mes surveillances",
                        data=csv,
                        file_name=f"surveillances_{user['username']}.csv",
                        mime="text/csv"
                    )

                with tab2:
                    st.subheader("⏰ Surveillances à venir")

                    df_futures = df[df['date_exam'] >= pd.Timestamp.now()].copy()

                    if not df_futures.empty:
                        df_futures['jours_restants'] = (
                                pd.to_datetime(df_futures['date_exam']) - pd.Timestamp.now()
                        ).dt.days

                        # Surveillances urgentes (< 7 jours)
                        df_urgents = df_futures[df_futures['jours_restants'] < 7]

                        if not df_urgents.empty:
                            st.warning(f"⚠️ **{len(df_urgents)} surveillance(s) dans moins de 7 jours !**")

                            for _, surv in df_urgents.iterrows():
                                with st.expander(f"🔴 {surv['module']} - {surv['jours_restants']} jour(s)"):
                                    col1, col2 = st.columns(2)

                                    with col1:
                                        st.write(f"📅 **Date :** {surv['date_exam'].strftime('%d/%m/%Y à %H:%M')}")
                                        st.write(f"⏱️ **Durée :** {surv['duree_min']} minutes")
                                        st.write(f"👑 **Rôle :** {surv['role']}")

                                    with col2:
                                        st.write(f"🏫 **Salle :** {surv['salle']} ({surv['batiment']})")
                                        st.write(f"👥 **Étudiants :** {surv['nb_inscrits']}")
                                        if surv['autres_surveillants']:
                                            st.write(f"🤝 **Avec :** {surv['autres_surveillants']}")

                        st.markdown("---")
                        st.markdown("**📅 Calendrier complet**")

                        df_display_futures = df_futures.copy()
                        df_display_futures['date_exam'] = pd.to_datetime(df_display_futures['date_exam']).dt.strftime(
                            '%d/%m/%Y %H:%M')

                        st.dataframe(
                            df_display_futures[['date_exam', 'module', 'formation',
                                                'salle', 'role', 'jours_restants']],
                            use_container_width=True,
                            column_config={
                                "date_exam": "Date et Heure",
                                "module": "Module",
                                "formation": "Formation",
                                "salle": "Salle",
                                "role": "Rôle",
                                "jours_restants": st.column_config.NumberColumn(
                                    "Jours restants",
                                    format="%d j"
                                )
                            }
                        )
                    else:
                        st.info("✅ Aucune surveillance à venir")

                with tab3:
                    st.subheader("📊 Statistiques de surveillance")

                    # Répartition par rôle
                    st.markdown("**📊 Répartition par rôle**")
                    role_counts = df['role'].value_counts()

                    fig_role = px.pie(
                        values=role_counts.values,
                        names=role_counts.index,
                        title="Répartition principal vs assistant"
                    )
                    st.plotly_chart(fig_role, use_container_width=True)

                    # Nombre de surveillances par jour
                    st.markdown("**📅 Charge de travail**")
                    df_by_day = df.copy()
                    df_by_day['jour'] = pd.to_datetime(df_by_day['date_exam']).dt.date
                    surv_par_jour = df_by_day.groupby('jour').size()

                    fig_jour = px.bar(
                        x=surv_par_jour.index.astype(str),
                        y=surv_par_jour.values,
                        labels={'x': 'Date', 'y': 'Nombre de surveillances'},
                        title="Nombre de surveillances par jour"
                    )
                    st.plotly_chart(fig_jour, use_container_width=True)

                    # Avertissement si > 3 surveillances un jour
                    jours_surcharges = surv_par_jour[surv_par_jour > 3]
                    if not jours_surcharges.empty:
                        st.error(f"⚠️ **Attention** : {len(jours_surcharges)} jour(s) avec plus de 3 surveillances !")
                        st.dataframe(jours_surcharges.reset_index(), use_container_width=True)

            else:
                st.warning("⚠️ Aucune surveillance assignée pour le moment")
        else:
            st.error("❌ Impossible de récupérer vos informations de professeur")
            st.info("💡 Contactez l'administrateur pour lier votre compte utilisateur à votre dossier professeur")

    else:  # admin
        # ==========================================
        # VUE ADMIN : Tous les examens
        # ==========================================
        st.markdown('<p class="main-header">📅 Planning des Examens</p>', unsafe_allow_html=True)

        df = load_exam_schedule()

        if not df.empty:
            st.dataframe(df, use_container_width=True, height=500)
            st.markdown("---")
            st.subheader("📆 Timeline des examens")
            plotly_exam_timeline(df)
        else:
            st.warning("Aucun examen planifié")

elif menu == "📊 Statistiques":
    if not require_auth(['admin', 'professeur']):
        st.stop()

    st.markdown('<p class="main-header">📊 Statistiques Détaillées</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📚 Modules", "🏫 Salles", "📅 Examens"])

    with tab1:
        df = load_students_per_module()
        st.dataframe(df, use_container_width=True)
        chart_students_per_module(df)

    with tab2:
        df = load_room_occupancy()
        st.dataframe(df, use_container_width=True)
        chart_room_occupancy(df)

    with tab3:
        df = load_exam_schedule()
        st.dataframe(df, use_container_width=True)
elif menu == "➕ Planifier un Examen":
    if not require_auth(['admin']):
        st.stop()

    st.markdown('<p class="main-header">➕ Planifier un Nouvel Examen</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📝 Créer un examen", "✏️ Modifier un examen", "🗑️ Supprimer un examen"])

    # ==========================================
    # TAB 1 : CRÉER UN EXAMEN
    # ==========================================
    with tab1:
        st.subheader("📝 Nouveau Planning d'Examen")

        with st.form("create_exam_form"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**📅 Date et Heure**")
                exam_date = st.date_input("Date de l'examen *")
                exam_time = st.time_input("Heure de début *", value=None)
                duree = st.number_input("Durée (minutes) *", min_value=30, max_value=300, value=90, step=15)

                st.markdown("**📚 Informations**")
                modules = get_all_modules()
                if modules:
                    module_options = {f"{m['nom']} ({m['formation']}) - {m['nb_inscrits']} inscrits": m['id_mod']
                                      for m in modules}
                    selected_module = st.selectbox("Module *", options=list(module_options.keys()))
                    id_mod = module_options[selected_module]

                    # Afficher le nombre d'inscrits
                    selected_mod_data = next(m for m in modules if m['id_mod'] == id_mod)
                    st.info(f"👥 {selected_mod_data['nb_inscrits']} étudiants inscrits à ce module")
                else:
                    st.error("❌ Aucun module disponible")
                    id_mod = None

            with col2:
                type_exam = st.selectbox("Type d'examen *", ["partiel", "final", "rattrapage"])
                session = st.selectbox("Session *", ["S1", "S2", "Rattrapage"])

                st.markdown("**🏫 Salle**")

                # Afficher les salles disponibles si date/heure sélectionnées
                if exam_date and exam_time:
                    from datetime import datetime

                    date_time_str = f"{exam_date} {exam_time}"
                    date_exam = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")

                    available_rooms = get_available_rooms(date_exam, duree)

                    if available_rooms:
                        room_options = {
                            f"{r['nom']} - {r['type_lieu']} ({r['capacite']} places) - {r['batiment']}": r['id_lieu']
                            for r in available_rooms}
                        selected_room = st.selectbox("Salle disponible *", options=list(room_options.keys()))
                        id_lieu = room_options[selected_room]

                        # Warning si capacité insuffisante
                        selected_room_data = next(r for r in available_rooms if r['id_lieu'] == id_lieu)
                        if selected_mod_data['nb_inscrits'] > selected_room_data['capacite']:
                            st.warning(
                                f"⚠️ Attention : {selected_mod_data['nb_inscrits']} inscrits mais seulement {selected_room_data['capacite']} places !")
                    else:
                        st.error("❌ Aucune salle disponible pour ce créneau")
                        id_lieu = None
                else:
                    st.info("Sélectionnez d'abord une date et une heure")
                    id_lieu = None

                st.markdown("**👨‍🏫 Surveillance**")
                profs = get_all_professors()
                if profs:
                    prof_options = {f"{p['nom']} {p['prenom']} - {p['specialite']}": p['id_prof']
                                    for p in profs}

                    principal = st.selectbox("Surveillant principal *", options=list(prof_options.keys()))
                    id_prof_principal = prof_options[principal]

                    # Surveillant assistant (optionnel)
                    assistant_options = ["Aucun"] + list(prof_options.keys())
                    assistant = st.selectbox("Surveillant assistant (optionnel)", options=assistant_options)
                    id_prof_assistant = prof_options[assistant] if assistant != "Aucun" else None
                else:
                    st.error("❌ Aucun professeur disponible")
                    id_prof_principal = None
                    id_prof_assistant = None

            submit = st.form_submit_button("✅ Créer l'examen", use_container_width=True)

            if submit:
                if all([exam_date, exam_time, duree, id_mod, id_lieu, id_prof_principal]):
                    from datetime import datetime

                    date_time_str = f"{exam_date} {exam_time}"
                    date_exam = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")

                    # Créer l'examen
                    id_exam = create_exam(date_exam, duree, type_exam, session, id_mod, id_lieu)

                    if id_exam:
                        # Assigner les surveillants
                        assign_surveillance(id_exam, id_prof_principal, "principal")

                        if id_prof_assistant:
                            assign_surveillance(id_exam, id_prof_assistant, "assistant")

                        st.success(f"✅ Examen créé avec succès ! (ID: {id_exam})")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la création de l'examen")
                else:
                    st.warning("⚠️ Veuillez remplir tous les champs obligatoires")

    # ==========================================
    # TAB 2 : MODIFIER UN EXAMEN
    # ==========================================
    with tab2:
        st.subheader("✏️ Modifier un Examen Existant")

        # Sélectionner un examen à modifier
        df_exams = load_exam_schedule()

        if not df_exams.empty:
            exam_options = {f"Examen {row['module']} - {row['date_exam']} - {row['salle']}": idx
                            for idx, row in df_exams.iterrows()}

            selected_exam = st.selectbox("Choisir un examen à modifier", options=list(exam_options.keys()))
            exam_idx = exam_options[selected_exam]
            exam_data = df_exams.loc[exam_idx]

            # Récupérer les détails complets
            # Note : Vous devrez adapter selon votre structure de données
            st.info(f"📝 Modification de l'examen : {exam_data['module']}")

            with st.form("modify_exam_form"):
                new_date = st.date_input("Nouvelle date", value=exam_data['date_exam'].date())
                new_time = st.time_input("Nouvelle heure", value=exam_data['date_exam'].time())
                new_duree = st.number_input("Nouvelle durée", value=int(exam_data['duree_min']), min_value=30,
                                            max_value=300)

                # Sélection de la nouvelle salle
                available_rooms = get_available_rooms(f"{new_date} {new_time}", new_duree)
                if available_rooms:
                    room_options = {f"{r['nom']} ({r['capacite']} places)": r['id_lieu'] for r in available_rooms}
                    new_room = st.selectbox("Nouvelle salle", options=list(room_options.keys()))
                    new_id_lieu = room_options[new_room]
                else:
                    st.warning("Aucune salle disponible")
                    new_id_lieu = None

                submit_modify = st.form_submit_button("💾 Enregistrer les modifications")

                if submit_modify and new_id_lieu:
                    from datetime import datetime

                    new_datetime = datetime.combine(new_date, new_time)

                    # Note : Vous devrez récupérer l'id_exam depuis vos données
                    # Cette partie nécessite d'ajouter id_exam dans load_exam_schedule()
                    st.warning("⚠️ Fonctionnalité en cours de développement")
                    # if update_exam(id_exam, new_datetime, new_duree, exam_data['type_examen'],
                    #                exam_data['session_examen'], new_id_lieu):
                    #     st.success("✅ Examen modifié !")
                    #     st.rerun()
        else:
            st.info("Aucun examen à modifier")

    # ==========================================
    # TAB 3 : SUPPRIMER UN EXAMEN
    # ==========================================
    with tab3:
        st.subheader("🗑️ Supprimer un Examen")
        st.warning("⚠️ **Attention** : La suppression est définitive !")

        df_exams = load_exam_schedule()

        if not df_exams.empty:
            st.dataframe(df_exams, use_container_width=True)

            exam_id_to_delete = st.number_input("ID de l'examen à supprimer", min_value=1, step=1)

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("🗑️ Supprimer", type="primary"):
                    if delete_exam(exam_id_to_delete):
                        st.success("✅ Examen supprimé !")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la suppression")
        else:
            st.info("Aucun examen à supprimer")
elif menu == "🤖 Génération Automatique":
            if not require_auth(['admin']):
                st.stop()

            st.markdown('<p class="main-header">🤖 Génération Automatique d\'Emploi du Temps</p>',
                        unsafe_allow_html=True)

            st.info("""
                **Cette fonctionnalité génère automatiquement un planning optimal** en respectant toutes les contraintes :
                - ✅ 1 examen par jour par étudiant
                - ✅ Maximum 3 examens par jour par professeur
                - ✅ Capacité des salles respectée
                - ✅ Pas de chevauchement de salles
                - ✅ Attribution automatique des surveillants
                - ✅ Génération par formation et niveau
                """)

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("⚙️ Paramètres de génération")

                # Sélection du département
                departements = {
                    'Informatique': 1,
                    'Mathématiques': 2,
                    'Biologie': 3,
                    'Physique': 4
                }

                dept_selected = st.selectbox(
                    "🏢 Département",
                    options=list(departements.keys())
                )

                id_dept = departements[dept_selected]

                # Sélection du niveau
                niveaux = {
                    'L1': ['L1'],
                    'L2': ['L2'],
                    'L3': ['L3'],
                    'M1': ['M1'],
                    'M2': ['M2'],
                    'Licence (L1+L2+L3)': ['L1', 'L2', 'L3'],
                    'Master (M1+M2)': ['M1', 'M2'],
                    'Tous les niveaux': ['L1', 'L2', 'L3', 'M1', 'M2']
                }

                niveau_selected = st.selectbox(
                    "🎓 Niveau(x)",
                    options=list(niveaux.keys())
                )

                niveaux_list = niveaux[niveau_selected]

                start_date = st.date_input(
                    "📅 Date de début de la session",
                    value=datetime(2026, 1, 20).date()
                )

                nb_jours = st.number_input(
                    "📆 Nombre de jours",
                    min_value=5,
                    max_value=30,
                    value=15,
                    step=1,
                    help="Recommandé : 5-10 jours pour un niveau, 15-20 pour plusieurs niveaux"
                )

                type_session = st.selectbox(
                    "📝 Type de session",
                    ["partiel", "final", "rattrapage"]
                )

                session_name = st.text_input(
                    "🏷️ Nom de la session",
                    value="S1"
                )

            with col2:
                st.subheader("📊 Aperçu de la sélection")

                # Récupérer les modules et étudiants concernés
                conn = get_connection()
                if conn:
                    cur = conn.cursor()

                    # Compter les formations concernées
                    cur.execute("""
                        SELECT f.id_form, f.nom, f.niveau, COUNT(e.id_etu) as nb_etudiants
                        FROM FORMATION f
                        LEFT JOIN ETUDIANT e ON f.id_form = e.id_form
                        WHERE f.id_dept = %s AND f.niveau = ANY(%s)
                        GROUP BY f.id_form, f.nom, f.niveau
                        ORDER BY f.niveau;
                        """, (id_dept, niveaux_list))

                    formations_info = cur.fetchall()

                    if formations_info:
                        st.success(f"**{dept_selected} - {niveau_selected}**")

                        total_etudiants = sum(f[3] for f in formations_info)
                        total_formations = len(formations_info)

                        st.metric("👥 Étudiants concernés", total_etudiants)
                        st.metric("📚 Formations", total_formations)

                        # Compter les modules
                        cur.execute("""
                            SELECT COUNT(DISTINCT m.id_mod)
                            FROM MODULE m
                            JOIN FORMATION f ON m.id_form = f.id_form
                            WHERE f.id_dept = %s AND f.niveau = ANY(%s);
                            """, (id_dept, niveaux_list))

                        nb_modules = cur.fetchone()[0]
                        st.metric("📖 Modules à planifier", nb_modules)

                        # Afficher le détail
                        with st.expander("📋 Détail des formations"):
                            for f in formations_info:
                                st.write(f"- **{f[1]}** ({f[2]}) : {f[3]} étudiants")
                    else:
                        st.warning("Aucune formation trouvée pour cette sélection")

                    cur.close()
                    conn.close()

                # Statistiques salles et profs
                salles = get_all_rooms()

                # Filtrer les profs du département
                conn = get_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT COUNT(*) FROM PROFESSEUR WHERE id_dept = %s;
                        """, (id_dept,))
                    nb_profs = cur.fetchone()[0]
                    cur.close()
                    conn.close()
                else:
                    nb_profs = 0

                st.metric("🏫 Salles disponibles", len(salles))
                st.metric(f"👨‍🏫 Professeurs {dept_selected}", nb_profs)
                st.metric("📅 Créneaux possibles", nb_jours * 2)

            st.markdown("---")

            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

            with col_btn1:
                if st.button("🤖 Générer Planning", type="primary", use_container_width=True):
                    with st.spinner("⏳ Génération en cours..."):
                        from scheduler_engine import ExamScheduler

                        scheduler = ExamScheduler()

                        # Convertir date en datetime
                        start_datetime = datetime.combine(start_date, datetime.min.time())

                        # Générer pour le département et les niveaux sélectionnés
                        planning = scheduler.generate_schedule_by_department(
                            start_date=start_datetime,
                            nb_jours=nb_jours,
                            id_dept=id_dept,
                            niveaux=niveaux_list
                        )

                        if planning:
                            st.session_state.generated_planning = planning
                            st.session_state.planning_info = {
                                'dept': dept_selected,
                                'niveaux': niveau_selected
                            }
                            st.success(
                                f"✅ Planning généré ! {len(planning)} examens pour {dept_selected} - {niveau_selected}")
                            st.rerun()
                        else:
                            st.error("❌ Impossible de générer un planning avec ces contraintes")

            with col_btn2:
                if 'generated_planning' in st.session_state and st.session_state.generated_planning:
                    if st.button("💾 Sauvegarder en BD", use_container_width=True):
                        from scheduler_engine import ExamScheduler

                        scheduler = ExamScheduler()

                        if scheduler.save_planning_to_db(st.session_state.generated_planning):
                            st.success("✅ Planning sauvegardé !")
                            del st.session_state.generated_planning
                            if 'planning_info' in st.session_state:
                                del st.session_state.planning_info
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la sauvegarde")

            with col_btn3:
                if 'generated_planning' in st.session_state and st.session_state.generated_planning:
                    if st.button("🗑️ Annuler", use_container_width=True):
                        del st.session_state.generated_planning
                        if 'planning_info' in st.session_state:
                            del st.session_state.planning_info
                        st.rerun()

            # Affichage du planning généré
            if 'generated_planning' in st.session_state and st.session_state.generated_planning:
                st.markdown("---")

                # Afficher les infos du planning
                if 'planning_info' in st.session_state:
                    info = st.session_state.planning_info
                    st.info(f"📋 **Planning généré pour : {info['dept']} - {info['niveaux']}**")

                st.subheader("📋 Aperçu du Planning")

                planning = st.session_state.generated_planning

                # Convertir en DataFrame
                df_planning = pd.DataFrame(planning)

                # Formater l'affichage
                df_display = df_planning.copy()
                df_display['date_exam'] = pd.to_datetime(df_display['date_exam']).dt.strftime('%d/%m/%Y %H:%M')
                df_display['surveillants_noms'] = df_display['surveillants'].apply(
                    lambda surv: ', '.join([f"{s[1]} {s[2]}" for s in surv]) if surv else 'Aucun'
                )

                # Afficher le tableau
                st.dataframe(
                    df_display[['date_exam', 'module_nom', 'formation', 'nb_inscrits',
                                'salle_nom', 'capacite', 'surveillants_noms']],
                    use_container_width=True,
                    height=500,
                    column_config={
                        "date_exam": "Date et Heure",
                        "module_nom": "Module",
                        "formation": "Formation",
                        "nb_inscrits": "Inscrits",
                        "salle_nom": "Salle",
                        "capacite": "Capacité",
                        "surveillants_noms": "Surveillants"
                    }
                )

                # Statistiques du planning
                st.markdown("---")
                st.subheader("📊 Statistiques du Planning")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("📝 Examens planifiés", len(planning))

                with col2:
                    salles_utilisees = df_display['salle_nom'].nunique()
                    st.metric("🏫 Salles utilisées", salles_utilisees)

                with col3:
                    jours_utilises = pd.to_datetime(df_display['date_exam'], format='%d/%m/%Y %H:%M').dt.date.nunique()
                    st.metric("📅 Jours utilisés", jours_utilises)

                with col4:
                    taux_remplissage = (df_display['nb_inscrits'] / df_display['capacite'] * 100).mean()
                    st.metric("📊 Taux remplissage moyen", f"{taux_remplissage:.1f}%")

                # Grouper par jour
                st.markdown("---")
                st.subheader("📅 Répartition par jour")

                df_par_jour = df_display.copy()
                df_par_jour['jour'] = pd.to_datetime(df_par_jour['date_exam'], format='%d/%m/%Y %H:%M').dt.date
                examens_par_jour = df_par_jour.groupby('jour').size()

                fig_jour = px.bar(
                    x=examens_par_jour.index.astype(str),
                    y=examens_par_jour.values,
                    labels={'x': 'Date', 'y': 'Nombre d\'examens'},
                    title="Nombre d'examens par jour"
                )
                st.plotly_chart(fig_jour, use_container_width=True)
elif menu == "🏫 Salles":
    if not require_auth(['admin']):
        st.stop()

    st.markdown('<p class="main-header">🏫 Gestion des Salles</p>', unsafe_allow_html=True)

    df = load_room_occupancy()

    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.markdown("---")
        chart_room_occupancy(df)
    else:
        st.warning("Aucune salle enregistrée")

elif menu == "⚠️ Vérification Contraintes":
    if not require_auth(['admin']):
        st.stop()

    st.markdown('<p class="main-header">⚠️ Vérification des Contraintes</p>', unsafe_allow_html=True)

    violations = get_constraint_violations()

    st.subheader("👥 Étudiants avec plusieurs examens le même jour")
    if violations['students_multiple_exams']:
        st.error(f"❌ {len(violations['students_multiple_exams'])} violations détectées")
        for v in violations['students_multiple_exams']:
            st.warning(f"Étudiant {v[1]} : {v[3]} examens le {v[2]}")
    else:
        st.success("✅ Aucune violation")

    st.markdown("---")

    st.subheader("👨‍🏫 Professeurs dépassant 3 examens/jour")
    if violations['professors_overload']:
        st.error(f"❌ {len(violations['professors_overload'])} violations détectées")
        for v in violations['professors_overload']:
            st.warning(f"Professeur {v[1]} : {v[3]} examens le {v[2]}")
    else:
        st.success("✅ Aucune violation")

    st.markdown("---")

    st.subheader("🏫 Salles dépassant leur capacité")
    if violations['room_overcapacity']:
        st.error(f"❌ {len(violations['room_overcapacity'])} violations détectées")
        for v in violations['room_overcapacity']:
            st.warning(f"Examen {v[0]} : Salle {v[1]} - {v[3]}/{v[2]} places")
    else:
        st.success("✅ Aucune violation")

elif menu == "🔐 Gestion Utilisateurs":
    if not require_auth(['admin']):
        st.stop()

    st.markdown('<p class="main-header">🔐 Gestion des Utilisateurs</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Liste des utilisateurs", "➕ Ajouter un utilisateur"])

    with tab1:
        users = get_all_users()
        if users:
            df_users = pd.DataFrame(users)
            st.dataframe(df_users, use_container_width=True)
        else:
            st.info("Aucun utilisateur trouvé")

    with tab2:
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)

            with col1:
                new_username = st.text_input("Nom d'utilisateur *")
                new_nom = st.text_input("Nom *")
                new_email = st.text_input("Email *")

            with col2:
                new_password = st.text_input("Mot de passe *", type="password")
                new_prenom = st.text_input("Prénom *")
                new_role = st.selectbox("Rôle *", ["admin", "professeur", "etudiant"])

            submit = st.form_submit_button("Créer l'utilisateur")

            if submit:
                if all([new_username, new_password, new_nom, new_prenom, new_email]):
                    if create_user(new_username, new_password, new_role, new_nom, new_prenom, new_email):
                        st.success(f"✅ Utilisateur {new_username} créé avec succès !")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la création")
                else:
                    st.warning("⚠️ Tous les champs sont obligatoires")

# ==========================================
# FOOTER
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown("**🎓 Système de Gestion d'Examens**")
st.sidebar.markdown("Version 1.0 - Décembre 2025")