import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

PROJECTS_FILE = Path(__file__).with_name("projects.json")


def load_projects():
    with PROJECTS_FILE.open(encoding="utf-8") as projects_file:
        return json.load(projects_file)


def save_projects(projects_db):
    with PROJECTS_FILE.open("w", encoding="utf-8") as projects_file:
        json.dump(projects_db, projects_file, indent=2)


@app.route("/")
def index():
    projects_db = load_projects()
    return render_template("index.html", projects=projects_db)


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


@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.get_json(silent=True)
    title = data.get("title") if isinstance(data, dict) else None
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "A non-empty title is required"}), 400

    projects_db = load_projects()
    project = {
        "id": max((item["id"] for item in projects_db), default=0) + 1,
        "title": title.strip(),
        "description": "",
        "likes": 0,
    }
    projects_db.append(project)
    save_projects(projects_db)
    return jsonify(project), 201


if __name__ == "__main__":
    app.run(debug=True)
