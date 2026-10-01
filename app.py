from flask import Flask, render_template, request, redirect, flash
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import time

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "student-management-secret-key"
)


def get_db_connection():
    max_retries = 10

    for attempt in range(max_retries):
        try:
            connection = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME")
            )

            if connection.is_connected():
                return connection

        except Error as e:
            print(
                f"Database connection attempt "
                f"{attempt + 1}/{max_retries} failed: {e}"
            )
            time.sleep(3)

    raise Exception("Could not connect to MySQL database.")


@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        course = request.form["course"].strip()
        age = request.form["age"].strip()

        if not name or not email or not course or not age:
            flash("All fields are required.", "error")
            return redirect("/")

        try:
            age = int(age)
        except ValueError:
            flash("Age must be a number.", "error")
            return redirect("/")

        if age < 1 or age > 100:
            flash("Age must be between 1 and 100.", "error")
            return redirect("/")

        db = None
        cursor = None

        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute(
                "SELECT id FROM students WHERE email = %s",
                (email,)
            )

            existing_student = cursor.fetchone()

            if existing_student:
                flash(
                    "A student with this email already exists.",
                    "error"
                )
                return redirect("/")

            query = """
            INSERT INTO students (name, email, course, age)
            VALUES (%s, %s, %s, %s)
            """

            values = (name, email, course, age)

            cursor.execute(query, values)
            db.commit()

            flash("Student added successfully!", "success")

        except Error as e:
            if db:
                db.rollback()

            print("Database error:", e)
            flash(
                "Database error. Student could not be added.",
                "error"
            )

        finally:
            if cursor:
                cursor.close()

            if db and db.is_connected():
                db.close()

        return redirect("/")

    search = request.args.get("search", "").strip()

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        if search:

            query = """
            SELECT * FROM students
            WHERE name LIKE %s
            """

            cursor.execute(
                query,
                ("%" + search + "%",)
            )

        else:
            cursor.execute(
                "SELECT * FROM students"
            )

        students = cursor.fetchall()

    except Error as e:

        print("Database error:", e)

        flash(
            "Database error. Could not load students.",
            "error"
        )

        students = []

    finally:

        if cursor:
            cursor.close()

        if db and db.is_connected():
            db.close()

    return render_template(
        "index.html",
        students=students,
        search=search
    )


@app.route("/delete/<int:id>")
def delete_student(id):

    db = None
    cursor = None

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "DELETE FROM students WHERE id = %s",
            (id,)
        )

        db.commit()

        flash(
            "Student deleted successfully!",
            "success"
        )

    except Error as e:

        if db:
            db.rollback()

        print("Database error:", e)

        flash(
            "Database error. Student could not be deleted.",
            "error"
        )

    finally:

        if cursor:
            cursor.close()

        if db and db.is_connected():
            db.close()

    return redirect("/")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        course = request.form["course"].strip()
        age = request.form["age"].strip()

        if not name or not email or not course or not age:

            flash(
                "All fields are required.",
                "error"
            )

            return redirect(f"/edit/{id}")

        try:
            age = int(age)

        except ValueError:

            flash(
                "Age must be a number.",
                "error"
            )

            return redirect(f"/edit/{id}")

        if age < 1 or age > 100:

            flash(
                "Age must be between 1 and 100.",
                "error"
            )

            return redirect(f"/edit/{id}")

        db = None
        cursor = None

        try:

            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute(
                """
                SELECT id
                FROM students
                WHERE email = %s
                AND id != %s
                """,
                (email, id)
            )

            existing_student = cursor.fetchone()

            if existing_student:

                flash(
                    "Another student already uses this email.",
                    "error"
                )

                return redirect(f"/edit/{id}")

            query = """
            UPDATE students
            SET name = %s,
                email = %s,
                course = %s,
                age = %s
            WHERE id = %s
            """

            values = (
                name,
                email,
                course,
                age,
                id
            )

            cursor.execute(
                query,
                values
            )

            db.commit()

            flash(
                "Student updated successfully!",
                "success"
            )

        except Error as e:

            if db:
                db.rollback()

            print("Database error:", e)

            flash(
                "Database error. Student could not be updated.",
                "error"
            )

        finally:

            if cursor:
                cursor.close()

            if db and db.is_connected():
                db.close()

        return redirect("/")

    db = None
    cursor = None

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM students WHERE id = %s",
            (id,)
        )

        student = cursor.fetchone()

    except Error as e:

        print("Database error:", e)

        flash(
            "Database error.",
            "error"
        )

        return redirect("/")

    finally:

        if cursor:
            cursor.close()

        if db and db.is_connected():
            db.close()

    if student is None:

        flash(
            "Student not found.",
            "error"
        )

        return redirect("/")

    return render_template(
        "edit.html",
        student=student
    )


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
