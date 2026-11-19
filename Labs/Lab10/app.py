import json
import os

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from ai_service import (
    AIRefusalError,
    AIServiceUnavailableError,
    discard_draft_session,
    extract_project_details,
    get_draft_session,
    refine_draft_blind,
    refine_draft_session,
    start_draft_session,
)
from github_service import (
    GitHubRepositoryNotFoundError,
    GitHubServiceUnavailableError,
    InvalidGitHubRepositoryError,
    fetch_readme,
)

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.template_folder = os.path.join(BASE_DIR, "templates")
app.static_folder = os.path.join(BASE_DIR, "static")
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(INSTANCE_DIR, "portfolio.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)


class Author(db.Model):
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    projects = db.relationship("Project", backref="author", lazy=True)


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=False, default="New project")
    likes = db.Column(db.Integer, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey("authors.id"), nullable=False)
    summary = db.Column(db.String(500), nullable=False, default="")
    technologies = db.Column(db.Text, nullable=False, default="")
    difficulty = db.Column(db.String(20), nullable=False, default="Beginner")

    def to_dict(self):
        author_name = self.author.name if self.author else None
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "likes": self.likes,
            "summary": self.summary,
            "technologies": self.technologies,
            "difficulty": self.difficulty,
            "author": author_name,
            "author_name": author_name,
        }


def init_seed_data():
    if Project.query.first() is not None:
        return

    author = Author.query.first()
    if author is None:
        author = Author(name="Hanbin Qin")
        db.session.add(author)
        db.session.flush()

    seed_path = os.path.join(BASE_DIR, "projects_seed.json")
    if not os.path.exists(seed_path):
        return

    with open(seed_path, "r", encoding="utf-8") as file:
        seed_projects = json.load(file)

    for project_data in seed_projects:
        project = Project(
            title=project_data.get("title"),
            description=project_data.get("description", "New project"),
            likes=int(project_data.get("likes", 0) or 0),
            author_id=author.id,
        )
        db.session.add(project)

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()


def migrate_project_columns():
    columns = {column["name"] for column in inspect(db.engine).get_columns("projects")}
    with db.engine.begin() as connection:
        if "summary" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE projects ADD COLUMN summary VARCHAR(500) "
                "NOT NULL DEFAULT ''"
            )
        if "technologies" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE projects ADD COLUMN technologies TEXT "
                "NOT NULL DEFAULT ''"
            )
        if "difficulty" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE projects ADD COLUMN difficulty VARCHAR(20) "
                "NOT NULL DEFAULT 'Beginner'"
            )


with app.app_context():
    db.create_all()
    migrate_project_columns()
    init_seed_data()


@app.route("/")
def index():
    projects = Project.query.order_by(Project.id).all()
    return render_template("index.html", projects=projects)


@app.route("/api/projects", methods=["GET"])
def get_projects():
    projects = Project.query.order_by(Project.id).all()
    return jsonify([project.to_dict() for project in projects]), 200


@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.get_json(silent=True) or {}
    title = data.get("title")

    if title is None or not str(title).strip():
        return jsonify({"error": "Title is required"}), 400

    cleaned_title = str(title).strip()
    if Project.query.filter_by(title=cleaned_title).first() is not None:
        return jsonify({"error": "Project already exists"}), 400

    author = Author.query.first()
    if author is None:
        author = Author(name="Hanbin Qin")
        db.session.add(author)
        db.session.flush()

    project = Project(
        title=cleaned_title,
        description="New project",
        likes=0,
        author_id=author.id,
    )
    db.session.add(project)

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Project already exists"}), 400

    return jsonify(project.to_dict()), 201


@app.route("/api/projects/smart", methods=["POST"])
def smart_create_project():
    data = request.get_json(silent=True)
    notes = data.get("notes") if isinstance(data, dict) else None
    if not isinstance(notes, str) or len(notes.strip()) < 20:
        return jsonify({"error": "Notes must be at least 20 characters"}), 400

    try:
        details = extract_project_details(notes.strip())
    except AIRefusalError:
        return jsonify({"error": "The project notes could not be processed"}), 422
    except AIServiceUnavailableError:
        app.logger.exception("Smart project extraction failed")
        return jsonify({"error": "The AI provider is unavailable"}), 503

    author = Author.query.first()
    if author is None:
        author = Author(name="Hanbin Qin")
        db.session.add(author)
        db.session.flush()

    technology_text = ", ".join(details.technologies)
    project = Project(
        title=details.title,
        description=details.summary,
        summary=details.summary,
        technologies=technology_text,
        difficulty="Beginner",
        likes=0,
        author_id=author.id,
    )
    db.session.add(project)

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "A project with this title could not be created"}), 400

    return jsonify(project.to_dict()), 201


