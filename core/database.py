import os
import sqlite3
import json

TURSO_URL = os.environ.get("TURSO_DATABASE_URL")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

ALLOWED_UPDATE_FIELDS = {"topic", "duration", "audience", "language", "outline", "script", "metadata", "research", "analysis"}


def get_connection():
    # Coba gunakan Turso jika kredensial tersedia dan library terpasang
    if TURSO_URL and TURSO_TOKEN:
        try:
            import libsql_experimental as libsql
            conn = libsql.connect(database=TURSO_URL, auth_token=TURSO_TOKEN)
            return conn
        except Exception as e:
            print(f"[DB Warning] Gagal koneksi Turso, beralih ke SQLite lokal: {e}")
    
    # Fallback ke SQLite (menggunakan /tmp di Vercel agar bisa ditulis)
    DB_PATH = "/tmp/database.db" if os.environ.get("VERCEL") else "database.db"
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                duration TEXT,
                audience TEXT,
                language TEXT,
                outline TEXT,
                script TEXT,
                metadata TEXT,
                research TEXT,
                analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    except Exception as e:
        print("Database init error:", e)
    finally:
        if conn:
            conn.close()


def create_project(topic, duration, audience, language, outline, script, metadata):
    conn = None
    try:
        init_database()
        conn = get_connection()
        cursor = conn.cursor()
        
        outline_str = json.dumps(outline) if isinstance(outline, (dict, list)) else str(outline)
        metadata_str = json.dumps(metadata) if isinstance(metadata, (dict, list)) else str(metadata)

        cursor.execute("""
            INSERT INTO projects (topic, duration, audience, language, outline, script, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (topic, duration, audience, language, outline_str, script, metadata_str))

        project_id = cursor.lastrowid
        conn.commit()
        return project_id
    except Exception as e:
        print("Error creating project:", e)
        return None
    finally:
        if conn:
            conn.close()


def get_projects():
    conn = None
    try:
        init_database()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY id DESC")
        rows = cursor.fetchall()
        
        projects = []
        for row in rows:
            if hasattr(row, 'keys'):
                projects.append(dict(row))
            else:
                projects.append({
                    "id": row[0], "topic": row[1], "duration": row[2],
                    "audience": row[3], "language": row[4], "outline": row[5],
                    "script": row[6], "metadata": row[7], "research": row[8],
                    "analysis": row[9], "created_at": row[10]
                })
        return projects
    except Exception as e:
        print("Error getting projects:", e)
        return []
    finally:
        if conn:
            conn.close()


def search_projects(query):
    conn = None
    try:
        init_database()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE topic LIKE ? ORDER BY id DESC", (f"%{query}%",))
        rows = cursor.fetchall()
        
        projects = []
        for row in rows:
            if hasattr(row, 'keys'):
                projects.append(dict(row))
            else:
                projects.append({
                    "id": row[0], "topic": row[1], "duration": row[2],
                    "audience": row[3], "language": row[4], "outline": row[5],
                    "script": row[6], "metadata": row[7], "research": row[8],
                    "analysis": row[9], "created_at": row[10]
                })
        return projects
    except Exception as e:
        print("Error searching projects:", e)
        return []
    finally:
        if conn:
            conn.close()


def get_project(project_id):
    conn = None
    try:
        init_database()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        
        if row:
            if hasattr(row, 'keys'):
                project = dict(row)
            else:
                project = {
                    "id": row[0], "topic": row[1], "duration": row[2],
                    "audience": row[3], "language": row[4], "outline": row[5],
                    "script": row[6], "metadata": row[7], "research": row[8],
                    "analysis": row[9], "created_at": row[10]
                }
            
            for field in ["outline", "metadata", "research", "analysis"]:
                if project.get(field):
                    try:
                        project[field] = json.loads(project[field])
                    except Exception:
                        pass
            return project
        return None
    except Exception as e:
        print(f"Error getting project {project_id}:", e)
        return None
    finally:
        if conn:
            conn.close()


def _update_field(project_id, field_name, value):
    if field_name not in ALLOWED_UPDATE_FIELDS:
        print(f"Invalid update field: {field_name}")
        return False

    conn = None
    try:
        init_database()
        conn = get_connection()
        cursor = conn.cursor()
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        cursor.execute(f"UPDATE projects SET {field_name} = ? WHERE id = ?", (value, project_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating {field_name}:", e)
        return False
    finally:
        if conn:
            conn.close()


def update_outline(project_id, outline):
    return _update_field(project_id, "outline", outline)


def update_script(project_id, script):
    return _update_field(project_id, "script", script)


def update_metadata(project_id, metadata):
    return _update_field(project_id, "metadata", metadata)


def update_research(project_id, research):
    return _update_field(project_id, "research", research)


def update_analysis(project_id, analysis):
    return _update_field(project_id, "analysis", analysis)


def rename_project(project_id, new_topic):
    return _update_field(project_id, "topic", new_topic)


def delete_project(project_id):
    conn = None
    try:
        init_database()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting project {project_id}:", e)
        return False
    finally:
        if conn:
            conn.close()