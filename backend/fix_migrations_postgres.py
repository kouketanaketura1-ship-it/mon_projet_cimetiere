"""
Script à exécuter UNE FOIS depuis le dossier backend :
    python fix_migrations_postgres.py

Se connecte à la VRAIE base utilisée par Django (PostgreSQL, définie dans .env)
et vérifie/supprime les tables orphelines avant la migration.
Ne touche à AUCUNE donnée de Utilisateur, Caveau, Reservation, MFACode.
"""
import os

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 n'est pas installé. Lancez : pip install psycopg2-binary")
    raise SystemExit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_NAME = os.getenv("DB_NAME", "cimetiere_gi2")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
if DB_HOST == "localhost":
    DB_HOST = "monprojetcimetiere-production.up.railway.app"  # évite la résolution IPv6 (::1) qui exige un mot de passe
DB_PORT = os.getenv("DB_PORT", "5432")

print(f"🔌 Connexion à PostgreSQL : base='{DB_NAME}' hôte='{DB_HOST}:{DB_PORT}' user='{DB_USER}'")

try:
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
except Exception as e:
    print(f"❌ Impossible de se connecter : {e}")
    print("Vérifiez que PostgreSQL tourne bien en local et que le mot de passe dans .env est correct.")
    raise SystemExit(1)

conn.autocommit = False
cur = conn.cursor()

cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' ORDER BY table_name
""")
tables_existantes = {row[0] for row in cur.fetchall()}

print("\n📋 Tables présentes dans la base PostgreSQL :")
for t in sorted(tables_existantes):
    print(f"   - {t}")

print()
try:
    cur.execute("SELECT name FROM django_migrations WHERE app='cimetiere' ORDER BY id")
    migrations_appliquees = [row[0] for row in cur.fetchall()]
    print("📋 Migrations 'cimetiere' déjà enregistrées comme appliquées :")
    for m in migrations_appliquees:
        print(f"   - {m}")
except Exception as e:
    print(f"⚠️  Impossible de lire django_migrations : {e}")

print()

TABLES_A_VERIFIER = [
    "cimetiere_auditlog",
    "cimetiere_concession",
    "cimetiere_transaction",
    "cimetiere_exhumation",
    "cimetiere_configurationterrain",
]
a_supprimer = [t for t in TABLES_A_VERIFIER if t in tables_existantes]

if not a_supprimer:
    print("✅ Aucune table orpheline détectée dans PostgreSQL. Vous pouvez lancer directement :")
    print("   python manage.py migrate")
else:
    print(f"⚠️  Tables orphelines détectées : {a_supprimer}")
    reponse = input("Voulez-vous les supprimer maintenant ? (o/n) : ").strip().lower()
    if reponse == "o":
        for t in a_supprimer:
            cur.execute(f'DROP TABLE IF EXISTS "{t}" CASCADE')
            print(f"🗑️  Table {t} supprimée")
        conn.commit()
        print("\n✅ Nettoyage terminé. Vous pouvez maintenant lancer :")
        print("   python manage.py migrate")
    else:
        conn.rollback()
        print("Annulé, aucune table supprimée.")

cur.close()
conn.close()
