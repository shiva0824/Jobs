# kb_loader.py
import json
import psycopg2
from pathlib import Path
from src.core.config import settings

# -------------------------------
# DB connection settings (local)
# -------------------------------
DB_NAME = settings.DB_NAME
DB_USER = settings.DB_USER
DB_PASSWORD = settings.DB_PASSWORD
DB_HOST = settings.DB_HOST
DB_PORT = settings.DB_PORT

# -------------------------------
# Paths
# -------------------------------
KB_PATH = Path(__file__).resolve().parents[1] / "data" / "job_skill_kb.json"

# -------------------------------
# Insert functions
# -------------------------------
def insert_role(cur, title, level):
    cur.execute(
        "INSERT INTO roles (title, level) VALUES (%s, %s) RETURNING id;",
        (title, level),
    )
    return cur.fetchone()[0]

def get_or_create_skill(cur, name, skill_type):
    # normalize to lowercase for uniqueness
    cur.execute("SELECT id FROM skills WHERE name = %s;", (name.lower(),))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO skills (name, type) VALUES (%s, %s) RETURNING id;",
        (name.lower(), skill_type),
    )
    return cur.fetchone()[0]

def link_role_skill(cur, role_id, skill_id):
    cur.execute(
        "INSERT INTO role_skills (role_id, skill_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
        (role_id, skill_id),
    )

# -------------------------------
# Main loader
# -------------------------------
def load_kb():
    with open(KB_PATH, "r", encoding="utf-8") as f:
        roles_data = json.load(f)

    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    cur = conn.cursor()

    for role in roles_data:
        title = role["title"]
        level = role["level"]
        role_id = insert_role(cur, title, level)

        for skill in role.get("technical", []):
            skill_id = get_or_create_skill(cur, skill, "technical")
            link_role_skill(cur, role_id, skill_id)

        for skill in role.get("soft", []):
            skill_id = get_or_create_skill(cur, skill, "soft")
            link_role_skill(cur, role_id, skill_id)

    conn.commit()
    cur.close()
    conn.close()
    print("Knowledge base loaded into Postgres.")

if __name__ == "__main__":
    load_kb()