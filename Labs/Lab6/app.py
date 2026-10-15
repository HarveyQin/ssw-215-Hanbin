from flask import Flask, jsonify, render_template

app = Flask(__name__)

projects_db = [
    {
        "id": 1,
        "title": "LLM in software testing.",
        "description": "Exploring the use of large language models in software testing.",
        "likes": 0,
    },
    {
        "id": 2,
        "title": "AI for SE.",
        "description": "Exploring the use of large language models in software development.",
        "likes": 0,
    }
]


@app.route("/")
def index():
    return render_template("index.html", projects=projects_db)


@app.route("/api/projects/<int:project_id>/upvote", methods=["POST"])
def upvote_project(project_id):
    project = next(
        (project for project in projects_db if project["id"] == project_id),
        None,
    )
    if project is None:
        return jsonify({"error": "Project not found"}), 404

    project["likes"] += 1
    return jsonify({"id": project_id, "likes": project["likes"]})


if __name__ == "__main__":
    app.run(debug=True)
