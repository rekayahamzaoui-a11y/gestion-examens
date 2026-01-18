# frontend/scheduler_engine.py
from ortools.sat.python import cp_model
from datetime import datetime, timedelta
import pandas as pd
from db_utils import get_connection


class ExamScheduler:
    """Générateur automatique d'emplois du temps - VERSION ULTRA-STRICTE"""

    def __init__(self):
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()

    def get_planning_data_by_dept(self, id_dept, niveaux):
        """Récupère modules, salles et profs pour un département"""
        conn = get_connection()
        if not conn:
            return None

        cur = conn.cursor()

        # Modules du département
        cur.execute("""
        SELECT m.id_mod, m.nom, f.nom AS formation, f.id_form, f.niveau,
               COUNT(DISTINCT i.id_etu) AS nb_inscrits
        FROM MODULE m
        JOIN FORMATION f ON m.id_form = f.id_form
        LEFT JOIN INSCRIPTION i ON m.id_mod = i.id_mod
        WHERE f.id_dept = %s AND f.niveau = ANY(%s)
        GROUP BY m.id_mod, m.nom, f.nom, f.id_form, f.niveau
        HAVING COUNT(DISTINCT i.id_etu) > 0
        ORDER BY f.niveau, f.id_form, m.id_mod;
        """, (id_dept, niveaux))
        modules = cur.fetchall()

        # Toutes les salles
        cur.execute("""
        SELECT id_lieu, nom, capacite, type_lieu
        FROM LIEU_EXAMEN
        ORDER BY capacite DESC;
        """)
        salles = cur.fetchall()

        # Profs du département
        cur.execute("""
        SELECT id_prof, nom, prenom, specialite
        FROM PROFESSEUR
        WHERE id_dept = %s
        ORDER BY id_prof;
        """, (id_dept,))
        profs = cur.fetchall()

        cur.close()
        conn.close()

        return {
            'modules': modules,
            'salles': salles,
            'professeurs': profs
        }

    def generate_schedule_by_department(self, start_date, nb_jours, id_dept, niveaux):
        """Génère planning - APPROCHE SIMPLIFIÉE GARANTIE SANS CONFLIT"""

        data = self.get_planning_data_by_dept(id_dept, niveaux)
        if not data:
            return None

        modules = data['modules']
        salles = data['salles']
        profs = data['professeurs']

        # ========================================
        # RÉCUPÉRER LES EXAMENS DÉJÀ PLANIFIÉS
        # ========================================
        examens_existants = []
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT e.date_exam, e.id_lieu, e.duree_min, l.nom, m.nom, f.nom
            FROM EXAMEN e
            JOIN LIEU_EXAMEN l ON e.id_lieu = l.id_lieu
            JOIN MODULE m ON e.id_mod = m.id_mod
            JOIN FORMATION f ON m.id_form = f.id_form
            ORDER BY e.date_exam;
            """)
            examens_existants = cur.fetchall()
            cur.close()
            conn.close()

            if examens_existants:
                print(f"\n⚠️  {len(examens_existants)} examens DÉJÀ en base - ils seront évités\n")

        # Créer un set des créneaux occupés: (date, id_lieu)
        creneaux_occupes = set()
        for exam in examens_existants:
            creneaux_occupes.add((exam[0], exam[1]))

        if not modules:
            print(f"❌ Aucun module trouvé")
            return None

        print(f"\n{'=' * 70}")
        print(f"🎯 GÉNÉRATION PLANNING - APPROCHE SIMPLIFIÉE ANTI-CONFLIT")
        print(f"{'=' * 70}")
        print(f"Département : {id_dept}")
        print(f"Niveaux : {niveaux}")
        print(f"Modules : {len(modules)}")
        print(f"Salles : {len(salles)}")
        print(f"Profs : {len(profs)}")
        print(f"{'=' * 70}\n")

        # Créneaux
        creneaux = []
        for jour in range(nb_jours):
            date = start_date + timedelta(days=jour)
            creneaux.append({
                'date': date.replace(hour=9, minute=0),
                'duree': 180,
                'periode': 'matin',
                'jour': jour
            })
            creneaux.append({
                'date': date.replace(hour=14, minute=0),
                'duree': 180,
                'periode': 'apres-midi',
                'jour': jour
            })

        num_modules = len(modules)
        num_creneaux = len(creneaux)
        num_salles = len(salles)
        num_profs = len(profs)

        print(f"📊 {num_modules} modules, {num_creneaux} créneaux, {num_salles} salles\n")

        # ========================================
        # NOUVELLE APPROCHE: 1 VARIABLE GLOBALE
        # ========================================

        # Variable unique: module M planifié au créneau C dans la salle S
        # 0 = non planifié, 1 = planifié
        x = {}
        for m in range(num_modules):
            for c in range(num_creneaux):
                for s in range(num_salles):
                    x[(m, c, s)] = self.model.NewBoolVar(f'x_{m}_{c}_{s}')

        print("🔒 CONTRAINTES ULTRA-STRICTES:\n")

        # ========================================
        # C1: Chaque module = EXACTEMENT 1 créneau + 1 salle
        # ========================================
        print("   ✅ C1: Chaque module assigné une seule fois")
        for m in range(num_modules):
            self.model.Add(
                sum(x[(m, c, s)]
                    for c in range(num_creneaux)
                    for s in range(num_salles)) == 1
            )

        # ========================================
        # C2: ⚠️ CRITIQUE - UNE SALLE = MAX 1 MODULE PAR CRÉNEAU
        # ========================================
        print("   ✅ C2: INTERDICTION ABSOLUE - 1 salle = 1 examen/créneau")
        for c in range(num_creneaux):
            for s in range(num_salles):
                # SOMME <= 1 signifie: AU MAXIMUM 1 module peut être dans cette salle à ce créneau
                self.model.Add(
                    sum(x[(m, c, s)] for m in range(num_modules)) <= 1
                )

        # ========================================
        # C3: Capacité des salles
        # ========================================
        print("   ✅ C3: Respect capacité salles")
        for m in range(num_modules):
            nb_inscrits = modules[m][5]
            for c in range(num_creneaux):
                for s in range(num_salles):
                    capacite_salle = salles[s][2]
                    if nb_inscrits > capacite_salle:
                        # Forcer x[(m,c,s)] = 0
                        self.model.Add(x[(m, c, s)] == 0)

        # ========================================
        # C3bis: ⚠️ ÉVITER LES CRÉNEAUX DÉJÀ OCCUPÉS EN BASE
        # ========================================
        if creneaux_occupes:
            print(f"   ✅ C3bis: Éviter {len(creneaux_occupes)} créneaux déjà occupés")
            for m in range(num_modules):
                for c in range(num_creneaux):
                    for s in range(num_salles):
                        date_creneau = creneaux[c]['date']
                        id_salle = salles[s][0]

                        # Si ce créneau est déjà occupé, interdire cette affectation
                        if (date_creneau, id_salle) in creneaux_occupes:
                            self.model.Add(x[(m, c, s)] == 0)

        # ========================================
        # C4: 1 examen/jour par formation
        # ========================================
        print("   ✅ C4: 1 examen/jour/formation")
        formations = {}
        for idx, module in enumerate(modules):
            form_id = module[3]
            if form_id not in formations:
                formations[form_id] = []
            formations[form_id].append(idx)

        for form_id, module_indices in formations.items():
            for jour in range(nb_jours):
                creneaux_jour = [c for c in range(num_creneaux) if creneaux[c]['jour'] == jour]
                self.model.Add(
                    sum(x[(m, c, s)]
                        for m in module_indices
                        for c in creneaux_jour
                        for s in range(num_salles)) <= 1
                )

        # ========================================
        # OBJECTIF: Minimiser le nombre de salles
        # ========================================
        salles_utilisees = []
        for s in range(num_salles):
            salle_used = self.model.NewBoolVar(f'used_s{s}')
            # Une salle est utilisée si au moins 1 examen y a lieu
            self.model.AddMaxEquality(
                salle_used,
                [x[(m, c, s)] for m in range(num_modules) for c in range(num_creneaux)]
            )
            salles_utilisees.append(salle_used)

        self.model.Minimize(sum(salles_utilisees))

        # ========================================
        # RÉSOLUTION
        # ========================================
        print("\n🔄 RÉSOLUTION...\n")

        self.solver.parameters.max_time_in_seconds = 300.0
        self.solver.parameters.num_search_workers = 12
        self.solver.parameters.log_search_progress = False

        # Stratégie: forcer la recherche de solutions valides
        self.solver.parameters.linearization_level = 2
        self.solver.parameters.cp_model_presolve = True

        status = self.solver.Solve(self.model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f"{'=' * 70}")
            print("✅ SOLUTION TROUVÉE")
            print(f"{'=' * 70}\n")

            planning = []

            # Extraire les affectations
            for m in range(num_modules):
                for c in range(num_creneaux):
                    for s in range(num_salles):
                        if self.solver.Value(x[(m, c, s)]) == 1:
                            # Assigner des surveillants aléatoires (simple)
                            surveillants = [profs[m % num_profs]]
                            if num_profs > 1:
                                surveillants.append(profs[(m + 1) % num_profs])

                            planning.append({
                                'module_id': modules[m][0],
                                'module_nom': modules[m][1],
                                'formation': modules[m][2],
                                'niveau': modules[m][4],
                                'nb_inscrits': modules[m][5],
                                'date_exam': creneaux[c]['date'],
                                'duree_min': creneaux[c]['duree'],
                                'salle_id': salles[s][0],
                                'salle_nom': salles[s][1],
                                'capacite': salles[s][2],
                                'surveillants': surveillants
                            })

            planning.sort(key=lambda x: x['date_exam'])

            # ========================================
            # VÉRIFICATION POST-GÉNÉRATION
            # ========================================
            print("🔍 VÉRIFICATION ANTI-CONFLIT:\n")

            conflicts_detected = []
            occupations = {}  # (créneau, salle) -> [examens]

            for exam in planning:
                key = (exam['date_exam'], exam['salle_id'])
                if key not in occupations:
                    occupations[key] = []
                occupations[key].append(exam)

            # Détecter les doublons
            for key, exams_list in occupations.items():
                if len(exams_list) > 1:
                    conflicts_detected.append((key, exams_list))

            if conflicts_detected:
                print("   ❌ CONFLITS DÉTECTÉS:")
                for (date, salle_id), exams_list in conflicts_detected:
                    salle_nom = exams_list[0]['salle_nom']
                    print(f"\n   🏫 {salle_nom} le {date}:")
                    for exam in exams_list:
                        print(f"      - {exam['module_nom']} ({exam['formation']})")

                print("\n❌ GÉNÉRATION ÉCHOUÉE - Conflits détectés")
                return None
            else:
                print("   ✅ AUCUN CONFLIT DÉTECTÉ")
                print(f"\n📋 {len(planning)} examens planifiés")
                print(f"🏫 {len(set([p['salle_id'] for p in planning]))} salles utilisées")
                print(f"📅 {len(set([p['date_exam'].date() for p in planning]))} jours utilisés\n")

                return planning

        elif status == cp_model.INFEASIBLE:
            print("\n❌ IMPOSSIBLE DE GÉNÉRER UN PLANNING")
            print("\n💡 SOLUTIONS:")
            print("   1. Augmentez le nombre de jours")
            print("   2. Générez par niveau séparé (L1, puis L2, etc.)")
            print("   3. Vérifiez qu'il y a assez de salles disponibles\n")
            return None
        else:
            print(f"\n⚠️ Statut: {self.solver.StatusName(status)}\n")
            return None

    def save_planning_to_db(self, planning):
        """Sauvegarde en base avec vérification finale anti-doublon"""
        conn = get_connection()
        if not conn:
            return False

        try:
            cur = conn.cursor()

            print("\n🔍 Vérification finale avant insertion en BD...\n")

            # Vérifier les doublons AVANT insertion
            for exam in planning:
                cur.execute("""
                SELECT e.id_exam, m.nom, f.nom
                FROM EXAMEN e
                JOIN MODULE m ON e.id_mod = m.id_mod
                JOIN FORMATION f ON m.id_form = f.id_form
                WHERE e.id_lieu = %s 
                AND e.date_exam = %s;
                """, (exam['salle_id'], exam['date_exam']))

                existing = cur.fetchall()

                if existing:
                    print(f"❌ CONFLIT DÉTECTÉ EN BD:")
                    print(f"   Salle: {exam['salle_nom']}")
                    print(f"   Date: {exam['date_exam']}")
                    print(f"   Examen existant: {existing[0][1]} ({existing[0][2]})")
                    print(f"   Nouveau: {exam['module_nom']} ({exam['formation']})")

                    conn.rollback()
                    cur.close()
                    conn.close()
                    return False

            # Si OK, insérer
            print("✅ Aucun conflit - Insertion en cours...\n")

            for exam in planning:
                cur.execute("""
                INSERT INTO EXAMEN (date_exam, duree_min, type_examen, session_examen, id_mod, id_lieu)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id_exam;
                """, (
                    exam['date_exam'],
                    exam['duree_min'],
                    'partiel',
                    'S1',
                    exam['module_id'],
                    exam['salle_id']
                ))

                id_exam = cur.fetchone()[0]

                # Insérer surveillants
                for idx, prof in enumerate(exam['surveillants']):
                    role = 'principal' if idx == 0 else 'assistant'
                    cur.execute("""
                    INSERT INTO SURVEILLANCE (id_exam, id_prof, role)
                    VALUES (%s, %s, %s);
                    """, (id_exam, prof[0], role))

            conn.commit()
            cur.close()
            conn.close()

            print(f"✅ {len(planning)} examens sauvegardés SANS CONFLIT\n")
            return True

        except Exception as e:
            print(f"\n❌ Erreur lors de la sauvegarde: {e}\n")
            if conn:
                conn.rollback()
                conn.close()
            return False