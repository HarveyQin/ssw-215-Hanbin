import json
import os

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.template_folder = os.path.join(BASE_DIR, "templates")
app.static_folder = os.path.join(BASE_DIR, "static")
PROJECTS_PATH = os.path.join(BASE_DIR, "projects.json")


def load_projects():
    if not os.path.exists(PROJECTS_PATH):
        return []
    with open(PROJECTS_PATH, "r", encoding="utf-8") as file:
        projects = json.load(file)
    return projects if isinstance(projects, list) else []


def save_projects(projects):
    with open(PROJECTS_PATH, "w", encoding="utf-8") as file:
        json.dump(projects, file, indent=2)
        file.write("\n")


projects_db = load_projects()


@app.route("/")
def index():
    projects_db = load_projects()
    return render_template("index.html", projects=projects_db)


@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.get_json(silent=True) or {}
    title = data.get("title")

    if title is None or not str(title).strip():
        return jsonify({"error": "Title is required"}), 400

    projects_db = load_projects()
    next_id = max((project["id"] for project in projects_db), default=0) + 1
    new_project = {
        "id": next_id,
        "title": str(title).strip(),
        "description": "New project",
        "likes": 0,
    }
    projects_db.append(new_project)
    save_projects(projects_db)
    return jsonify(new_project), 201


@app.route("/api/projects/<int:project_id>/upvote", methods=["POST"])
def upvote_project(project_id):
    projects_db = load_projects()
    project = next(
        (project for project in projects_db if project["id"] == project_id),
        None,
    )
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    project["likes"] += 1
    save_projects(projects_db)
    return jsonify({"id": project_id, "likes": project["likes"]})


if __name__ == "__main__":
    app.run(debug=True)
