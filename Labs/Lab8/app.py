import json
import os

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

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

    def to_dict(self):
        author_name = self.author.name if self.author else None
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "likes": self.likes,
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
    except IntegrityError:
        db.session.rollback()


with app.app_context():
    db.create_all()
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
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Project already exists"}), 400

    return jsonify(project.to_dict()), 201


@app.route("/api/projects/<int:project_id>/upvote", methods=["POST"])
def upvote_project(project_id):
    project = Project.query.get(project_id)
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    project.likes += 1

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Unable to update project"}), 400

    return jsonify({"id": project_id, "likes": project.likes}), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        init_seed_data()
    app.run(debug=True)
