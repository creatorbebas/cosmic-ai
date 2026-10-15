import hashlib
import hmac
import os
import re
from datetime import timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv tidak wajib di production
    pass

from core.content import (
    generate_outline,
    regenerate_outline,
    generate_script,
    regenerate_script,
    generate_metadata,
    normalize_outline,
    is_dracin_mode
)

from core.database import (
    init_database,
    create_project,
    get_projects,
    search_projects,
    get_project,
    update_outline,
    update_script,
    update_metadata,
    update_research,
    update_analysis,
    rename_project,
    delete_project
)

from core.script_editor import (
    split_script,
    combine_sections,
    normalize_section_name
)

from core.script_rewriter import (
    rewrite_section
)

from core.script_analyzer import (
    analyze_script
)

from core.research import (
    research_project
)

from core.research_outline import (
    generate_outline_from_research
)

from core.outline_script import (
    generate_script_from_outline,
    script_to_text
)


# ============================================================
# APP CONFIGURATION
# ============================================================
# Environment variable yang dipakai:
# - ACCESS_KEYS      : kunci akses studio, pisahkan dengan koma
#                      contoh: kunci_a,kunci_b,kunci_c
# - FLASK_SECRET_KEY : kunci penanda sesi login (isi teks acak yang panjang)
# - AI_API_KEY       : API key OpenAI (dipakai di core/ai.py)
# - TURSO_DATABASE_URL, TURSO_AUTH_TOKEN : database Turso

def _load_access_keys():
    """
    Membaca ACCESS_KEYS. Dipisah koma, titik koma, atau baris baru.
    Spasi dan tanda kutip di sekitar tiap kunci diabaikan, jadi nilai seperti
    "studio_rahasia_2026" atau  studio_rahasia_2026  tetap terbaca benar.
    """
    # Nama variabel yang diterima: ACCESS_KEYS (disarankan) atau ACCESS_KEY
    raw = "\n".join(
        os.environ.get(name, "") for name in ("ACCESS_KEYS", "ACCESS_KEY")
    )
    keys = []

    for part in re.split(r"[,;\n]", raw):
        key = part.strip().strip("\"'").strip()

        if key:
            keys.append(key)

    return keys


# Kunci lama yang sudah dibagikan ke pengguna. Tetap berlaku seperti sebelumnya,
# jadi link lama (?key=...) tidak perlu diganti dan Vercel tidak perlu diubah.
# Catatan: kunci di sini tersimpan di kode/GitHub. Untuk menggantinya nanti,
# kosongkan daftar ini ([]) lalu isi ACCESS_KEYS di Vercel dengan kunci baru.
LEGACY_ACCESS_KEYS = [
    "studio_rahasia_2026",
    "dullahstudio777",
    "dullahstudio_rahasia_2026",
]

ENV_ACCESS_KEYS = _load_access_keys()

ACCESS_KEYS = list(dict.fromkeys(LEGACY_ACCESS_KEYS + ENV_ACCESS_KEYS))

if not ACCESS_KEYS:
    print("PERINGATAN: tidak ada kunci akses, studio tidak bisa dibuka.")


def _build_secret_key():
    secret = os.environ.get("FLASK_SECRET_KEY")

    if secret:
        return secret

    print("PERINGATAN: FLASK_SECRET_KEY belum diatur.")

    if ACCESS_KEYS:
        # Turunan dari kunci akses supaya sesi tetap stabil antar instance Vercel
        seed = "cosmic-ai|" + "|".join(sorted(ACCESS_KEYS))
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()

    return os.urandom(32).hex()


app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static"
)

app.secret_key = _build_secret_key()
app.permanent_session_lifetime = timedelta(days=30)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = bool(os.environ.get("VERCEL"))


# ============================================================
# DATABASE
# ============================================================

try:
    init_database()
except Exception as e:
    print("Database init handled:", e)


# ============================================================
# AKSES / LOGIN
# ============================================================

def _is_valid_key(candidate):
    candidate = (candidate or "").strip()

    if not candidate:
        return False

    candidate_bytes = candidate.encode("utf-8")

    return any(
        hmac.compare_digest(candidate_bytes, key.encode("utf-8"))
        for key in ACCESS_KEYS
    )


