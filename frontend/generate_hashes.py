# generate_hashes.py
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

passwords = {
    'admin123': hash_password('admin123'),
    'prof123': hash_password('prof123'),
    'etu123': hash_password('etu123')
}

print("="*60)
print("HASH CORRECTS POUR LA BASE DE DONNÉES")
print("="*60)

for pwd, hash_val in passwords.items():
    print(f"\n{pwd:12} → {hash_val}")

print("\n" + "="*60)
print("SCRIPT SQL POUR MISE À JOUR")
print("="*60)
print(f"""
-- Mettre à jour les mots de passe avec les hash corrects
UPDATE UTILISATEURS SET password_hash = '{passwords['admin123']}' WHERE username = 'admin';
UPDATE UTILISATEURS SET password_hash = '{passwords['prof123']}' WHERE username IN ('prof1', 'prof2');
UPDATE UTILISATEURS SET password_hash = '{passwords['etu123']}' WHERE username IN ('etu1', 'etu2', 'etu3');

-- Vérification
SELECT username, password_hash, role FROM UTILISATEURS ORDER BY role, username;
""")