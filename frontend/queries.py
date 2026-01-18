# frontend/queries.py
import pandas as pd
from db_utils import get_connection


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
    FROM ETUDIANT e
    JOIN FORMATION f ON e.id_form = f.id_form
    JOIN DEPARTEMENT d ON f.id_dept = d.id_dept
    ORDER BY d.nom, e.nom;
    """
    conn = get_connection()
    if conn:
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    return pd.DataFrame()


def load_exams_per_professor():
    """Nombre d'examens par professeur par jour"""
    query = """
    SELECT 
        p.nom || ' ' || p.prenom AS professeur,
        p.specialite,
        COUNT(*) AS nb_examens,
        e.date_exam::date AS jour,
        STRING_AGG(m.nom, ', ') AS modules
    FROM SURVEILLANCE s
    JOIN EXAMEN e ON s.id_exam = e.id_exam
    JOIN PROFESSEUR p ON s.id_prof = p.id_prof
    JOIN MODULE m ON e.id_mod = m.id_mod
    GROUP BY p.nom, p.prenom, p.specialite, jour
    ORDER BY jour, professeur;
    """
    conn = get_connection()
    if conn:
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    return pd.DataFrame()


def load_students_per_module():
    """Nombre d'étudiants par module"""
    query = """
    SELECT 
        m.nom AS module,
        m.credits,
        m.coefficient,
        f.nom AS formation,
        COUNT(i.id_etu) AS nb_etudiants
    FROM MODULE m
    LEFT JOIN INSCRIPTION i ON m.id_mod = i.id_mod
    JOIN FORMATION f ON m.id_form = f.id_form
    GROUP BY m.nom, m.credits, m.coefficient, f.nom
    ORDER BY nb_etudiants DESC;
    """
    conn = get_connection()
    if conn:
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    return pd.DataFrame()


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
    FROM EXAMEN e
    JOIN MODULE m ON e.id_mod = m.id_mod
    JOIN LIEU_EXAMEN l ON e.id_lieu = l.id_lieu
    LEFT JOIN INSCRIPTION i ON m.id_mod = i.id_mod
    LEFT JOIN SURVEILLANCE s ON e.id_exam = s.id_exam
    LEFT JOIN PROFESSEUR p ON s.id_prof = p.id_prof
    GROUP BY e.id_exam, e.date_exam, e.duree_min, e.type_examen, 
             e.session_examen, m.nom, l.nom, l.capacite
    ORDER BY e.date_exam;
    """
    conn = get_connection()
    if conn:
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    return pd.DataFrame()


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
    FROM LIEU_EXAMEN l
    LEFT JOIN EXAMEN e ON l.id_lieu = e.id_lieu
    LEFT JOIN (
        SELECT ex.id_exam, COUNT(i.id_etu) AS nb_inscrits
        FROM EXAMEN ex
        JOIN MODULE m ON ex.id_mod = m.id_mod
        LEFT JOIN INSCRIPTION i ON m.id_mod = i.id_mod
        GROUP BY ex.id_exam
    ) subq ON e.id_exam = subq.id_exam
    GROUP BY l.id_lieu, l.nom, l.capacite, l.type_lieu, l.batiment
    ORDER BY taux_occupation_pct DESC;
    """
    conn = get_connection()
    if conn:
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    return pd.DataFrame()


def load_student_exam_schedule(student_id):
    """Planning d'examens pour un étudiant spécifique"""
    query = """
    SELECT 
        e.date_exam,
        e.duree_min,
        m.nom AS module,
        m.credits,
        l.nom AS salle,
        l.batiment,
        i.statut,
        i.note
    FROM INSCRIPTION i
    JOIN MODULE m ON i.id_mod = m.id_mod
    JOIN EXAMEN e ON m.id_mod = e.id_mod
    JOIN LIEU_EXAMEN l ON e.id_lieu = l.id_lieu
    WHERE i.id_etu = %s
    ORDER BY e.date_exam;
    """
    conn = get_connection()
    if conn:
        df = pd.read_sql(query, conn, params=(student_id,))
        conn.close()
        return df
    return pd.DataFrame()


