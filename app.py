from flask import Flask, render_template, request, redirect, flash
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os


# Load environment variables
load_dotenv()


app = Flask(__name__)

# Secret key for flash messages
app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "student-management-secret-key"
)


# MySQL Database Connection
db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)


# Home Page + Add Student + Search
@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        course = request.form["course"].strip()
        age = request.form["age"].strip()

        # Basic validation
        if not name or not email or not course or not age:
            flash("All fields are required.", "error")
            return redirect("/")

        # Age validation
        try:
            age = int(age)

        except ValueError:
            flash("Age must be a number.", "error")
            return redirect("/")

        if age < 1 or age > 100:
            flash("Age must be between 1 and 100.", "error")
            return redirect("/")

        cursor = db.cursor()

        try:

            # Check duplicate email
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

            # Insert student
            query = """
            INSERT INTO students (name, email, course, age)
            VALUES (%s, %s, %s, %s)
            """

            values = (name, email, course, age)

            cursor.execute(query, values)

            db.commit()

            flash(
                "Student added successfully!",
                "success"
            )

        except Error:

            db.rollback()

            flash(
                "Database error. Student could not be added.",
                "error"
            )

        finally:

            cursor.close()

        return redirect("/")


    # Search Student
    search = request.args.get("search", "").strip()

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

    cursor.close()

    return render_template(
        "index.html",
        students=students,
        search=search
    )


# Delete Student
@app.route("/delete/<int:id>")
def delete_student(id):

    cursor = db.cursor()

    try:

        cursor.execute(
            "DELETE FROM students WHERE id = %s",
            (id,)
        )

        db.commit()

        flash(
            "Student deleted successfully!",
            "success"
        )

    except Error:

        db.rollback()

        flash(
            "Database error. Student could not be deleted.",
            "error"
        )

    finally:

        cursor.close()

    return redirect("/")


# Edit / Update Student
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):

    cursor = db.cursor()

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        course = request.form["course"].strip()
        age = request.form["age"].strip()

        # Validation
        if not name or not email or not course or not age:

            flash(
                "All fields are required.",
                "error"
            )

            cursor.close()

            return redirect(f"/edit/{id}")

        try:

            age = int(age)

        except ValueError:

            flash(
                "Age must be a number.",
                "error"
            )

            cursor.close()

            return redirect(f"/edit/{id}")

        if age < 1 or age > 100:

            flash(
                "Age must be between 1 and 100.",
                "error"
            )

            cursor.close()

            return redirect(f"/edit/{id}")


        try:

            # Check duplicate email
            cursor.execute(
                """
                SELECT id FROM students
                WHERE email = %s AND id != %s
                """,
                (email, id)
            )

            existing_student = cursor.fetchone()

            if existing_student:

                flash(
                    "Another student already uses this email.",
                    "error"
                )

                cursor.close()

                return redirect(f"/edit/{id}")


            # Update student
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

        except Error:

            db.rollback()

            flash(
                "Database error. Student could not be updated.",
                "error"
            )

        finally:

            cursor.close()

        return redirect("/")


    # Get existing student
    cursor.execute(
        "SELECT * FROM students WHERE id = %s",
        (id,)
    )

    student = cursor.fetchone()

    cursor.close()

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
