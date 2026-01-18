# frontend/test_login.py
import sys
sys.path.append('.')

from users_db import verify_user, hash_password

print("=" * 60)
print("TEST DE CONNEXION")
print("=" * 60)

# Test des hash
print("\n1️⃣ Test des hash générés:")
print(f"Hash admin123: {hash_password('admin123')}")
print(f"Hash prof123:  {hash_password('prof123')}")
print(f"Hash etu123:   {hash_password('etu123')}")

# Test connexion admin
print("\n2️⃣ Test connexion ADMIN:")
user = verify_user('admin', 'admin123')
if user:
    print(f"✅ SUCCÈS: {user['username']} ({user['role']})")
else:
    print("❌ ÉCHEC")

# Test connexion prof1
print("\n3️⃣ Test connexion PROF1:")
user = verify_user('prof1', 'prof123')
if user:
    print(f"✅ SUCCÈS: {user['username']} ({user['role']})")
else:
    print("❌ ÉCHEC")

# Test connexion etu1
print("\n4️⃣ Test connexion ETU1:")
user = verify_user('etu1', 'etu123')
if user:
    print(f"✅ SUCCÈS: {user['username']} ({user['role']})")
else:
    print("❌ ÉCHEC")

print("\n" + "=" * 60)