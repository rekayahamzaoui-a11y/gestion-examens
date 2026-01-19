# main.py - VERSION CORRIGÉE
import streamlit as st  # ← AJOUTÉ !
import psycopg2
import os
import time
from collections import defaultdict
from datetime import date


# ==========================================
# CONNEXION À LA BASE DE DONNÉES (CORRIGÉE)
# ==========================================
@st.cache_resource
def get_database_connection():
    """
    Connexion à PostgreSQL qui fonctionne partout

    - En LOCAL: Utilise variables d'environnement ou valeurs par défaut
    - Sur STREAMLIT CLOUD: Utilise st.secrets

    Returns:
        psycopg2.connection ou None si échec
    """
    max_retries = 3
    retry_delay = 2

    for attempt in range(1, max_retries + 1):
        try:
            # Vérifier si on est sur Streamlit Cloud
            if hasattr(st, 'secrets') and 'database' in st.secrets:
                # ✅ MODE PRODUCTION (Streamlit Cloud)
                st.info(f"🔄 Tentative de connexion {attempt}/{max_retries} à Neon.tech...")

                conn = psycopg2.connect(
                    host=st.secrets["database"]["host"],
                    port=int(st.secrets["database"]["port"]),  # Convertir en int
                    database=st.secrets["database"]["dbname"],  # ← Utiliser "dbname"
                    user=st.secrets["database"]["user"],
                    password=st.secrets["database"]["password"],
                    sslmode=st.secrets["database"].get("sslmode", "require"),
                    connect_timeout=10
                )

                # Test de la connexion
                cur = conn.cursor()
                cur.execute("SELECT 1")
                cur.close()

                st.success("✅ Connecté à la base de données (Neon.tech)")
                return conn

            else:
                # ✅ MODE DÉVELOPPEMENT LOCAL
                st.info("🔄 Connexion à PostgreSQL local...")

                conn = psycopg2.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    port=int(os.getenv("DB_PORT", 5432)),
                    database=os.getenv("DB_NAME", "gestion_examens_db"),
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", "postgres"),
                    connect_timeout=5
                )

                st.info("✅ Connecté à PostgreSQL local")
                return conn

        except psycopg2.OperationalError as e:
            if attempt < max_retries:
                st.warning(f"⚠️ Échec tentative {attempt}/{max_retries}. Nouvelle tentative dans {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                st.error(f"""
                ❌ **Impossible de se connecter après {max_retries} tentatives**

                **Erreur:** {str(e)}

                **Solutions:**
                1. Vérifiez vos Secrets Streamlit (Settings → Secrets)
                2. Vérifiez que Neon.tech est actif
                3. Vérifiez votre connexion Internet

                **Configuration attendue:**
                ```toml
                [database]
                host = "ep-xxx.neon.tech"
                port = 5432
                dbname = "neondb"
                user = "neondb_owner"
                password = "npg_xxxxx"
                sslmode = "require"
                ```
                """)
                return None

        except Exception as e:
            st.error(f"❌ Erreur inattendue: {type(e).__name__} - {str(e)}")
            return None

    return None  # ← CORRIGÉ : Pas de parenthèse en trop !


# Alias pour compatibilité avec votre ancien code
def get_connection():
    """Alias pour get_database_connection()"""
    return get_database_connection()


# ==========================================
# INSERTION DES DONNÉES (OPTIMISÉE)
# ==========================================
def insert_initial_data():
    """Insère les données initiales avec gestion d'erreurs"""
    try:
        conn = get_connection()

        if conn is None:
            st.error("❌ Impossible d'insérer les données : pas de connexion BD")
            return False

        cur = conn.cursor()

        with st.spinner("📝 Insertion des données..."):

            # DEPARTEMENT
            st.write("📝 Insertion DEPARTEMENT...")
            cur.execute("""
            INSERT INTO DEPARTEMENT (nom, code) VALUES
            ('Informatique', 'INFO'),
            ('Mathématiques', 'MATH'),
            ('Physique', 'PHYS')
            ON CONFLICT DO NOTHING;
            """)

            # FORMATION
            st.write("📝 Insertion FORMATION...")
            cur.execute("""
            INSERT INTO FORMATION (nom, niveau, id_dept) VALUES
            ('Licence Info', 'L1', 1),
            ('Licence Math', 'L1', 2),
            ('Master Physique', 'M2', 3)
            ON CONFLICT DO NOTHING;
            """)

            # ETUDIANT
            st.write("📝 Insertion ETUDIANT...")
            cur.execute("""
            INSERT INTO ETUDIANT (nom, prenom, email, promo, id_form) VALUES
            ('Ali', 'Benali', 'ali@mail.com', '2025', 1),
            ('Sara', 'Khaled', 'sara@mail.com', '2025', 1),
            ('Omar', 'Ahmed', 'omar@mail.com', '2025', 2)
            ON CONFLICT DO NOTHING;
            """)

            # MODULE
            st.write("📝 Insertion MODULE...")
            cur.execute("""
            INSERT INTO MODULE (nom, credits, coefficient, id_form) VALUES
            ('Algorithmique', 5, 1.5, 1),
            ('Base de données', 4, 1.2, 1),
            ('Analyse', 6, 1.8, 2)
            ON CONFLICT DO NOTHING;
            """)

            # PROFESSEUR
            st.write("📝 Insertion PROFESSEUR...")
            cur.execute("""
            INSERT INTO PROFESSEUR (nom, prenom, email, specialite, id_dept) VALUES
            ('Fares', 'Slim', 'fares@mail.com', 'Info', 1),
            ('Nadia', 'Ali', 'nadia@mail.com', 'Math', 2)
            ON CONFLICT DO NOTHING;
            """)

            # LIEU_EXAMEN
            st.write("📝 Insertion LIEU_EXAMEN...")
            cur.execute("""
            INSERT INTO LIEU_EXAMEN (nom, capacite, type_lieu, batiment, equipements) VALUES
            ('Amphi A', 50, 'amphi', 'Batiment 1', 'Projecteur, Tableau'),
            ('Salle TD 1', 30, 'salle_TD', 'Batiment 2', 'Tableau, Ordinateurs')
            ON CONFLICT DO NOTHING;
            """)

            # EXAMEN
            st.write("📝 Insertion EXAMEN...")
            cur.execute("""
            INSERT INTO EXAMEN (date_exam, duree_min, type_examen, session_examen, id_mod, id_lieu) VALUES
            ('2025-12-27 09:00', 90, 'partiel', 'S1', 1, 1),
            ('2025-12-28 14:00', 120, 'partiel', 'S1', 2, 1),
            ('2025-12-29 10:00', 60, 'partiel', 'S1', 3, 2)
            ON CONFLICT DO NOTHING;
            """)

            # INSCRIPTION
            st.write("📝 Insertion INSCRIPTION...")
            cur.execute("""
            INSERT INTO INSCRIPTION (id_etu, id_mod, note, statut) VALUES
            (1, 1, NULL, 'inscrit'),
            (2, 1, NULL, 'inscrit'),
            (3, 3, NULL, 'inscrit')
            ON CONFLICT DO NOTHING;
            """)

            # SURVEILLANCE
            st.write("📝 Insertion SURVEILLANCE...")
            cur.execute("""
            INSERT INTO SURVEILLANCE (id_prof, id_exam, role) VALUES
            (1, 1, 'principal'),
            (1, 2, 'assistant'),
            (2, 3, 'principal')
            ON CONFLICT DO NOTHING;
            """)

        conn.commit()
        st.success("✅ Toutes les données insérées avec succès")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        st.error(f"❌ Erreur lors de l'insertion : {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return False


# ==========================================
# CONTRAINTES MÉTIER
# ==========================================
def check_student_exam_per_day(student_exams):
    """Vérifie qu'un étudiant n'a pas plus d'1 examen par jour"""
    exam_dates = set()
    for exam in student_exams:
        if exam["date"] in exam_dates:
            return False
        exam_dates.add(exam["date"])
    return True


def check_professor_exam_limit(professor_exams):
    """Vérifie qu'un professeur n'a pas plus de 3 examens par jour"""
    exams_per_day = defaultdict(int)
    for exam in professor_exams:
        exams_per_day[exam["date"]] += 1
        if exams_per_day[exam["date"]] > 3:
            return False
    return True


# ==========================================
# RÉCUPÉRATION DONNÉES (OPTIMISÉE)
# ==========================================
@st.cache_data(ttl=300)  # Cache 5 minutes
def get_student_exams_by_student(_conn):
    """Récupère examens par étudiant (avec cache)"""
    try:
        cur = _conn.cursor()
        cur.execute("""
            SELECT i.id_etu, ex.id_exam, ex.date_exam
            FROM INSCRIPTION i
            JOIN EXAMEN ex ON i.id_mod = ex.id_mod
            ORDER BY i.id_etu, ex.date_exam
            LIMIT 10000;  -- Limite de sécurité
        """)
        rows = cur.fetchall()
        cur.close()

        students_exams = {}
        for id_etu, id_exam, date_exam in rows:
            if id_etu not in students_exams:
                students_exams[id_etu] = []
            students_exams[id_etu].append({
                "id_exam": id_exam,
                "date": date_exam.date() if hasattr(date_exam, 'date') else date_exam
            })

        return students_exams

    except Exception as e:
        st.error(f"❌ Erreur récupération examens étudiants: {e}")
        return {}


@st.cache_data(ttl=300)
def get_professor_exams_by_professor(_conn):
    """Récupère examens par professeur (avec cache)"""
    try:
        cur = _conn.cursor()
        cur.execute("""
            SELECT s.id_prof, ex.id_exam, ex.date_exam
            FROM SURVEILLANCE s
            JOIN EXAMEN ex ON s.id_exam = ex.id_exam
            ORDER BY s.id_prof, ex.date_exam
            LIMIT 10000;  -- Limite de sécurité
        """)
        rows = cur.fetchall()
        cur.close()

        profs_exams = {}
        for id_prof, id_exam, date_exam in rows:
            if id_prof not in profs_exams:
                profs_exams[id_prof] = []
            profs_exams[id_prof].append({
                "id_exam": id_exam,
                "date": date_exam.date() if hasattr(date_exam, 'date') else date_exam
            })

        return profs_exams

    except Exception as e:
        st.error(f"❌ Erreur récupération examens professeurs: {e}")
        return {}


@st.cache_data(ttl=300)
def check_room_capacities(_conn):
    """Vérifie capacités des salles (avec cache)"""
    try:
        cur = _conn.cursor()
        cur.execute("""
            SELECT 
                ex.id_exam,
                l.nom AS salle,
                l.capacite,
                COUNT(i.id_etu) AS nb_inscrits
            FROM EXAMEN ex
            JOIN LIEU_EXAMEN l ON ex.id_lieu = l.id_lieu
            JOIN MODULE m ON ex.id_mod = m.id_mod
            JOIN INSCRIPTION i ON m.id_mod = i.id_mod
            GROUP BY ex.id_exam, l.nom, l.capacite
            LIMIT 1000;  -- Limite de sécurité
        """)
        rows = cur.fetchall()
        cur.close()

        violations = []
        for id_exam, salle, capacite, nb_inscrits in rows:
            if nb_inscrits > capacite:
                violations.append({
                    "id_exam": id_exam,
                    "salle": salle,
                    "capacite": capacite,
                    "nb_inscrits": nb_inscrits
                })

        return violations

    except Exception as e:
        st.error(f"❌ Erreur vérification capacités: {e}")
        return []


# ==========================================
# GÉNÉRATION ET VALIDATION DU PLANNING
# ==========================================
def generate_schedule():
    """Vérifie toutes les contraintes"""

    conn = get_connection()

    if conn is None:
        st.error("❌ Impossible de générer le planning : pas de connexion BD")
        return False

    try:
        st.subheader("🔍 Vérification des contraintes...")

        # Récupération des données
        with st.spinner("📊 Récupération des données..."):
            students_exams = get_student_exams_by_student(conn)
            profs_exams = get_professor_exams_by_professor(conn)

        st.info(f"📊 {len(students_exams)} étudiants | {len(profs_exams)} professeurs")

        violations_found = False

        # 1️⃣ Contrainte étudiants
        st.write("**1️⃣ Vérification : 1 examen/jour par étudiant**")
        violations_students = [
            id_etu for id_etu, exams in students_exams.items()
            if not check_student_exam_per_day(exams)
        ]

        if violations_students:
            st.error(f"❌ {len(violations_students)} étudiants avec plusieurs examens/jour")
            with st.expander("Voir les étudiants concernés"):
                st.write(violations_students[:10])  # Afficher max 10
            violations_found = True
        else:
            st.success("✅ Contrainte respectée")

        # 2️⃣ Contrainte professeurs
        st.write("**2️⃣ Vérification : Max 3 examens/jour par professeur**")
        violations_profs = [
            id_prof for id_prof, exams in profs_exams.items()
            if not check_professor_exam_limit(exams)
        ]

        if violations_profs:
            st.error(f"❌ {len(violations_profs)} professeurs dépassant 3 examens/jour")
            with st.expander("Voir les professeurs concernés"):
                st.write(violations_profs)
            violations_found = True
        else:
            st.success("✅ Contrainte respectée")

        # 3️⃣ Contrainte salles
        st.write("**3️⃣ Vérification : Capacités des salles**")
        violations_rooms = check_room_capacities(conn)

        if violations_rooms:
            st.error(f"❌ {len(violations_rooms)} salles en surcharge")
            with st.expander("Voir les détails"):
                for v in violations_rooms[:10]:  # Max 10
                    st.warning(f"Examen {v['id_exam']} : {v['salle']} ({v['nb_inscrits']}/{v['capacite']})")
            violations_found = True
        else:
            st.success("✅ Toutes les capacités OK")

        # Résultat final
        st.markdown("---")
        if not violations_found:
            st.success("✅ **Toutes les contraintes sont respectées !**")
            return True
        else:
            st.error("❌ **Planning invalide : des violations ont été détectées**")
            return False

    except Exception as e:
        st.error(f"❌ Erreur lors de la génération du planning: {e}")
        return False

    finally:
        if conn:
            conn.close()


# ==========================================
# BENCHMARK (OPTIMISÉ)
# ==========================================
def benchmark():
    """Test de performance avec affichage Streamlit"""

    conn = get_connection()

    if conn is None:
        st.error("❌ Impossible de faire le benchmark : pas de connexion BD")
        return

    try:
        cur = conn.cursor()

        queries = {
            "Inscriptions module 1": "SELECT * FROM INSCRIPTION WHERE id_mod = 1 LIMIT 100",
            "Étudiants": "SELECT * FROM ETUDIANT LIMIT 100",
            "Examens": "SELECT * FROM EXAMEN LIMIT 100",
            "Surveillance prof 1": "SELECT * FROM SURVEILLANCE WHERE id_prof = 1 LIMIT 100"
        }

        st.subheader("📊 Benchmark des requêtes")

        results = []

        for label, query in queries.items():
            start = time.time()
            cur.execute(query)
            rows = cur.fetchall()
            end = time.time()

            execution_time = (end - start) * 1000
            results.append({
                "Requête": label,
                "Lignes": len(rows),
                "Temps (ms)": f"{execution_time:.2f}"
            })

        # Affichage sous forme de tableau
        import pandas as pd
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)

        cur.close()
        conn.close()

    except Exception as e:
        st.error(f"❌ Erreur benchmark: {e}")


# ==========================================
# INTERFACE STREAMLIT PRINCIPALE
# ==========================================
def main():
    """Interface principale Streamlit"""

    st.set_page_config(
        page_title="Gestion Examens",
        page_icon="📚",
        layout="wide"
    )

    st.title("🚀 Système de Gestion d'Examens")
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("🎛️ Actions")

        action = st.radio(
            "Choisissez une action",
            [
                "🔌 Test Connexion",
                "📝 Insérer Données",
                "✅ Valider Planning",
                "📊 Benchmark"
            ]
        )

    # Actions
    if action == "🔌 Test Connexion":
        st.header("🔌 Test de Connexion PostgreSQL")

        if st.button("Tester la connexion", type="primary"):
            conn = get_connection()
            if conn:
                st.balloons()
                conn.close()

    elif action == "📝 Insérer Données":
        st.header("📝 Insertion des Données Initiales")

        st.warning("⚠️ Cette action va insérer des données de test dans la base.")

        if st.button("Insérer les données", type="primary"):
            success = insert_initial_data()
            if success:
                st.balloons()

    elif action == "✅ Valider Planning":
        st.header("✅ Validation du Planning")

        if st.button("Vérifier les contraintes", type="primary"):
            is_valid = generate_schedule()
            if is_valid:
                st.balloons()

    elif action == "📊 Benchmark":
        st.header("📊 Benchmark de Performance")

        if st.button("Lancer le benchmark", type="primary"):
            benchmark()


# ==========================================
# POINT D'ENTRÉE
# ==========================================
if __name__ == "__main__":
    main()