def require_access(view):
    """Semua halaman dan aksi studio hanya bisa dipakai setelah akses dibuka."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("unlocked"):
            if request.method == "GET":
                return redirect(url_for("home"))

            return "Akses ditolak. Buka halaman utama dengan kunci akses terlebih dahulu.", 403

        return view(*args, **kwargs)

    return wrapped


# ============================================================
# HELPER
# ============================================================

def _clean_text(value):
    """Browser mengirim baris baru textarea sebagai CRLF; simpan sebagai LF."""
    return (value or "").replace("\r\n", "\n").strip()


def _detect_mode():
    """
    Menentukan mode generator: 'dracin', 'general', atau None.

    Form baru mengirim field 'mode'. Jika form lama masih ada di cache browser
    (kedua tab terkirim sekaligus), mode ditebak dari kolom topik yang terisi.
    """
    mode = request.form.get("mode", "").strip().lower()

    if mode in ("dracin", "general"):
        return mode

    topics = request.form.getlist("topic")

    if len(topics) >= 2:
        if topics[-1].strip() and not topics[0].strip():
            return "general"
        return "dracin"

    return None


def _pick(name, mode):
    values = [value.strip() for value in request.form.getlist(name)]

    if not values:
        return ""

    if len(values) == 1:
        return values[0]

    if mode == "dracin":
        return values[0]

    if mode == "general":
        return values[-1]

    for value in reversed(values):
        if value:
            return value

    return ""


def _ai_failed(message):
    return f"{message} Coba lagi beberapa saat. Jika terus gagal, periksa API key dan log server.", 500


# ============================================================
# HOME & ACCESS CONTROL
# ============================================================

@app.route("/")
def home():
    key_ok = _is_valid_key(request.args.get("key"))

    if key_ok:
        session["unlocked"] = True
        session.permanent = True

    is_unlocked = bool(session.get("unlocked")) or key_ok

    return render_template("index.html", is_unlocked=is_unlocked)


@app.route("/logout-access")
def logout_access():
    session.pop("unlocked", None)
    return redirect(url_for("home"))


# ============================================================
# CEK AKSES (SEMENTARA, hapus setelah akses normal)
# ============================================================
# Hanya menampilkan jumlah kunci yang terbaca dan apakah kunci di URL cocok.
# Isi kunci tidak pernah ditampilkan. Contoh: /cek-akses?key=kunci_kamu

@app.route("/cek-akses")
def cek_akses():
    lines = [
        f"Kunci dari Vercel (ACCESS_KEYS / ACCESS_KEY): {len(ENV_ACCESS_KEYS)}",
        f"Kunci bawaan lama di kode: {len(LEGACY_ACCESS_KEYS)}",
        "FLASK_SECRET_KEY: " + ("terisi" if os.environ.get("FLASK_SECRET_KEY") else "KOSONG"),
        "API key AI: " + ("terisi" if (os.environ.get("AI_API_KEY") or os.environ.get("OPENAI_API_KEY")) else "KOSONG"),
        "Turso: " + ("terisi" if (os.environ.get("TURSO_DATABASE_URL") and os.environ.get("TURSO_AUTH_TOKEN")) else "KOSONG (data hanya sementara)"),
        "Kunci di URL cocok: " + ("YA" if _is_valid_key(request.args.get("key")) else "TIDAK"),
    ]

    return "\n".join(lines), 200, {"Content-Type": "text/plain; charset=utf-8"}


# ============================================================
# SETTINGS PAGE
# ============================================================

@app.route("/settings")
@require_access
def settings_page():
    return render_template("settings.html")


# ============================================================
# PROJECTS
# ============================================================

@app.route("/projects")
@require_access
def projects():
    search_query = (
        request.args.get("search") or request.args.get("q") or ""
    ).strip()

    if search_query:
        project_list = search_projects(search_query)
    else:
        project_list = get_projects()

    return render_template(
        "projects.html",
        projects=project_list,
        search_query=search_query
    )


# ============================================================
# PROJECT DETAIL
# ============================================================

@app.route("/projects/<int:project_id>")
@require_access
def project_detail(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    if "outline" in project and project["outline"]:
        project["outline"] = normalize_outline(project["outline"])

    return render_template(
        "project.html",
        project=project
    )


# ============================================================
# RESEARCH PAGE
# ============================================================

@app.route("/projects/<int:project_id>/research")
@require_access
def research_page(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    return render_template(
        "research.html",
        project=project,
        research=project.get("research"),
        error=None
    )


# ============================================================
# RUN RESEARCH
# ============================================================

@app.route("/projects/<int:project_id>/research/run", methods=["POST"])
@require_access
def research_run(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    mode = request.form.get("research_mode", "knowledge").strip().lower()
    web_search = (mode == "web")

    research = research_project(project, web_search=web_search)

    if research is None:
        return render_template(
            "research.html",
            project=project,
            research=project.get("research"),
            error="Research gagal dibuat. Periksa API key atau koneksi."
        )

    update_research(project_id, research)

    return redirect(f"/projects/{project_id}/research")


# ============================================================
# GENERATE OUTLINE FROM RESEARCH
# ============================================================

@app.route("/projects/<int:project_id>/research/generate-outline", methods=["POST"])
@require_access
def generate_outline_from_research_route(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    research = project.get("research")

    if not research:
        return "Research belum tersedia.", 400

    outline = generate_outline_from_research(
        project=project,
        research=research
    )

    if outline is None:
        return _ai_failed("Gagal membuat outline dari research.")

    outline = normalize_outline(outline)

    update_outline(project_id, outline)

    return redirect(f"/projects/{project_id}")


# ============================================================
# GENERATE SCRIPT FROM OUTLINE
# ============================================================

@app.route("/projects/<int:project_id>/research/generate-script", methods=["POST"])
@require_access
def generate_script_from_outline_route(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    outline = project.get("outline")

    if not outline:
        return "Outline belum tersedia.", 400

    script_data = generate_script_from_outline(
        project=project,
        outline=outline
    )

    if script_data is None:
        return _ai_failed("Gagal membuat script dari outline.")

    script = script_to_text(script_data)

    if not script:
        return "Script hasil generate kosong.", 500

    update_script(project_id, script)

    return redirect(f"/projects/{project_id}/editor")


# ============================================================
# SCRIPT EDITOR (LENGKAP DENGAN ANALYZE & REWRITE)
# ============================================================

@app.route("/projects/<int:project_id>/editor")
@require_access
def script_editor(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    sections = split_script(project.get("script") or "")

    return render_template(
        "editor.html",
        project=project,
        sections=sections,
        rewrite_preview=None,
        rewrite_section_name=None,
        rewrite_style=None,
        analysis=None,
        analysis_error=None
    )


# ============================================================
# SAVE SCRIPT EDITOR
# ============================================================
# Tiap section punya form sendiri, jadi yang terkirim hanya satu section.
# Section itu dimasukkan ke script yang sudah tersimpan; section lain tidak berubah.

@app.route("/projects/<int:project_id>/editor/save", methods=["POST"])
@require_access
def save_script_editor(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    names = request.form.getlist("section_name")
    contents = request.form.getlist("section_content")

    updates = {}

    for name, content in zip(names, contents):
        key = normalize_section_name(name)

        if key:
            updates[key] = _clean_text(content)

    if not updates:
        return "Tidak ada section yang dikirim.", 400

    sections = split_script(project.get("script") or "")
    updated = set()

    for section in sections:
        key = normalize_section_name(section.get("name", ""))

        if key in updates and key not in updated:
            section["content"] = updates[key]
            updated.add(key)

    if not updated:
        return "Section tidak ditemukan.", 404

    new_script = combine_sections(sections)

    update_script(project_id, new_script)

    return redirect(f"/projects/{project_id}/editor")


# ============================================================
# REWRITE SCRIPT SECTION
# ============================================================

@app.route("/projects/<int:project_id>/editor/rewrite", methods=["POST"])
@require_access
def rewrite_script_section(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    section_name = request.form.get("section_name", "").strip()
    section_content = _clean_text(request.form.get("section_content", ""))
    style = request.form.get("style", "More engaging").strip()

    if not section_name or not section_content:
        return "Section name dan content wajib diisi.", 400

    rewritten_content = rewrite_section(
        section_name=section_name,
        section_content=section_content,
        style=style,
        language=project.get("language") or "Indonesian"
    )

    if rewritten_content is None:
        return _ai_failed("Gagal membuat rewrite.")

    sections = split_script(project.get("script") or "")

    return render_template(
        "editor.html",
        project=project,
        sections=sections,
        rewrite_preview=rewritten_content,
        rewrite_section_name=section_name,
        rewrite_style=style,
        analysis=None,
        analysis_error=None
    )


# ============================================================
# ACCEPT REWRITE
# ============================================================

@app.route("/projects/<int:project_id>/editor/accept-rewrite", methods=["POST"])
@require_access
def accept_rewrite(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    section_name = request.form.get("section_name", "").strip()
    new_content = _clean_text(request.form.get("new_content", ""))

    if not section_name or not new_content:
        return "Section name dan isi rewrite wajib diisi.", 400

    sections = split_script(project.get("script") or "")
    target_found = False
    target_key = normalize_section_name(section_name)

    for section in sections:
        if normalize_section_name(section.get("name", "")) == target_key:
            section["content"] = new_content
            target_found = True
            break

    if not target_found:
        return "Section tidak ditemukan.", 404

    new_script = combine_sections(sections)

    update_script(project_id, new_script)

    return redirect(f"/projects/{project_id}/editor")


# ============================================================
# SCRIPT ANALYZER
# ============================================================

@app.route("/projects/<int:project_id>/editor/analyze", methods=["POST"])
@require_access
def analyze_script_route(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    script = (project.get("script") or "").strip()

    if not script:
        return "Script kosong.", 400

    analysis = analyze_script(
        script=script,
        language=project.get("language") or "Indonesian"
    )

    if analysis is None:
        return render_template(
            "editor.html",
            project=project,
            sections=split_script(script),
            rewrite_preview=None,
            rewrite_section_name=None,
            rewrite_style=None,
            analysis=None,
            analysis_error="Analisis gagal dibuat atau hasil AI bukan JSON valid. Coba lagi."
        )

    update_analysis(project_id, analysis)

    return render_template(
        "editor.html",
        project=project,
        sections=split_script(script),
        rewrite_preview=None,
        rewrite_section_name=None,
        rewrite_style=None,
        analysis=analysis,
        analysis_error=None
    )


# ============================================================
# REGENERATE OUTLINE
# ============================================================

@app.route("/projects/<int:project_id>/regenerate-outline", methods=["POST"])
@require_access
def regenerate_outline_route(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    new_outline = regenerate_outline(
        topic=project["topic"],
        duration=project["duration"],
        audience=project["audience"],
        language=project["language"]
    )

    if new_outline is None:
        return _ai_failed("Gagal membuat outline baru.")

    new_outline = normalize_outline(new_outline)

    update_outline(project_id, new_outline)

    return redirect(f"/projects/{project_id}")


# ============================================================
# REGENERATE SCRIPT
# ============================================================

@app.route("/projects/<int:project_id>/regenerate-script", methods=["POST"])
@require_access
def regenerate_script_route(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    if not project.get("outline"):
        return "Outline belum tersedia.", 400

    new_script = regenerate_script(
        topic=project["topic"],
        duration=project["duration"],
        audience=project["audience"],
        language=project["language"],
        outline=project["outline"]
    )

    if new_script is None:
        return _ai_failed("Gagal membuat script baru.")

    update_script(project_id, new_script)

    return redirect(f"/projects/{project_id}")


# ============================================================
# REGENERATE METADATA
# ============================================================

@app.route("/projects/<int:project_id>/regenerate-metadata", methods=["POST"])
@require_access
def regenerate_metadata_route(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    new_metadata = generate_metadata(
        topic=project["topic"],
        script=project.get("script") or "",
        outline=project.get("outline"),
        language=project["language"],
        duration=project.get("duration"),
        audience=project.get("audience")
    )

    if new_metadata is None:
        return _ai_failed("Gagal membuat metadata baru.")

    update_metadata(project_id, new_metadata)

    return redirect(f"/projects/{project_id}")


# ============================================================
# RENAME & DELETE PROJECT
# ============================================================

@app.route("/projects/<int:project_id>/rename", methods=["POST"])
@require_access
def rename_project_route(project_id):
    new_topic = request.form.get("new_topic", "").strip()

    if new_topic:
        rename_project(project_id, new_topic[:200])

    return redirect(f"/projects/{project_id}")


@app.route("/projects/<int:project_id>/delete", methods=["POST"])
@require_access
def delete_project_route(project_id):
    delete_project(project_id)
    return redirect("/projects")


# ============================================================
# GENERATOR (MENDUKUNG MODE DRACIN & KONTEN UMUM)
# ============================================================

@app.route("/generate", methods=["POST"])
@require_access
def generate():
    mode = _detect_mode()

    topic = _pick("topic", mode)[:200]
    audience = _pick("audience", mode)
    duration = _pick("duration", mode)
    language = _pick("language", mode)

    # Mode Dracin: fokus adegan boleh kosong, pakai nilai bawaan
    if is_dracin_mode(duration) and not audience:
        audience = "Drama China Rekap Fokus Emosional"

    missing = [
        label
        for label, value in (
            ("judul/topik", topic),
            ("durasi/episode", duration),
            ("audience/fokus adegan", audience),
            ("bahasa", language),
        )
        if not value
    ]

    if missing:
        return "Field berikut wajib diisi: " + ", ".join(missing) + ".", 400

    outline = generate_outline(
        topic=topic,
        duration=duration,
        audience=audience,
        language=language
    )

    if outline is None:
        return _ai_failed("Gagal membuat outline.")

    outline = normalize_outline(outline)

    script = generate_script(
        topic=topic,
        duration=duration,
        audience=audience,
        language=language,
        outline=outline
    )

    if script is None:
        return _ai_failed("Gagal membuat script.")

    metadata = generate_metadata(
        topic=topic,
        script=script,
        outline=outline,
        language=language,
        duration=duration,
        audience=audience
    )

    # Metadata gagal tidak boleh membuang outline dan script yang sudah jadi
    if metadata is None:
        print("Metadata gagal dibuat, project tetap disimpan tanpa metadata.")
        metadata = {}

    project_id = create_project(
        topic=topic,
        duration=duration,
        audience=audience,
        language=language,
        outline=outline,
        script=script,
        metadata=metadata
    )

    if not project_id:
        return "Gagal menyimpan proyek ke database.", 500

    return redirect(f"/projects/{project_id}")


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")