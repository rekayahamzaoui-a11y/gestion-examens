# frontend/users_db.py
import psycopg2
import hashlib
from db_utils import get_connection  # ← CORRECTION : db au lieu de db_utils


def hash_password(password):
    """Hash le mot de passe avec SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def init_users_table():
    """Crée la table des utilisateurs si elle n'existe pas"""
    conn = get_connection()
    if not conn:
        print("❌ Impossible de se connecter à PostgreSQL")
        return False

    try:
        cur = conn.cursor()

        # Vérifier si la table existe
        cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'utilisateurs'
        );
        """)
        table_exists = cur.fetchone()[0]

        if not table_exists:
            print("🔨 Création de la table UTILISATEURS...")
            cur.execute("""
            CREATE TABLE UTILISATEURS (
                id_user SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'professeur', 'etudiant')),
                email VARCHAR(100),
                nom VARCHAR(50),
                prenom VARCHAR(50),
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                dernier_login TIMESTAMP
            );
            """)
            print("✅ Table UTILISATEURS créée")

        # Vérifier le nombre d'utilisateurs
        cur.execute("SELECT COUNT(*) FROM UTILISATEURS;")
        count = cur.fetchone()[0]

        if count == 0:
            print("📝 Insertion des utilisateurs par défaut...")

            # Hash des mots de passe
            admin_hash = hash_password("admin123")
            prof_hash = hash_password("prof123")
            etu_hash = hash_password("etu123")

            print(f"🔐 Hash admin123: {admin_hash}")
            print(f"🔐 Hash prof123: {prof_hash}")
            print(f"🔐 Hash etu123: {etu_hash}")

            # Insérer les utilisateurs
            cur.execute("""
            INSERT INTO UTILISATEURS (username, password_hash, role, nom, prenom, email)
            VALUES 
            ('admin', %s, 'admin', 'Administrateur', 'Système', 'admin@univ.dz'),
            ('prof1', %s, 'professeur', 'Benali', 'Ahmed', 'a.benali@univ.dz'),
            ('prof2', %s, 'professeur', 'Kaci', 'Fatima', 'f.kaci@univ.dz'),
            ('etu1', %s, 'etudiant', 'Amrani', 'Yacine', 'y.amrani@etu.dz'),
            ('etu2', %s, 'etudiant', 'Belkacem', 'Rania', 'r.belkacem@etu.dz'),
            ('etu3', %s, 'etudiant', 'Boudiaf', 'Yazid', 'y.boudiaf@etu.dz')
            ON CONFLICT (username) DO NOTHING;
            """, (admin_hash, prof_hash, prof_hash, etu_hash, etu_hash, etu_hash))

            print("✅ 6 utilisateurs créés :")
            print("   👑 admin / admin123")
            print("   👨‍🏫 prof1 / prof123")
            print("   👨‍🏫 prof2 / prof123")
            print("   👨‍🎓 etu1 / etu123 (Yacine Amrani)")
            print("   👨‍🎓 etu2 / etu123 (Rania Belkacem)")
            print("   👨‍🎓 etu3 / etu123 (Yazid Boudiaf)")
        else:
            print(f"✅ {count} utilisateurs déjà présents")

        conn.commit()
        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Erreur : {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def verify_user(username, password):
    """Vérifie les identifiants utilisateur"""
    conn = get_connection()
    if not conn:
        print("❌ Pas de connexion")
        return None

    try:
        cur = conn.cursor()
        password_hash = hash_password(password)

        print(f"🔍 Tentative connexion: {username}")
        print(f"🔐 Hash généré: {password_hash}")

        cur.execute("""
        SELECT id_user, username, role, nom, prenom, email
        FROM UTILISATEURS
        WHERE username = %s AND password_hash = %s;
        """, (username, password_hash))

        user = cur.fetchone()

        if user:
            # Mettre à jour le dernier login
            cur.execute("""
            UPDATE UTILISATEURS 
            SET dernier_login = CURRENT_TIMESTAMP 
            WHERE id_user = %s;
            """, (user[0],))
            conn.commit()

            print(f"✅ Connexion réussie : {user[1]} ({user[2]})")

            cur.close()
            conn.close()

            return {
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'nom': user[3],
                'prenom': user[4],
                'email': user[5]
            }
        else:
            print(f"❌ Aucun utilisateur trouvé pour {username}")

        cur.close()
        conn.close()
        return None

    except Exception as e:
        print(f"❌ Erreur vérification : {e}")
        if conn:
            conn.close()
        return None


def create_user(username, password, role, nom, prenom, email):
    """Crée un nouvel utilisateur"""
    conn = get_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        password_hash = hash_password(password)

        cur.execute("""
        INSERT INTO UTILISATEURS (username, password_hash, role, nom, prenom, email)
        VALUES (%s, %s, %s, %s, %s, %s);
        """, (username, password_hash, role, nom, prenom, email))

        conn.commit()
        print(f"✅ Utilisateur créé : {username} ({role})")

        cur.close()
        conn.close()
        return True

    except psycopg2.IntegrityError:
        print(f"❌ Utilisateur {username} existe déjà")
        if conn:
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"❌ Erreur création : {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def get_all_users():
    """Récupère tous les utilisateurs (pour l'admin)"""
    conn = get_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT id_user, username, role, nom, prenom, email, 
               date_creation, dernier_login
        FROM UTILISATEURS
        ORDER BY role, nom;
        """)

        users = cur.fetchall()
        cur.close()
        conn.close()

        return [{
            'id': u[0],
            'username': u[1],
            'role': u[2],
            'nom': u[3],
            'prenom': u[4],
            'email': u[5],
            'date_creation': u[6],
            'dernier_login': u[7]
        } for u in users]

    except Exception as e:
        print(f"❌ Erreur récupération utilisateurs : {e}")
        if conn:
            conn.close()
        return []


def delete_user(user_id):
    """Supprime un utilisateur"""
    conn = get_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM UTILISATEURS WHERE id_user = %s;", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Erreur suppression : {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


# Test du module
if __name__ == "__main__":
    print("=" * 50)
    print("🔐 TEST MODULE AUTHENTIFICATION")
    print("=" * 50)

    if init_users_table():
        print("\n✅ Initialisation OK\n")

        # Afficher tous les utilisateurs
        users = get_all_users()
        print("📋 Liste des utilisateurs :")
        for u in users:
            print(f"   - {u['username']:12} ({u['role']:12}) : {u['nom']} {u['prenom']}")

        # Test connexion
        print("\n🧪 Test connexion admin...")
        user = verify_user("admin", "admin123")
        if user:
            print(f"   ✅ {user['prenom']} {user['nom']}")

        print("\n🧪 Test connexion etu1...")
        user = verify_user("etu1", "etu123")
        if user:
            print(f"   ✅ {user['prenom']} {user['nom']}")