# main.py
import psycopg2
import time
from collections import defaultdict
from datetime import date


# ==========================================
# CONNEXION À LA BASE DE DONNÉES
# ==========================================
def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="gestion_examens_db",
        user="postgres",
        password="rekaya22"
    )


# ==========================================
# INSERTION DES DONNÉES
# ==========================================
def insert_initial_data():
    try:
        conn = get_connection()
        cur = conn.cursor()

        print("📝 Insertion DEPARTEMENT...")
        cur.execute("""
        INSERT INTO DEPARTEMENT (nom, code) VALUES
        ('Informatique', 'INFO'),
        ('Mathématiques', 'MATH'),
        ('Physique', 'PHYS')
        ON CONFLICT DO NOTHING;
        """)

        print("📝 Insertion FORMATION...")
        cur.execute("""
        INSERT INTO FORMATION (nom, niveau, id_dept) VALUES
        ('Licence Info', 'L1', 1),
        ('Licence Math', 'L1', 2),
        ('Master Physique', 'M2', 3)
        ON CONFLICT DO NOTHING;
        """)

        print("📝 Insertion ETUDIANT...")
        cur.execute("""
        INSERT INTO ETUDIANT (nom, prenom, email, promo, id_form) VALUES
        ('Ali', 'Benali', 'ali@mail.com', '2025', 1),
        ('Sara', 'Khaled', 'sara@mail.com', '2025', 1),
        ('Omar', 'Ahmed', 'omar@mail.com', '2025', 2)
        ON CONFLICT DO NOTHING;
        """)

        print("📝 Insertion MODULE...")
        cur.execute("""
        INSERT INTO MODULE (nom, credits, coefficient, id_form) VALUES
        ('Algorithmique', 5, 1.5, 1),
        ('Base de données', 4, 1.2, 1),
        ('Analyse', 6, 1.8, 2)
        ON CONFLICT DO NOTHING;
        """)

        print("📝 Insertion PROFESSEUR...")
        cur.execute("""
        INSERT INTO PROFESSEUR (nom, prenom, email, specialite, id_dept) VALUES
        ('Fares', 'Slim', 'fares@mail.com', 'Info', 1),
        ('Nadia', 'Ali', 'nadia@mail.com', 'Math', 2)
        ON CONFLICT DO NOTHING;
        """)

        print("📝 Insertion LIEU_EXAMEN...")
        cur.execute("""
        INSERT INTO LIEU_EXAMEN (nom, capacite, type_lieu, batiment, equipements) VALUES
        ('Amphi A', 50, 'amphi', 'Batiment 1', 'Projecteur, Tableau'),
        ('Salle TD 1', 30, 'salle_TD', 'Batiment 2', 'Tableau, Ordinateurs')
        ON CONFLICT DO NOTHING;
        """)

        print("📝 Insertion EXAMEN...")
        cur.execute("""
        INSERT INTO EXAMEN (date_exam, duree_min, type_examen, session_examen, id_mod, id_lieu) VALUES
        ('2025-12-27 09:00', 90, 'partiel', 'S1', 1, 1),
        ('2025-12-28 14:00', 120, 'partiel', 'S1', 2, 1),
        ('2025-12-29 10:00', 60, 'partiel', 'S1', 3, 2)
        ON CONFLICT DO NOTHING;
        """)

        print("📝 Insertion INSCRIPTION...")
        cur.execute("""
        INSERT INTO INSCRIPTION (id_etu, id_mod, note, statut) VALUES
        (1, 1, NULL, 'inscrit'),
        (2, 1, NULL, 'inscrit'),
        (3, 3, NULL, 'inscrit')
        ON CONFLICT DO NOTHING;
        """)

        print("📝 Insertion SURVEILLANCE...")
        cur.execute("""
        INSERT INTO SURVEILLANCE (id_prof, id_exam, role) VALUES
        (1, 1, 'principal'),
        (1, 2, 'assistant'),
        (2, 3, 'principal')
        ON CONFLICT DO NOTHING;
        """)

        conn.commit()
        print("✅ Toutes les données insérées")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Erreur insertion : {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()


# ==========================================
# CONTRAINTES MÉTIER
# ==========================================
def check_student_exam_per_day(student_exams):
    """1 examen par jour max pour un étudiant"""
    exam_dates = set()
    for exam in student_exams:
        if exam["date"] in exam_dates:
            return False
        exam_dates.add(exam["date"])
    return True


def check_professor_exam_limit(professor_exams):
    """Max 3 examens par jour pour un professeur"""
    exams_per_day = defaultdict(int)
    for exam in professor_exams:
        exams_per_day[exam["date"]] += 1
        if exams_per_day[exam["date"]] > 3:
            return False
    return True


# ==========================================
# SCHEDULER - VÉRIFICATION DES CONTRAINTES
# ==========================================
def get_student_exams_by_student():
    """Récupère examens par étudiant"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT i.id_etu, ex.id_exam, ex.date_exam
        FROM INSCRIPTION i
        JOIN EXAMEN ex ON i.id_mod = ex.id_mod
        ORDER BY i.id_etu, ex.date_exam;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    students_exams = {}
    for id_etu, id_exam, date_exam in rows:
        if id_etu not in students_exams:
            students_exams[id_etu] = []
        students_exams[id_etu].append({
            "id_exam": id_exam,
            "date": date_exam.date()
        })

    return students_exams


def get_professor_exams_by_professor():
    """Récupère examens par professeur"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id_prof, ex.id_exam, ex.date_exam
        FROM SURVEILLANCE s
        JOIN EXAMEN ex ON s.id_exam = ex.id_exam
        ORDER BY s.id_prof, ex.date_exam;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    profs_exams = {}
    for id_prof, id_exam, date_exam in rows:
        if id_prof not in profs_exams:
            profs_exams[id_prof] = []
        profs_exams[id_prof].append({
            "id_exam": id_exam,
            "date": date_exam.date()
        })

    return profs_exams


def check_room_capacities():
    """Vérifie capacités des salles"""
    conn = get_connection()
    cur = conn.cursor()
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
        GROUP BY ex.id_exam, l.nom, l.capacite;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

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


def generate_schedule():
    """Vérifie toutes les contraintes"""
    print("🔍 Récupération des données...\n")

    students_exams = get_student_exams_by_student()
    profs_exams = get_professor_exams_by_professor()

    print(f"📊 {len(students_exams)} étudiants | {len(profs_exams)} professeurs\n")

    # 1️⃣ Contrainte étudiants
    violations_students = [id_etu for id_etu, exams in students_exams.items()
                           if not check_student_exam_per_day(exams)]

    if violations_students:
        print(f"❌ Étudiants avec plusieurs examens/jour : {violations_students}")
        return False
    print("✅ 1 examen/jour par étudiant")

    # 2️⃣ Contrainte professeurs
    violations_profs = [id_prof for id_prof, exams in profs_exams.items()
                        if not check_professor_exam_limit(exams)]

    if violations_profs:
        print(f"❌ Professeurs dépassant 3 examens/jour : {violations_profs}")
        return False
    print("✅ Max 3 examens/jour par professeur")

    # 3️⃣ Contrainte salles
    violations_rooms = check_room_capacities()
    if violations_rooms:
        print("❌ Capacité des salles dépassée :")
        for v in violations_rooms:
            print(f"   Examen {v['id_exam']} : {v['salle']} ({v['nb_inscrits']}/{v['capacite']})")
        return False
    print("✅ Capacités des salles OK")

    print("\n✅ Toutes les contraintes respectées")
    return True


# ==========================================
# BENCHMARK
# ==========================================
def benchmark():
    """Test de performance"""
    conn = get_connection()
    cur = conn.cursor()

    queries = {
        "Inscriptions module 1": "SELECT * FROM INSCRIPTION WHERE id_mod = 1",
        "Tous les étudiants": "SELECT * FROM ETUDIANT",
        "Tous les examens": "SELECT * FROM EXAMEN",
        "Surveillance prof 1": "SELECT * FROM SURVEILLANCE WHERE id_prof = 1"
    }

    print("\n📊 Benchmark des requêtes\n")

    for label, query in queries.items():
        start = time.time()
        cur.execute(query)
        rows = cur.fetchall()
        end = time.time()
        print(f"✅ {label}: {len(rows)} lignes en {(end - start) * 1000:.2f}ms")

    cur.close()
    conn.close()


# ==========================================
# PROGRAMME PRINCIPAL
# ==========================================
def main():
    print("=" * 50)
    print("🚀 SYSTÈME DE GESTION D'EXAMENS")
    print("=" * 50)

    # Test connexion
    print("\n1️⃣ Test de connexion PostgreSQL...")
    try:
        conn = get_connection()
        print("✅ Connexion réussie")
        conn.close()
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return

    # Insertion données
    print("\n2️⃣ Insertion des données...\n")
    insert_initial_data()

    # Vérification planning
    print("\n3️⃣ Vérification des contraintes...\n")
    if generate_schedule():
        print("\n✅ Planning validé : prêt pour le frontend")
    else:
        print("\n❌ Planning invalide")

    # Benchmark
    benchmark()

    print("\n" + "=" * 50)
    print("✅ Processus terminé")
    print("=" * 50)


if __name__ == "__main__":
    main()