def get_constraint_violations():
    """Détecte les violations de contraintes potentielles"""
    violations = {
        "students_multiple_exams": [],
        "professors_overload": [],
        "room_overcapacity": []
    }

    conn = get_connection()
    if not conn:
        return violations

    cur = conn.cursor()

    # 1️⃣ Étudiants avec plusieurs examens le même jour
    cur.execute("""
        SELECT i.id_etu, e.nom || ' ' || e.prenom AS etudiant, 
               ex.date_exam::date AS jour, COUNT(*) AS nb_examens
        FROM INSCRIPTION i
        JOIN ETUDIANT e ON i.id_etu = e.id_etu
        JOIN EXAMEN ex ON i.id_mod = ex.id_mod
        GROUP BY i.id_etu, etudiant, jour
        HAVING COUNT(*) > 1;
    """)
    violations["students_multiple_exams"] = cur.fetchall()

    # 2️⃣ Professeurs avec plus de 3 examens/jour
    cur.execute("""
        SELECT s.id_prof, p.nom || ' ' || p.prenom AS professeur,
               e.date_exam::date AS jour, COUNT(*) AS nb_examens
        FROM SURVEILLANCE s
        JOIN PROFESSEUR p ON s.id_prof = p.id_prof
        JOIN EXAMEN e ON s.id_exam = e.id_exam
        GROUP BY s.id_prof, professeur, jour
        HAVING COUNT(*) > 3;
    """)
    violations["professors_overload"] = cur.fetchall()

    # 3️⃣ Salles dépassant leur capacité
    cur.execute("""
        SELECT e.id_exam, l.nom AS salle, l.capacite,
               COUNT(i.id_etu) AS nb_inscrits
        FROM EXAMEN e
        JOIN LIEU_EXAMEN l ON e.id_lieu = l.id_lieu
        JOIN MODULE m ON e.id_mod = m.id_mod
        LEFT JOIN INSCRIPTION i ON m.id_mod = i.id_mod
        GROUP BY e.id_exam, l.nom, l.capacite
        HAVING COUNT(i.id_etu) > l.capacite;
    """)
    violations["room_overcapacity"] = cur.fetchall()

    cur.close()
    conn.close()

    return violations


def get_dashboard_stats():
    """Statistiques générales pour le dashboard"""
    conn = get_connection()
    if not conn:
        return {}

    cur = conn.cursor()
    stats = {}

    # Nombre total d'étudiants
    cur.execute("SELECT COUNT(*) FROM ETUDIANT;")
    stats['total_students'] = cur.fetchone()[0]

    # Nombre total d'examens
    cur.execute("SELECT COUNT(*) FROM EXAMEN;")
    stats['total_exams'] = cur.fetchone()[0]

    # Nombre de professeurs
    cur.execute("SELECT COUNT(*) FROM PROFESSEUR;")
    stats['total_professors'] = cur.fetchone()[0]

    # Nombre de salles
    cur.execute("SELECT COUNT(*) FROM LIEU_EXAMEN;")
    stats['total_rooms'] = cur.fetchone()[0]

    # Capacité totale
    cur.execute("SELECT SUM(capacite) FROM LIEU_EXAMEN;")
    stats['total_capacity'] = cur.fetchone()[0]

    cur.close()
    conn.close()

    return stats


# ==========================================
# FONCTIONS POUR PLANIFICATION D'EXAMENS
# ==========================================

