import sqlite3
import json
from datetime import datetime


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_NAME = "cosmic_ai.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    connection = sqlite3.connect(
        DATABASE_NAME
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# HELPERS
# ============================================================

def table_columns(
    connection,
    table_name
):
    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return {
        row["name"]
        for row in rows
    }


def add_column_if_missing(
    connection,
    table_name,
    column_name,
    column_definition
):
    columns = table_columns(
        connection,
        table_name
    )

    if column_name not in columns:

        connection.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name}
            {column_definition}
            """
        )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_database():

    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            topic TEXT NOT NULL,

            duration TEXT NOT NULL,

            audience TEXT NOT NULL,

            language TEXT NOT NULL,

            outline TEXT,

            script TEXT,

            metadata TEXT,

            created_at TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------------------
    # FUTURE PIPELINE DATA
    # --------------------------------------------------------

    # Research
    add_column_if_missing(
        connection,
        "projects",
        "research",
        "TEXT"
    )

    # Script analysis
    add_column_if_missing(
        connection,
        "projects",
        "analysis",
        "TEXT"
    )

    # Scene planner
    add_column_if_missing(
        connection,
        "projects",
        "scene_plan",
        "TEXT"
    )

    # Voice generation information
    add_column_if_missing(
        connection,
        "projects",
        "voice",
        "TEXT"
    )

    # Subtitle information
    add_column_if_missing(
        connection,
        "projects",
        "subtitles",
        "TEXT"
    )

    # Video information
    add_column_if_missing(
        connection,
        "projects",
        "video",
        "TEXT"
    )

    # Export information
    add_column_if_missing(
        connection,
        "projects",
        "export_data",
        "TEXT"
    )

    connection.commit()

    connection.close()


# ============================================================
# CREATE PROJECT
# ============================================================

def create_project(
    topic,
    duration,
    audience,
    language,
    outline,
    script,
    metadata
):

    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO projects (
            topic,
            duration,
            audience,
            language,
            outline,
            script,
            metadata,
            created_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            topic,
            duration,
            audience,
            language,
            json.dumps(
                outline,
                ensure_ascii=False
            ),
            script,
            json.dumps(
                metadata,
                ensure_ascii=False
            ),
            datetime.now().isoformat()
        )
    )

    project_id = cursor.lastrowid

    connection.commit()

    connection.close()

    return project_id


# ============================================================
# GET PROJECTS
# ============================================================

def get_projects():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM projects
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# SEARCH PROJECTS
# ============================================================

def search_projects(
    search_query
):

    connection = get_connection()

    pattern = f"%{search_query}%"

    rows = connection.execute(
        """
        SELECT *
        FROM projects

        WHERE
            topic LIKE ?
            OR audience LIKE ?
            OR language LIKE ?

        ORDER BY id DESC
        """,
        (
            pattern,
            pattern,
            pattern
        )
    ).fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# GET PROJECT
# ============================================================

def get_project(
    project_id
):

    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM projects
        WHERE id = ?
        """,
        (
            project_id,
        )
    ).fetchone()

    connection.close()

    if row is None:
        return None

    project = dict(row)

    # --------------------------------------------------------
    # JSON FIELDS
    # --------------------------------------------------------

    json_fields = [
        "outline",
        "metadata",
        "research",
        "analysis",
        "scene_plan",
        "voice",
        "subtitles",
        "video",
        "export_data"
    ]

    for field in json_fields:

        value = project.get(
            field
        )

        if value:

            try:

                project[field] = json.loads(
                    value
                )

            except (
                json.JSONDecodeError,
                TypeError
            ):

                project[field] = None

        else:

            project[field] = None

    return project


# ============================================================
# UPDATE OUTLINE
# ============================================================

def update_outline(
    project_id,
    outline
):

    connection = get_connection()

    connection.execute(
        """
        UPDATE projects
        SET outline = ?
        WHERE id = ?
        """,
        (
            json.dumps(
                outline,
                ensure_ascii=False
            ),
            project_id
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# UPDATE SCRIPT
# ============================================================

def update_script(
    project_id,
    script
):

    connection = get_connection()

    connection.execute(
        """
        UPDATE projects
        SET script = ?
        WHERE id = ?
        """,
        (
            script,
            project_id
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# UPDATE METADATA
# ============================================================

def update_metadata(
    project_id,
    metadata
):

    connection = get_connection()

    connection.execute(
        """
        UPDATE projects
        SET metadata = ?
        WHERE id = ?
        """,
        (
            json.dumps(
                metadata,
                ensure_ascii=False
            ),
            project_id
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# UPDATE RESEARCH
# ============================================================

def update_research(
    project_id,
    research
):

    connection = get_connection()

    connection.execute(
        """
        UPDATE projects
        SET research = ?
        WHERE id = ?
        """,
        (
            json.dumps(
                research,
                ensure_ascii=False
            ),
            project_id
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# UPDATE ANALYSIS
# ============================================================

def update_analysis(
    project_id,
    analysis
):

    connection = get_connection()

    connection.execute(
        """
        UPDATE projects
        SET analysis = ?
        WHERE id = ?
        """,
        (
            json.dumps(
                analysis,
                ensure_ascii=False
            ),
            project_id
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# UPDATE SCENE PLAN
# ============================================================

def update_scene_plan(
    project_id,
    scene_plan
):

    connection = get_connection()

    connection.execute(
        """
        UPDATE projects
        SET scene_plan = ?
        WHERE id = ?
        """,
        (
            json.dumps(
                scene_plan,
                ensure_ascii=False
            ),
            project_id
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# UPDATE VOICE
# ============================================================

def update_voice(
    project_id,
    voice
):

    connection = get_connection()

    connection.execute(
        """
        UPDATE projects
        SET voice = ?
        WHERE id = ?
        """,
        (
            json.dumps(
                voice,
                ensure_ascii=False
            ),
            project_id
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# UPDATE SUBTITLES
# ============================================================

def update_subtitles(
    project_id,
    subtitles
):

    connection = get_connection()

    connection.execute(
        """
        UPDATE projects
        SET subtitles = ?
        WHERE id = ?
        """,
        (
            json.dumps(
                subtitles,
                ensure_ascii=False
            ),
            project_id
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# UPDATE VIDEO
# ============================================================

def update_video(
    project_id,
    video
):

    connection = get_connection()

    connection.execute(
        """
        UPDATE projects
        SET video = ?
        WHERE id = ?
        """,
        (
            json.dumps(
                video,
                ensure_ascii=False
            ),
            project_id
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# UPDATE EXPORT DATA
# ============================================================

def update_export_data(
    project_id,
    export_data
):

    connection = get_connection()

    connection.execute(
        """
        UPDATE projects
        SET export_data = ?
        WHERE id = ?
        """,
        (
            json.dumps(
                export_data,
                ensure_ascii=False
            ),
            project_id
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# RENAME PROJECT
# ============================================================

def rename_project(
    project_id,
    new_topic
):

    connection = get_connection()

    connection.execute(
        """
        UPDATE projects
        SET topic = ?
        WHERE id = ?
        """,
        (
            new_topic,
            project_id
        )
    )

    connection.commit()

    connection.close()


# ============================================================
# DELETE PROJECT
# ============================================================

def delete_project(
    project_id
):

    connection = get_connection()

    connection.execute(
        """
        DELETE FROM projects
        WHERE id = ?
        """,
        (
            project_id,
        )
    )

    connection.commit()

    connection.close()