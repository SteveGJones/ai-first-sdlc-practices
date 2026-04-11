"""MiniProject — tiny Flask API with deliberate security issues for smoke testing."""

from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = "users.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    db.commit()
    db.close()


@app.route("/users", methods=["GET"])
def list_users():
    db = get_db()
    # DELIBERATE VULNERABILITY: SQL injection via query parameter
    name_filter = request.args.get("name", "")
    cursor = db.execute(f"SELECT * FROM users WHERE name LIKE '%{name_filter}%'")
    users = [dict(row) for row in cursor.fetchall()]
    db.close()
    return jsonify(users)


@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    # DELIBERATE ISSUE: No input validation
    db = get_db()
    db.execute("INSERT INTO users (name, email) VALUES (?, ?)", (data["name"], data["email"]))
    db.commit()
    db.close()
    return jsonify({"status": "created"}), 201


@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    db.close()
    return jsonify({"status": "deleted"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