def get_available_rooms(date_exam, duree_min):
    """Récupère les salles disponibles pour une date/heure donnée"""
    conn = get_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()

        # Salles non occupées durant ce créneau
        cur.execute("""
        SELECT l.id_lieu, l.nom, l.capacite, l.type_lieu, l.batiment
        FROM LIEU_EXAMEN l
        WHERE l.id_lieu NOT IN (
            SELECT e.id_lieu
            FROM EXAMEN e
            WHERE 
                %s < (e.date_exam + (e.duree_min || ' minutes')::interval)
                AND (%s + (%s || ' minutes')::interval) > e.date_exam
        )
        ORDER BY l.capacite DESC;
        """, (date_exam, date_exam, duree_min))

        rooms = cur.fetchall()
        cur.close()
        conn.close()

        return [{
            'id_lieu': r[0],
            'nom': r[1],
            'capacite': r[2],
            'type_lieu': r[3],
            'batiment': r[4]
        } for r in rooms]

    except Exception as e:
        print(f"❌ Erreur récupération salles : {e}")
        if conn:
            conn.close()
        return []


def get_all_modules():
    """Récupère tous les modules disponibles"""
    conn = get_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT m.id_mod, m.nom, m.credits, m.coefficient, f.nom AS formation, 
               COUNT(i.id_etu) AS nb_inscrits
        FROM MODULE m
        JOIN FORMATION f ON m.id_form = f.id_form
        LEFT JOIN INSCRIPTION i ON m.id_mod = i.id_mod
        GROUP BY m.id_mod, m.nom, m.credits, m.coefficient, f.nom
        ORDER BY f.nom, m.nom;
        """)

        modules = cur.fetchall()
        cur.close()
        conn.close()

        return [{
            'id_mod': m[0],
            'nom': m[1],
            'credits': m[2],
            'coefficient': m[3],
            'formation': m[4],
            'nb_inscrits': m[5]
        } for m in modules]

    except Exception as e:
        print(f"❌ Erreur récupération modules : {e}")
        if conn:
            conn.close()
        return []


def get_all_professors():
    """Récupère tous les professeurs"""
    conn = get_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT p.id_prof, p.nom, p.prenom, p.specialite, d.nom AS departement
        FROM PROFESSEUR p
        JOIN DEPARTEMENT d ON p.id_dept = d.id_dept
        ORDER BY p.nom, p.prenom;
        """)

        profs = cur.fetchall()
        cur.close()
        conn.close()

        return [{
            'id_prof': p[0],
            'nom': p[1],
            'prenom': p[2],
            'specialite': p[3],
            'departement': p[4]
        } for p in profs]

    except Exception as e:
        print(f"❌ Erreur récupération professeurs : {e}")
        if conn:
            conn.close()
        return []


def get_all_rooms():
    """Récupère toutes les salles"""
    conn = get_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT id_lieu, nom, capacite, type_lieu, batiment, equipements
        FROM LIEU_EXAMEN
        ORDER BY capacite DESC;
        """)

        rooms = cur.fetchall()
        cur.close()
        conn.close()

        return [{
            'id_lieu': r[0],
            'nom': r[1],
            'capacite': r[2],
            'type_lieu': r[3],
            'batiment': r[4],
            'equipements': r[5]
        } for r in rooms]

    except Exception as e:
        print(f"❌ Erreur récupération salles : {e}")
        if conn:
            conn.close()
        return []


def create_exam(date_exam, duree_min, type_examen, session_examen, id_mod, id_lieu):
    """Crée un nouvel examen"""
    conn = get_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO EXAMEN (date_exam, duree_min, type_examen, session_examen, id_mod, id_lieu)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id_exam;
        """, (date_exam, duree_min, type_examen, session_examen, id_mod, id_lieu))

        id_exam = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        print(f"✅ Examen créé : ID {id_exam}")
        return id_exam

    except Exception as e:
        print(f"❌ Erreur création examen : {e}")
        if conn:
            conn.rollback()
            conn.close()
        return None


