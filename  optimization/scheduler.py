# optimization/scheduler.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constraints import (
    check_student_exam_per_day,
    check_professor_exam_limit,
)
from db.connection import get_connection


def get_student_exams_by_student():
    """Récupère les examens PAR étudiant"""
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
    """Récupère les examens PAR professeur"""
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
    """Vérifie capacité des salles"""
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
    print("🔍 Récupération des données...")

    students_exams = get_student_exams_by_student()
    profs_exams = get_professor_exams_by_professor()

    print(f"📊 {len(students_exams)} étudiants | {len(profs_exams)} professeurs\n")

    # 1️⃣ Étudiants
    violations_students = [id_etu for id_etu, exams in students_exams.items()
                           if not check_student_exam_per_day(exams)]

    if violations_students:
        print(f"❌ Étudiants avec plusieurs examens/jour : {violations_students}")
        return False
    print("✅ 1 examen/jour par étudiant")

    # 2️⃣ Professeurs
    violations_profs = [id_prof for id_prof, exams in profs_exams.items()
                        if not check_professor_exam_limit(exams)]

    if violations_profs:
        print(f"❌ Professeurs dépassant 3 examens/jour : {violations_profs}")
        return False
    print("✅ Max 3 examens/jour par professeur")

    # 3️⃣ Salles
    violations_rooms = check_room_capacities()
    if violations_rooms:
        print("❌ Capacité des salles dépassée :")
        for v in violations_rooms:
            print(f"   Examen {v['id_exam']} : {v['salle']} ({v['nb_inscrits']}/{v['capacite']})")
        return False
    print("✅ Capacités des salles OK")

    print("\n✅ Toutes les contraintes respectées")
    return True


if __name__ == "__main__":
    generate_schedule()