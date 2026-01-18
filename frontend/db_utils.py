# frontend/db.py
import psycopg2
from psycopg2 import Error

def get_connection():
    """Connexion à PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="gestion_examens_db",
            user="postgres",
            password="rekaya22",
            port="5432"
        )
        return conn
    except Error as e:
        print(f"❌ Erreur de connexion PostgreSQL: {e}")
        return None

def test_connection():
    """Test de connexion"""
    conn = get_connection()
    if conn:
        print("✅ Connexion PostgreSQL réussie")
        conn.close()
        return True
    return False
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT username, password_hash FROM utilisateurs;")
for row in cur.fetchall():
    print(row)
cur.close()
conn.close()