def assign_surveillance(id_exam, id_prof, role):
    """Assigne un surveillant à un examen"""
    conn = get_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO SURVEILLANCE (id_exam, id_prof, role)
        VALUES (%s, %s, %s);
        """, (id_exam, id_prof, role))

        conn.commit()
        cur.close()
        conn.close()

        print(f"✅ Surveillant assigné : Prof {id_prof} ({role})")
        return True

    except Exception as e:
        print(f"❌ Erreur assignation surveillant : {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def update_exam(id_exam, date_exam, duree_min, type_examen, session_examen, id_lieu):
    """Modifie un examen existant"""
    conn = get_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute("""
        UPDATE EXAMEN
        SET date_exam = %s, duree_min = %s, type_examen = %s, 
            session_examen = %s, id_lieu = %s
        WHERE id_exam = %s;
        """, (date_exam, duree_min, type_examen, session_examen, id_lieu, id_exam))

        conn.commit()
        cur.close()
        conn.close()

        print(f"✅ Examen {id_exam} modifié")
        return True

    except Exception as e:
        print(f"❌ Erreur modification examen : {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def delete_exam(id_exam):
    """Supprime un examen"""
    conn = get_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()

        # Supprimer d'abord les surveillances
        cur.execute("DELETE FROM SURVEILLANCE WHERE id_exam = %s;", (id_exam,))

        # Puis l'examen
        cur.execute("DELETE FROM EXAMEN WHERE id_exam = %s;", (id_exam,))

        conn.commit()
        cur.close()
        conn.close()

        print(f"✅ Examen {id_exam} supprimé")
        return True

    except Exception as e:
        print(f"❌ Erreur suppression examen : {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def get_exam_details(id_exam):
    """Récupère les détails d'un examen"""
    conn = get_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT 
            e.id_exam,
            e.date_exam,
            e.duree_min,
            e.type_examen,
            e.session_examen,
            m.id_mod,
            m.nom AS module,
            l.id_lieu,
            l.nom AS salle,
            l.capacite,
            COUNT(i.id_etu) AS nb_inscrits
        FROM EXAMEN e
        JOIN MODULE m ON e.id_mod = m.id_mod
        JOIN LIEU_EXAMEN l ON e.id_lieu = l.id_lieu
        LEFT JOIN INSCRIPTION i ON m.id_mod = i.id_mod
        WHERE e.id_exam = %s
        GROUP BY e.id_exam, e.date_exam, e.duree_min, e.type_examen, 
                 e.session_examen, m.id_mod, m.nom, l.id_lieu, l.nom, l.capacite;
        """, (id_exam,))

        exam = cur.fetchone()

        # Récupérer les surveillants
        cur.execute("""
        SELECT p.id_prof, p.nom, p.prenom, s.role
        FROM SURVEILLANCE s
        JOIN PROFESSEUR p ON s.id_prof = p.id_prof
        WHERE s.id_exam = %s;
        """, (id_exam,))

        surveillants = cur.fetchall()

        cur.close()
        conn.close()

        if exam:
            return {
                'id_exam': exam[0],
                'date_exam': exam[1],
                'duree_min': exam[2],
                'type_examen': exam[3],
                'session_examen': exam[4],
                'id_mod': exam[5],
                'module': exam[6],
                'id_lieu': exam[7],
                'salle': exam[8],
                'capacite': exam[9],
                'nb_inscrits': exam[10],
                'surveillants': [{
                    'id_prof': s[0],
                    'nom': s[1],
                    'prenom': s[2],
                    'role': s[3]
                } for s in surveillants]
            }
        return None

    except Exception as e:
        print(f"❌ Erreur récupération détails examen : {e}")
        if conn:
            conn.close()
        return None


def remove_surveillance(id_exam, id_prof):
    """Retire un surveillant d'un examen"""
    conn = get_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute("""
        DELETE FROM SURVEILLANCE 
        WHERE id_exam = %s AND id_prof = %s;
        """, (id_exam, id_prof))

        conn.commit()
        cur.close()
        conn.close()

        print(f"✅ Surveillant retiré de l'examen {id_exam}")
        return True

    except Exception as e:
        print(f"❌ Erreur retrait surveillant : {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def check_professor_availability(id_prof, date_exam):
    """Vérifie le nombre d'examens d'un prof un jour donné"""
    conn = get_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT COUNT(*) 
        FROM SURVEILLANCE s
        JOIN EXAMEN e ON s.id_exam = e.id_exam
        WHERE s.id_prof = %s 
        AND DATE(e.date_exam) = DATE(%s);
        """, (id_prof, date_exam))

        count = cur.fetchone()[0]
        cur.close()
        conn.close()

        return count

    except Exception as e:
        print(f"❌ Erreur vérification disponibilité : {e}")
        if conn:
            conn.close()
        return None


def load_student_own_exams(username):
    """Récupère les examens d'un étudiant connecté (basé sur son username)"""
    conn = get_connection()
    if not conn:
        return pd.DataFrame()

    try:
        # Récupérer l'id_etu à partir du username
        cur = conn.cursor()

        # Trouver l'étudiant correspondant au username
        cur.execute("""
        SELECT e.id_etu 
        FROM ETUDIANT e
        JOIN UTILISATEURS u ON LOWER(e.email) = LOWER(u.email)
        WHERE u.username = %s;
        """, (username,))

        result = cur.fetchone()

        if not result:
            cur.close()
            conn.close()
            return pd.DataFrame()

        id_etu = result[0]

        # Récupérer les examens de cet étudiant
        query = """
        SELECT 
            e.id_exam,
            e.date_exam,
            e.duree_min,
            e.type_examen,
            e.session_examen,
            m.nom AS module,
            m.credits,
            m.coefficient,
            l.nom AS salle,
            l.batiment,
            l.capacite,
            i.statut,
            i.note,
            STRING_AGG(DISTINCT p.nom || ' ' || p.prenom, ', ') AS surveillants
        FROM INSCRIPTION i
        JOIN MODULE m ON i.id_mod = m.id_mod
        JOIN EXAMEN e ON m.id_mod = e.id_mod
        JOIN LIEU_EXAMEN l ON e.id_lieu = l.id_lieu
        LEFT JOIN SURVEILLANCE s ON e.id_exam = s.id_exam
        LEFT JOIN PROFESSEUR p ON s.id_prof = p.id_prof
        WHERE i.id_etu = %s
        GROUP BY e.id_exam, e.date_exam, e.duree_min, e.type_examen, 
                 e.session_examen, m.nom, m.credits, m.coefficient,
                 l.nom, l.batiment, l.capacite, i.statut, i.note
        ORDER BY e.date_exam;
        """

        df = pd.read_sql(query, conn, params=(id_etu,))
        cur.close()
        conn.close()

        return df

    except Exception as e:
        print(f"❌ Erreur récupération examens étudiant : {e}")
        if conn:
            conn.close()
        return pd.DataFrame()


def get_student_id_from_username(username):
    """Récupère l'ID d'un étudiant à partir de son username"""
    conn = get_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT e.id_etu, e.nom, e.prenom, e.email, f.nom AS formation
        FROM ETUDIANT e
        JOIN UTILISATEURS u ON LOWER(e.email) = LOWER(u.email)
        JOIN FORMATION f ON e.id_form = f.id_form
        WHERE u.username = %s;
        """, (username,))

        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            return {
                'id_etu': result[0],
                'nom': result[1],
                'prenom': result[2],
                'email': result[3],
                'formation': result[4]
            }
        return None

    except Exception as e:
        print(f"❌ Erreur récupération ID étudiant : {e}")
        if conn:
            conn.close()
        return None


def get_all_rooms():
    """Récupère toutes les salles"""
    conn = get_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT id_lieu, nom, capacite, type_lieu, batiment
        FROM LIEU_EXAMEN
        ORDER BY nom;
        """)

        rooms = cur.fetchall()
        cur.close()
        conn.close()

        return [{
            'id_lieu': r[0],
            'nom': r[1],
            'capacite': r[2],
            'type_lieu': r[3],
            'batiment': r[4] if len(r) > 4 else 'N/A'
        } for r in rooms]

    except Exception as e:
        print(f"❌ Erreur get_all_rooms: {e}")
        if conn:
            conn.close()
        return []



