# optimization/constraints.py

from collections import defaultdict
from datetime import date


# =====================================================
#  Vérifier : 1 étudiant ne passe pas 2 examens le même jour
# =====================================================

def check_student_exam_per_day(student_exams):
    """
    student_exams : liste de dictionnaires
    Exemple :
    [
        {"id_exam": 1, "date": date(2025, 12, 27)},
        {"id_exam": 2, "date": date(2025, 12, 28)}
    ]
    """
    exam_dates = set()

    for exam in student_exams:
        if exam["date"] in exam_dates:
            return False  # ❌ Contrainte violée
        exam_dates.add(exam["date"])

    return True  # ✅ OK


# =====================================================
# 2️⃣ Vérifier : capacité maximale de la salle
# =====================================================

def check_room_capacity(nb_students, room_capacity):
    """
    nb_students    : nombre d'étudiants inscrits
    room_capacity  : capacité de la salle
    """
    return nb_students <= room_capacity


# =====================================================
# 3️⃣ Vérifier : max 3 examens par jour pour un professeur
# =====================================================

def check_professor_exam_limit(professor_exams):
    """
    professor_exams : liste de dictionnaires
    Exemple :
    [
        {"id_exam": 1, "date": date(2025, 12, 27)},
        {"id_exam": 2, "date": date(2025, 12, 27)}
    ]
    """

    exams_per_day = defaultdict(int)

    for exam in professor_exams:
        exams_per_day[exam["date"]] += 1
        if exams_per_day[exam["date"]] > 3:
            return False  # ❌ Trop d'examens ce jour

    return True  # ✅ OK


# =====================================================
# 4️⃣ Vérification globale (utile pour l'optimisation)
# =====================================================

def check_all_constraints(student_exams, professor_exams, nb_students, room_capacity):
    """
    Vérifie toutes les contraintes métiers
    """

    if not check_student_exam_per_day(student_exams):
        return False, "Étudiant a plusieurs examens le même jour"

    if not check_professor_exam_limit(professor_exams):
        return False, "Professeur dépasse 3 examens par jour"

    if not check_room_capacity(nb_students, room_capacity):
        return False, "Capacité de la salle insuffisante"

    return True, "Toutes les contraintes sont respectées"
