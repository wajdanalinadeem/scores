from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB = "school.db"

def db():
    return sqlite3.connect(DB)

# -----------------------
# DATABASE SETUP
# -----------------------

def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT,
        name TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT,
        test TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT,
        test TEXT,
        subject TEXT,
        student TEXT,
        score INTEGER
    )
    """)

    con.commit()
    con.close()

# -----------------------
# CLASSES
# -----------------------

@app.route("/classes", methods=["GET"])
def get_classes():
    con = db()
    cur = con.cursor()
    rows = cur.execute("SELECT name FROM classes").fetchall()
    con.close()
    return jsonify([r[0] for r in rows])

@app.route("/classes", methods=["POST"])
def add_class():
    data = request.json
    name = data["name"]
    students = data["students"]

    con = db()
    cur = con.cursor()

    cur.execute("INSERT INTO classes(name) VALUES (?)", (name,))

    for s in students:
        if s.strip():
            cur.execute(
                "INSERT INTO students(class_name, name) VALUES (?,?)",
                (name, s.strip())
            )

    con.commit()
    con.close()

    return jsonify({"status": "ok"})

# -----------------------
# TESTS
# -----------------------

@app.route("/tests/<class_name>")
def get_tests(class_name):
    con = db()
    cur = con.cursor()
    rows = cur.execute(
        "SELECT test FROM tests WHERE class_name=?",
        (class_name,)
    ).fetchall()
    con.close()

    return jsonify([r[0] for r in rows])

@app.route("/tests", methods=["POST"])
def add_test():
    data = request.json

    class_name = str(data["class"])
    test_name = str(data["name"])

    con = db()
    cur = con.cursor()

    cur.execute(
        "INSERT INTO tests(class_name, test) VALUES (?,?)",
        (class_name, test_name)
    )

    con.commit()
    con.close()

    return jsonify({"status": "ok"})


# -----------------------
# SCORES
# -----------------------

@app.route("/scores/<class_name>/<test>/<subject>")
def get_scores(class_name, test, subject):
    con = db()
    cur = con.cursor()

    students = cur.execute(
        "SELECT name FROM students WHERE class_name=?",
        (class_name,)
    ).fetchall()

    result = []

    for s in students:
        student = s[0]
        row = cur.execute("""
            SELECT score FROM scores
            WHERE class_name=? AND test=? AND subject=? AND student=?
        """, (class_name, test, subject, student)).fetchone()

        result.append({
            "student": student,
            "score": row[0] if row else None
        })

    con.close()
    return jsonify(result)

@app.route("/scores", methods=["POST"])
def save_score():
    data = request.json

    con = db()
    cur = con.cursor()

    # delete old score if exists
    cur.execute("""
        DELETE FROM scores
        WHERE class_name=? AND test=? AND subject=? AND student=?
    """, (
        data["class"],
        data["test"],
        data["subject"],
        data["student"]
    ))

    # insert new
    cur.execute("""
        INSERT INTO scores(class_name, test, subject, student, score)
        VALUES (?,?,?,?,?)
    """, (
        data["class"],
        data["test"],
        data["subject"],
        data["student"],
        data["score"]
    ))

    con.commit()
    con.close()

    return jsonify({"status": "saved"})

# -----------------------

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
