from flask import Flask, render_template, request, redirect
import json

from core.content import (
    generate_outline,
    regenerate_outline,
    generate_script,
    regenerate_script,
    generate_metadata,
    normalize_outline
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
    combine_sections
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

app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static"
)


# ============================================================
# DATABASE
# ============================================================

try:
    init_database()
except Exception as e:
    print("Database init handled:", e)


# ============================================================
# FILE HELPERS
# ============================================================

def save_text(filename, content):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)
    except Exception as e:
        print(f"Skipped saving file {filename}: {e}")


def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Skipped saving JSON {filename}: {e}")


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# SETTINGS
# ============================================================

@app.route("/settings")
def settings():
    return render_template("settings.html")


# ============================================================
# PROJECTS
# ============================================================

@app.route("/projects")
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
            research=None,
            error=(
                "Research gagal dibuat. "
                "Periksa API key, koneksi internet, "
                "atau coba lagi."
            )
        )

    update_research(project_id, research)
    save_json("research.json", research)

    return redirect(f"/projects/{project_id}/research")


# ============================================================
# GENERATE OUTLINE FROM RESEARCH
# ============================================================

@app.route("/projects/<int:project_id>/research/generate-outline", methods=["POST"])
def generate_outline_from_research_route(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    research = project.get("research")

    if not research:
        return (
            "Research belum tersedia. Jalankan Research terlebih dahulu.",
            400
        )

    outline = generate_outline_from_research(
        project=project,
        research=research
    )

    if outline is None:
        return "Gagal membuat outline dari research.", 500

    outline = normalize_outline(outline)

    update_outline(project_id, outline)
    save_json("outline.json", outline)

    return redirect(f"/projects/{project_id}")


# ============================================================
# GENERATE SCRIPT FROM OUTLINE
# ============================================================

@app.route("/projects/<int:project_id>/research/generate-script", methods=["POST"])
def generate_script_from_outline_route(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    outline = project.get("outline")

    if not outline:
        return (
            "Outline belum tersedia. Generate Outline terlebih dahulu.",
            400
        )

    script_data = generate_script_from_outline(
        project=project,
        outline=outline
    )

    if script_data is None:
        return "Gagal membuat script dari outline.", 500

    script = script_to_text(script_data)

    if not script:
        return "Script hasil generate kosong.", 500

    update_script(project_id, script)
    save_text("script.txt", script)

    return redirect(f"/projects/{project_id}/editor")


# ============================================================
# SCRIPT EDITOR
# ============================================================

@app.route("/projects/<int:project_id>/editor")
def script_editor(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    sections = split_script(project.get("script", ""))

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

@app.route("/projects/<int:project_id>/editor/save", methods=["POST"])
def save_script_editor(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    section_names = request.form.getlist("section_name")
    section_contents = request.form.getlist("section_content")

    sections = [
        {"name": name, "content": content}
        for name, content in zip(section_names, section_contents)
    ]

    new_script = combine_sections(sections)

    update_script(project_id, new_script)
    save_text("script.txt", new_script)

    return redirect(f"/projects/{project_id}/editor")


# ============================================================
# REWRITE SCRIPT SECTION
# ============================================================

@app.route("/projects/<int:project_id>/editor/rewrite", methods=["POST"])
def rewrite_script_section(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    section_name = request.form.get("section_name", "").strip()
    section_content = request.form.get("section_content", "").strip()
    style = request.form.get("style", "More engaging").strip()

    if not section_name or not section_content:
        return "Section name dan content wajib diisi.", 400

    rewritten_content = rewrite_section(
        section_name=section_name,
        section_content=section_content,
        style=style,
        language=project.get("language", "Indonesian")
    )

    if rewritten_content is None:
        return "Gagal membuat rewrite.", 500

    sections = split_script(project.get("script", ""))

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
def accept_rewrite(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    section_name = request.form.get("section_name", "").strip()
    new_content = request.form.get("new_content", "").strip()

    if not section_name or not new_content:
        return "Section name dan isi rewrite wajib diisi.", 400

    sections = split_script(project.get("script", ""))
    target_found = False

    for section in sections:
        if section.get("name", "").strip().upper() == section_name.upper():
            section["content"] = new_content
            target_found = True
            break

    if not target_found:
        return "Section tidak ditemukan.", 404

    new_script = combine_sections(sections)

    update_script(project_id, new_script)
    save_text("script.txt", new_script)

    return redirect(f"/projects/{project_id}/editor")


# ============================================================
# SCRIPT ANALYZER
# ============================================================

@app.route("/projects/<int:project_id>/editor/analyze", methods=["POST"])
def analyze_script_route(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    script = project.get("script", "").strip()

    if not script:
        return "Script kosong.", 400

    result = analyze_script(
        script=script,
        language=project.get("language", "Indonesian")
    )

    if result is None:
        return "Gagal menganalisis script.", 500

    try:
        analysis = json.loads(result)
    except json.JSONDecodeError:
        return render_template(
            "editor.html",
            project=project,
            sections=split_script(script),
            rewrite_preview=None,
            rewrite_section_name=None,
            rewrite_style=None,
            analysis=None,
            analysis_error="AI mengembalikan hasil yang bukan JSON valid."
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
        return "Gagal membuat outline baru.", 500

    new_outline = normalize_outline(new_outline)

    update_outline(project_id, new_outline)
    save_json("outline.json", new_outline)

    return redirect(f"/projects/{project_id}")


# ============================================================
# REGENERATE SCRIPT
# ============================================================

@app.route("/projects/<int:project_id>/regenerate-script", methods=["POST"])
def regenerate_script_route(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    new_script = regenerate_script(
        topic=project["topic"],
        duration=project["duration"],
        audience=project["audience"],
        language=project["language"],
        outline=project["outline"]
    )

    if new_script is None:
        return "Gagal membuat script baru.", 500

    update_script(project_id, new_script)
    save_text("script.txt", new_script)

    return redirect(f"/projects/{project_id}")


# ============================================================
# REGENERATE METADATA
# ============================================================

@app.route("/projects/<int:project_id>/regenerate-metadata", methods=["POST"])
def regenerate_metadata_route(project_id):
    project = get_project(project_id)

    if project is None:
        return "Project tidak ditemukan.", 404

    new_metadata = generate_metadata(
        topic=project["topic"],
        script=project["script"],
        outline=project["outline"],
        language=project["language"]
    )

    if new_metadata is None:
        return "Gagal membuat metadata baru.", 500

    update_metadata(project_id, new_metadata)
    save_json("metadata.json", new_metadata)

    return redirect(f"/projects/{project_id}")


# ============================================================
# RENAME PROJECT
# ============================================================

@app.route("/projects/<int:project_id>/rename", methods=["POST"])
def rename_project_route(project_id):
    new_topic = request.form.get("new_topic", "").strip()

    if new_topic:
        rename_project(project_id, new_topic)

    return redirect(f"/projects/{project_id}")


# ============================================================
# DELETE PROJECT
# ============================================================

@app.route("/projects/<int:project_id>/delete", methods=["POST"])
def delete_project_route(project_id):
    delete_project(project_id)
    return redirect("/projects")


# ============================================================
# GENERATOR
# ============================================================

@app.route("/generate", methods=["POST"])
def generate():
    topic = request.form.get("topic", "").strip()
    duration = request.form.get("duration", "").strip()
    audience = request.form.get("audience", "").strip()
    language = request.form.get("language", "").strip()

    if not topic or not duration or not audience or not language:
        return "Semua field input wajib diisi.", 400

    outline = generate_outline(
        topic=topic,
        duration=duration,
        audience=audience,
        language=language
    )

    if outline is None:
        return "Gagal membuat outline.", 500

    outline = normalize_outline(outline)

    script = generate_script(
        topic=topic,
        duration=duration,
        audience=audience,
        language=language,
        outline=outline
    )

    if script is None:
        return "Gagal membuat script.", 500

    metadata = generate_metadata(
        topic=topic,
        script=script,
        outline=outline,
        language=language
    )

    if metadata is None:
        return "Gagal membuat metadata.", 500

    try:
        save_json("outline.json", outline)
        save_text("script.txt", script)
        save_json("metadata.json", metadata)
    except Exception as e:
        print("Abaikan error penulisan file lokal di serverless:", e)

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

app = app

if __name__ == "__main__":
    app.run(debug=True)