@app.route("/api/projects/git-start", methods=["POST"])
def start_github_import():
    data = request.get_json(silent=True)
    owner = data.get("owner") if isinstance(data, dict) else None
    repo = data.get("repo") if isinstance(data, dict) else None
    if not isinstance(owner, str) or not isinstance(repo, str):
        return jsonify({"error": "GitHub owner and repository are required"}), 400

    owner = owner.strip()
    repo = repo.strip()
    try:
        readme = fetch_readme(owner, repo)
    except InvalidGitHubRepositoryError as error:
        return jsonify({"error": str(error)}), 400
    except GitHubRepositoryNotFoundError:
        return jsonify({"error": "GitHub repository or README not found"}), 404
    except GitHubServiceUnavailableError:
        app.logger.exception("GitHub README fetch failed")
        return jsonify({"error": "GitHub is unavailable"}), 503

    if len(readme.strip()) < 20:
        return jsonify({"error": "README must contain at least 20 characters"}), 400

    try:
        session_id, draft = start_draft_session(readme.strip())
    except AIRefusalError:
        return jsonify({"error": "The project text could not be processed"}), 422
    except AIServiceUnavailableError:
        app.logger.exception("GitHub project draft generation failed")
        return jsonify({"error": "The AI provider is unavailable"}), 503

    return jsonify({"session_id": session_id, "draft": draft}), 201


@app.route("/api/projects/git-refine", methods=["POST"])
def refine_github_import():
    data = request.get_json(silent=True)
    session_id = data.get("session_id") if isinstance(data, dict) else None
    feedback = data.get("feedback") if isinstance(data, dict) else None
    if not isinstance(session_id, str) or not session_id:
        return jsonify({"error": "A session_id is required"}), 400
    if get_draft_session(session_id) is None:
        return jsonify({"error": "Draft session not found"}), 404
    if not isinstance(feedback, str) or not feedback.strip():
        return jsonify({"error": "Feedback is required"}), 400

    try:
        draft = refine_draft_session(session_id, feedback.strip())
    except AIRefusalError:
        return jsonify({"error": "The feedback could not be processed"}), 422
    except AIServiceUnavailableError:
        app.logger.exception("GitHub project draft refinement failed")
        return jsonify({"error": "The AI provider is unavailable"}), 503

    if draft is None:
        return jsonify({"error": "Draft session not found"}), 404
    return jsonify(draft), 200


@app.route("/api/projects/git-refine-blind", methods=["POST"])
def refine_github_import_blind():
    data = request.get_json(silent=True)
    session_id = data.get("session_id") if isinstance(data, dict) else None
    feedback = data.get("feedback") if isinstance(data, dict) else None
    if not isinstance(session_id, str) or not session_id:
        return jsonify({"error": "A session_id is required"}), 400
    if get_draft_session(session_id) is None:
        return jsonify({"error": "Draft session not found"}), 404
    if not isinstance(feedback, str) or not feedback.strip():
        return jsonify({"error": "Feedback is required"}), 400

    try:
        draft = refine_draft_blind(feedback)
    except AIRefusalError:
        return jsonify({"error": "The feedback could not be processed"}), 422
    except AIServiceUnavailableError:
        app.logger.exception("Blind GitHub project draft refinement failed")
        return jsonify({"error": "The AI provider is unavailable"}), 503

    return jsonify(draft), 200


@app.route("/api/projects/git-commit", methods=["POST"])
def commit_github_import():
    data = request.get_json(silent=True)
    session_id = data.get("session_id") if isinstance(data, dict) else None
    if not isinstance(session_id, str) or not session_id:
        return jsonify({"error": "A session_id is required"}), 400

    draft = get_draft_session(session_id)
    if draft is None:
        return jsonify({"error": "Draft session not found"}), 404

    author = Author.query.first()
    try:
        if author is None:
            author = Author(name="Hanbin Qin")
            db.session.add(author)
            db.session.flush()

        project = Project(
            title=draft["title"].strip(),
            description=draft["summary"],
            summary=draft["summary"],
            technologies=", ".join(draft["technologies"]),
            difficulty=draft["difficulty"],
            likes=0,
            author_id=author.id,
        )
        db.session.add(project)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "The approved project could not be saved"}), 400

    discard_draft_session(session_id)
    return jsonify(project.to_dict()), 201


@app.route("/api/projects/<int:project_id>/upvote", methods=["POST"])
def upvote_project(project_id):
    project = Project.query.get(project_id)
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    project.likes += 1

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Unable to update project"}), 400

    return jsonify({"id": project_id, "likes": project.likes}), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        init_seed_data()
    app.run(debug=True)
