import json
import os
import sqlite3


# ============================================================
# KONFIGURASI
# ============================================================

# Urutan kolom tabel projects. SELECT selalu memakai nama kolom eksplisit
# supaya hasil tuple dari libsql/Turso selalu cocok dengan urutan ini,
# walaupun urutan kolom di database lama berbeda.
COLUMNS = [
    "id", "topic", "duration", "audience", "language",
    "outline", "script", "metadata", "research", "analysis",
    "created_at"
]

# Kolom ringan untuk halaman daftar project (tanpa outline/script yang besar)
LIST_COLUMNS = ["id", "topic", "duration", "audience", "language", "created_at"]

JSON_FIELDS = ("outline", "metadata", "research", "analysis")

UPDATABLE_FIELDS = (
    "topic", "outline", "script", "metadata", "research", "analysis"
)

_db_ready = False


# ============================================================
# KONEKSI
# ============================================================

def get_connection():
    turso_url = os.environ.get("TURSO_DATABASE_URL")
    turso_token = os.environ.get("TURSO_AUTH_TOKEN")

    if turso_url and turso_token:
        # Menggunakan Turso Cloud Database
        import libsql_experimental as libsql

        return libsql.connect(database=turso_url, auth_token=turso_token)

    # Menggunakan SQLite lokal saat pengembangan lokal.
    # Di Vercel folder /tmp bersifat sementara: data hilang saat instance
    # berganti, jadi di production wajib memakai Turso.
    db_path = "/tmp/database.db" if os.environ.get("VERCEL") else "database.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _close(conn):
    if conn is None:
        return

    try:
        conn.close()
    except Exception:
        pass


def _row_to_dict(row, columns):
    if row is None:
        return None

    if hasattr(row, "keys"):
        return dict(row)

    # Hasil tuple dari libsql
    return dict(zip(columns, row))


def _to_text(value):
    if value is None:
        return None

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


# ============================================================
# INIT DATABASE (dijalankan sekali per proses, bukan tiap request)
# ============================================================

def init_database():
    global _db_ready

    if _db_ready:
        return

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

        # Migrasi otomatis: tambahkan kolom yang belum ada di database lama
        try:
            cursor.execute("PRAGMA table_info(projects)")
            existing = {row[1] for row in cursor.fetchall()}

            for column in COLUMNS:
                if column in existing or column == "id":
                    continue

                column_type = "TIMESTAMP" if column == "created_at" else "TEXT"
                cursor.execute(
                    f"ALTER TABLE projects ADD COLUMN {column} {column_type}"
                )
                print(f"Database migration: kolom '{column}' ditambahkan.")
        except Exception as e:
            print("Database migration check skipped:", e)

        conn.commit()
        _db_ready = True

    except Exception as e:
        print("Database init error:", e)

    finally:
        _close(conn)


# ============================================================
# PROJECT OPERATIONS
# ============================================================

def create_project(topic, duration, audience, language, outline, script, metadata):
    conn = None

    try:
        init_database()
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO projects (topic, duration, audience, language, outline, script, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            topic,
            duration,
            audience,
            language,
            _to_text(outline),
            script,
            _to_text(metadata)
        ))

        conn.commit()

        project_id = getattr(cursor, "lastrowid", None)

        if not project_id:
            try:
                cursor.execute("SELECT last_insert_rowid()")
                row = cursor.fetchone()
                project_id = row[0] if row else None
            except Exception:
                project_id = None

        if not project_id:
            cursor.execute("SELECT MAX(id) FROM projects")
            row = cursor.fetchone()
            project_id = row[0] if row else None

        return project_id

    except Exception as e:
        print("Error creating project:", e)
        return None

    finally:
        _close(conn)


def get_projects():
    conn = None

    try:
        init_database()
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT {', '.join(LIST_COLUMNS)} FROM projects ORDER BY id DESC"
        )
        rows = cursor.fetchall()

        return [_row_to_dict(row, LIST_COLUMNS) for row in rows]

    except Exception as e:
        print("Error getting projects:", e)
        return []

    finally:
        _close(conn)


def search_projects(query):
    conn = None

    try:
        init_database()
        conn = get_connection()
        cursor = conn.cursor()

        # Escape karakter wildcard supaya pencarian "50%" atau "a_b" tidak aneh
        safe_query = (
            str(query)
            .replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )

        cursor.execute(
            f"SELECT {', '.join(LIST_COLUMNS)} FROM projects "
            "WHERE topic LIKE ? ESCAPE '\\' ORDER BY id DESC",
            (f"%{safe_query}%",)
        )
        rows = cursor.fetchall()

        return [_row_to_dict(row, LIST_COLUMNS) for row in rows]

    except Exception as e:
        print("Error searching projects:", e)
        return []

    finally:
        _close(conn)


def get_project(project_id):
    conn = None

    try:
        init_database()
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT {', '.join(COLUMNS)} FROM projects WHERE id = ?",
            (project_id,)
        )
        row = cursor.fetchone()

        if not row:
            return None

        project = _row_to_dict(row, COLUMNS)

        for field in JSON_FIELDS:
            if project.get(field):
                try:
                    project[field] = json.loads(project[field])
                except Exception:
                    pass

        # Script kosong selalu berupa string, bukan None
        project["script"] = project.get("script") or ""

        return project

    except Exception as e:
        print(f"Error getting project {project_id}:", e)
        return None

    finally:
        _close(conn)


# ============================================================
# UPDATE OPERATIONS
# ============================================================

def _update_field(project_id, field_name, value):
    # Nama kolom tidak boleh berasal dari input bebas
    if field_name not in UPDATABLE_FIELDS:
        print(f"Error updating: kolom '{field_name}' tidak diizinkan.")
        return False

    conn = None

    try:
        init_database()
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            f"UPDATE projects SET {field_name} = ? WHERE id = ?",
            (_to_text(value), project_id)
        )
        conn.commit()
        return True

    except Exception as e:
        print(f"Error updating {field_name}:", e)
        return False

    finally:
        _close(conn)


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
        _close(conn)