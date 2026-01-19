# frontend/queries.py
import pandas as pd
from db_utils import get_connection
import streamlit as st


# ==========================================
# REQUÊTES D'ANALYSE
# ==========================================

def load_students_by_department():
    """Liste des étudiants par département"""
    query = """
    SELECT 
        d.nom AS departement,
        d.code,
        e.nom,
        e.prenom,
        e.email,
        f.nom AS formation,
        f.niveau
    FROM etudiant e
    JOIN formation f ON e.id_form = f.id_form
    JOIN departement d ON f.id_dept = d.id_dept
    ORDER BY d.nom, e.nom;
    """

    conn = None
    try:
        conn = get_connection()
        if not conn:
            st.error("❌ Pas de connexion DB")
            return pd.DataFrame()

        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"❌ Erreur chargement étudiants: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def load_exams_per_professor():
    """Nombre d'examens par professeur par jour"""
    query = """
    SELECT 
        p.nom || ' ' || p.prenom AS professeur,
        p.specialite,
        COUNT(*) AS nb_examens,
        e.date_exam::date AS jour,
        STRING_AGG(m.nom, ', ') AS modules
    FROM surveillance s
    JOIN examen e ON s.id_exam = e.id_exam
    JOIN professeur p ON s.id_prof = p.id_prof
    JOIN module m ON e.id_mod = m.id_mod
    GROUP BY p.nom, p.prenom, p.specialite, jour
    ORDER BY jour, professeur;
    """

    conn = None
    try:
        conn = get_connection()
        if not conn:
            return pd.DataFrame()

        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def load_students_per_module():
    """Nombre d'étudiants par module"""
    query = """
    SELECT 
        m.nom AS module,
        m.credits,
        m.coefficient,
        f.nom AS formation,
        COUNT(i.id_etu) AS nb_etudiants
    FROM module m
    LEFT JOIN inscription i ON m.id_mod = i.id_mod
    JOIN formation f ON m.id_form = f.id_form
    GROUP BY m.nom, m.credits, m.coefficient, f.nom
    ORDER BY nb_etudiants DESC;
    """

    conn = None
    try:
        conn = get_connection()
        if not conn:
            return pd.DataFrame()

        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def load_exam_schedule():
    """Planning complet des examens"""
    query = """
    SELECT 
        e.id_exam,
        e.date_exam,
        e.duree_min,
        e.type_examen,
        e.session_examen,
        m.nom AS module,
        l.nom AS salle,
        l.capacite,
        COUNT(DISTINCT i.id_etu) AS nb_inscrits,
        STRING_AGG(DISTINCT p.nom || ' ' || p.prenom, ', ') AS surveillants,
        STRING_AGG(DISTINCT s.role, ', ') AS roles
    FROM examen e
    JOIN module m ON e.id_mod = m.id_mod
    JOIN lieu_examen l ON e.id_lieu = l.id_lieu
    LEFT JOIN inscription i ON m.id_mod = i.id_mod
    LEFT JOIN surveillance s ON e.id_exam = s.id_exam
    LEFT JOIN professeur p ON s.id_prof = p.id_prof
    GROUP BY e.id_exam, e.date_exam, e.duree_min, e.type_examen, 
             e.session_examen, m.nom, l.nom, l.capacite
    ORDER BY e.date_exam;
    """

    conn = None
    try:
        conn = get_connection()
        if not conn:
            return pd.DataFrame()

        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def load_room_occupancy():
    """Taux d'occupation des salles"""
    query = """
    SELECT 
        l.nom AS salle,
        l.capacite,
        l.type_lieu,
        l.batiment,
        COUNT(e.id_exam) AS nb_examens,
        COALESCE(ROUND(AVG(subq.nb_inscrits), 1), 0) AS moy_occupation,
        COALESCE(ROUND(AVG(subq.nb_inscrits) * 100.0 / l.capacite, 1), 0) AS taux_occupation_pct
    FROM lieu_examen l
    LEFT JOIN examen e ON l.id_lieu = e.id_lieu
    LEFT JOIN (
        SELECT ex.id_exam, COUNT(i.id_etu) AS nb_inscrits
        FROM examen ex
        JOIN module m ON ex.id_mod = m.id_mod
        LEFT JOIN inscription i ON m.id_mod = i.id_mod
        GROUP BY ex.id_exam
    ) subq ON e.id_exam = subq.id_exam
    GROUP BY l.id_lieu, l.nom, l.capacite, l.type_lieu, l.batiment
    ORDER BY taux_occupation_pct DESC;
    """

    conn = None
    try:
        conn = get_connection()
        if not conn:
            return pd.DataFrame()

        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def get_constraint_violations():
    """Détecte les violations de contraintes potentielles"""
    violations = {
        "students_multiple_exams": [],
        "professors_overload": [],
        "room_overcapacity": []
    }

    conn = None
    try:
        conn = get_connection()
        if not conn:
            return violations

        cur = conn.cursor()

        # 1️⃣ Étudiants avec plusieurs examens le même jour
        cur.execute("""
            SELECT i.id_etu, e.nom || ' ' || e.prenom AS etudiant, 
                   ex.date_exam::date AS jour, COUNT(*) AS nb_examens
            FROM inscription i
            JOIN etudiant e ON i.id_etu = e.id_etu
            JOIN examen ex ON i.id_mod = ex.id_mod
            GROUP BY i.id_etu, etudiant, jour
            HAVING COUNT(*) > 1;
        """)
        violations["students_multiple_exams"] = cur.fetchall()

        # 2️⃣ Professeurs avec plus de 3 examens/jour
        cur.execute("""
            SELECT s.id_prof, p.nom || ' ' || p.prenom AS professeur,
                   e.date_exam::date AS jour, COUNT(*) AS nb_examens
            FROM surveillance s
            JOIN professeur p ON s.id_prof = p.id_prof
            JOIN examen e ON s.id_exam = e.id_exam
            GROUP BY s.id_prof, professeur, jour
            HAVING COUNT(*) > 3;
        """)
        violations["professors_overload"] = cur.fetchall()

        # 3️⃣ Salles dépassant leur capacité
        cur.execute("""
            SELECT e.id_exam, l.nom AS salle, l.capacite,
                   COUNT(i.id_etu) AS nb_inscrits
            FROM examen e
            JOIN lieu_examen l ON e.id_lieu = l.id_lieu
            JOIN module m ON e.id_mod = m.id_mod
            LEFT JOIN inscription i ON m.id_mod = i.id_mod
            GROUP BY e.id_exam, l.nom, l.capacite
            HAVING COUNT(i.id_etu) > l.capacite;
        """)
        violations["room_overcapacity"] = cur.fetchall()

        cur.close()
        return violations

    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        return violations
    finally:
        if conn:
            conn.close()