def load_professor_surveillances(username):
        """Récupère les surveillances d'un professeur (basé sur son username)"""
        conn = get_connection()
        if not conn:
            return pd.DataFrame()

        try:
            cur = conn.cursor()

            # Trouver le professeur correspondant au username
            cur.execute("""
            SELECT p.id_prof 
            FROM PROFESSEUR p
            JOIN UTILISATEURS u ON LOWER(p.email) = LOWER(u.email)
            WHERE u.username = %s;
            """, (username,))

            result = cur.fetchone()

            if not result:
                cur.close()
                conn.close()
                return pd.DataFrame()

            id_prof = result[0]

            # Récupérer les surveillances de ce professeur
            query = """
            SELECT 
                e.id_exam,
                e.date_exam,
                e.duree_min,
                e.type_examen,
                e.session_examen,
                m.nom AS module,
                f.nom AS formation,
                f.niveau,
                l.nom AS salle,
                l.batiment,
                l.capacite,
                COUNT(DISTINCT i.id_etu) AS nb_inscrits,
                s.role,
                STRING_AGG(DISTINCT p2.nom || ' ' || p2.prenom, ', ') 
                    FILTER (WHERE p2.id_prof != %s) AS autres_surveillants
            FROM SURVEILLANCE s
            JOIN EXAMEN e ON s.id_exam = e.id_exam
            JOIN MODULE m ON e.id_mod = m.id_mod
            JOIN FORMATION f ON m.id_form = f.id_form
            JOIN LIEU_EXAMEN l ON e.id_lieu = l.id_lieu
            LEFT JOIN INSCRIPTION i ON m.id_mod = i.id_mod
            LEFT JOIN SURVEILLANCE s2 ON e.id_exam = s2.id_exam
            LEFT JOIN PROFESSEUR p2 ON s2.id_prof = p2.id_prof
            WHERE s.id_prof = %s
            GROUP BY e.id_exam, e.date_exam, e.duree_min, e.type_examen, 
                     e.session_examen, m.nom, f.nom, f.niveau,
                     l.nom, l.batiment, l.capacite, s.role
            ORDER BY e.date_exam;
            """

            df = pd.read_sql(query, conn, params=(id_prof, id_prof))
            cur.close()
            conn.close()

            return df

        except Exception as e:
            print(f"❌ Erreur récupération surveillances prof : {e}")
            if conn:
                conn.close()
            return pd.DataFrame()

def get_professor_id_from_username(username):
        """Récupère l'ID d'un professeur à partir de son username"""
        conn = get_connection()
        if not conn:
            return None

        try:
            cur = conn.cursor()
            cur.execute("""
            SELECT p.id_prof, p.nom, p.prenom, p.email, d.nom AS departement, p.specialite
            FROM PROFESSEUR p
            JOIN UTILISATEURS u ON LOWER(p.email) = LOWER(u.email)
            JOIN DEPARTEMENT d ON p.id_dept = d.id_dept
            WHERE u.username = %s;
            """, (username,))

            result = cur.fetchone()
            cur.close()
            conn.close()

            if result:
                return {
                    'id_prof': result[0],
                    'nom': result[1],
                    'prenom': result[2],
                    'email': result[3],
                    'departement': result[4],
                    'specialite': result[5]
                }
            return None

        except Exception as e:
            print(f"❌ Erreur récupération ID professeur : {e}")
            if conn:
                conn.close()
            return None