def get_dashboard_stats():
    """Statistiques générales pour le dashboard"""
    stats = {
        'total_students': 0,
        'total_exams': 0,
        'total_professors': 0,
        'total_rooms': 0,
        'total_capacity': 0
    }

    conn = None
    try:
        conn = get_connection()
        if not conn:
            return stats

        cur = conn.cursor()

        # Nombre total d'étudiants
        cur.execute("SELECT COUNT(*) FROM etudiant;")
        stats['total_students'] = cur.fetchone()[0]

        # Nombre total d'examens
        cur.execute("SELECT COUNT(*) FROM examen;")
        stats['total_exams'] = cur.fetchone()[0]

        # Nombre de professeurs
        cur.execute("SELECT COUNT(*) FROM professeur;")
        stats['total_professors'] = cur.fetchone()[0]

        # Nombre de salles
        cur.execute("SELECT COUNT(*) FROM lieu_examen;")
        stats['total_rooms'] = cur.fetchone()[0]

        # Capacité totale
        cur.execute("SELECT COALESCE(SUM(capacite), 0) FROM lieu_examen;")
        stats['total_capacity'] = cur.fetchone()[0]

        cur.close()
        return stats

    except Exception as e:
        st.error(f"❌ Erreur stats: {e}")
        return stats
    finally:
        if conn:
            conn.close()


# Placeholder pour autres fonctions
def get_available_rooms(date_exam, duree_min):
    return []


def get_all_modules():
    return []


def get_all_professors():
    return []


def create_exam(*args):
    return None


def assign_surveillance(*args):
    return False


def update_exam(*args):
    return False


def delete_exam(*args):
    return False


def load_student_own_exams(username):
    return pd.DataFrame()


def get_student_id_from_username(username):
    return None


def get_exam_details(id_exam):
    return None


def load_professor_surveillances(username):
    return pd.DataFrame()


def get_professor_id_from_username(username):
    return None


def get_all_rooms():
    return []