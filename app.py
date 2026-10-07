from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "college-internship-secret-key"


def init_db():

    connection = sqlite3.connect("internship.db")

    connection.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            college_name TEXT NOT NULL,
            course TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS internships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            internship_title TEXT NOT NULL,
            location TEXT NOT NULL,
            duration TEXT NOT NULL,
            stipend TEXT NOT NULL,
            skills TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            internship_id INTEGER NOT NULL,
            application_date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (internship_id) REFERENCES internships(id)
        )
    """)

    connection.commit()
    connection.close()


init_db()


@app.route("/")
def home():

    return render_template("index.html")


@app.route("/about")
def about():

    return render_template("about.html")


@app.route("/contact")
def contact():

    return render_template("contact.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        college_name = request.form["college_name"]
        course = request.form["course"]
        password = request.form["password"]

        connection = sqlite3.connect("internship.db")

        try:

            connection.execute("""
                INSERT INTO students
                (full_name, email, college_name, course, password)
                VALUES (?, ?, ?, ?, ?)
            """, (
                full_name,
                email,
                college_name,
                course,
                password
            ))

            connection.commit()
            connection.close()

            return redirect("/login")

        except sqlite3.IntegrityError:

            connection.close()

            return "Email already registered."


    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = sqlite3.connect("internship.db")

        student = connection.execute(
            "SELECT * FROM students WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()

        connection.close()

        if student:

            session["student_id"] = student[0]
            session["student_name"] = student[1]

            return redirect("/dashboard")

        return "Invalid Email or Password"


    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "student_id" not in session:

        return redirect("/login")

    connection = sqlite3.connect("internship.db")

    student = connection.execute(
        "SELECT * FROM students WHERE id = ?",
        (session["student_id"],)
    ).fetchone()

    connection.close()

    if student:

        return render_template(
            "dashboard.html",
            student=student
        )

    session.clear()

    return redirect("/login")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


@app.route("/internships")
def internships():

    connection = sqlite3.connect("internship.db")

    internship_list = connection.execute(
        "SELECT * FROM internships"
    ).fetchall()

    connection.close()

    return render_template(
        "internships.html",
        internships=internship_list
    )


@app.route("/add-internship", methods=["GET", "POST"])
def add_internship():

    if "admin" not in session:

        return redirect("/admin-login")

    if request.method == "POST":

        company_name = request.form["company_name"]
        internship_title = request.form["internship_title"]
        location = request.form["location"]
        duration = request.form["duration"]
        stipend = request.form["stipend"]
        skills = request.form["skills"]

        connection = sqlite3.connect("internship.db")

        connection.execute("""
            INSERT INTO internships
            (company_name, internship_title, location, duration, stipend, skills)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            company_name,
            internship_title,
            location,
            duration,
            stipend,
            skills
        ))

        connection.commit()
        connection.close()

        return redirect("/internships")


    return render_template("add_internship.html")


@app.route("/edit-internship/<int:internship_id>", methods=["GET", "POST"])
def edit_internship(internship_id):

    if "admin" not in session:

        return redirect("/admin-login")

    connection = sqlite3.connect("internship.db")

    internship = connection.execute(
        "SELECT * FROM internships WHERE id = ?",
        (internship_id,)
    ).fetchone()

    if not internship:

        connection.close()

        return "Internship not found"


    if request.method == "POST":

        company_name = request.form["company_name"]
        internship_title = request.form["internship_title"]
        location = request.form["location"]
        duration = request.form["duration"]
        stipend = request.form["stipend"]
        skills = request.form["skills"]

        connection.execute("""
            UPDATE internships
            SET company_name = ?,
                internship_title = ?,
                location = ?,
                duration = ?,
                stipend = ?,
                skills = ?
            WHERE id = ?
        """, (
            company_name,
            internship_title,
            location,
            duration,
            stipend,
            skills,
            internship_id
        ))

        connection.commit()
        connection.close()

        return redirect("/internships")


    connection.close()

    return render_template(
        "edit_internship.html",
        internship=internship
    )


@app.route("/delete-internship/<int:internship_id>")
def delete_internship(internship_id):

    if "admin" not in session:

        return redirect("/admin-login")

    connection = sqlite3.connect("internship.db")

    connection.execute(
        "DELETE FROM applications WHERE internship_id = ?",
        (internship_id,)
    )

    connection.execute(
        "DELETE FROM internships WHERE id = ?",
        (internship_id,)
    )

    connection.commit()
    connection.close()

    return redirect("/internships")


@app.route("/apply/<int:internship_id>")
def apply(internship_id):

    if "student_id" not in session:

        return redirect("/login")

    connection = sqlite3.connect("internship.db")

    internship = connection.execute(
        "SELECT * FROM internships WHERE id = ?",
        (internship_id,)
    ).fetchone()

    connection.close()

    if internship:

        return render_template(
            "apply.html",
            internship=internship,
            student_name=session["student_name"]
        )

    return "Internship not found"


@app.route("/submit-application/<int:internship_id>", methods=["POST"])
def submit_application(internship_id):

    if "student_id" not in session:

        return redirect("/login")

    student_id = session["student_id"]

    connection = sqlite3.connect("internship.db")

    existing_application = connection.execute("""
        SELECT id
        FROM applications
        WHERE student_id = ? AND internship_id = ?
    """, (
        student_id,
        internship_id
    )).fetchone()

    if existing_application:

        connection.close()

        return "You have already applied for this internship."


    application_date = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    connection.execute("""
        INSERT INTO applications
        (student_id, internship_id, application_date, status)
        VALUES (?, ?, ?, ?)
    """, (
        student_id,
        internship_id,
        application_date,
        "Pending"
    ))

    connection.commit()
    connection.close()

    return redirect("/my-applications")


@app.route("/my-applications")
def my_applications():

    if "student_id" not in session:

        return redirect("/login")

    student_id = session["student_id"]

    connection = sqlite3.connect("internship.db")

    applications = connection.execute("""
        SELECT
            applications.id,
            internships.internship_title,
            internships.company_name,
            applications.application_date,
            applications.status
        FROM applications
        JOIN internships
        ON applications.internship_id = internships.id
        WHERE applications.student_id = ?
        ORDER BY applications.id DESC
    """, (student_id,)).fetchall()

    connection.close()

    return render_template(
        "my_applications.html",
        applications=applications
    )


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        if email == "admin@gmail.com" and password == "admin123":

            session["admin"] = True

            return redirect("/admin-dashboard")

        return "Invalid Admin Email or Password"


    return render_template("admin_login.html")


@app.route("/admin-dashboard")
def admin_dashboard():

    if "admin" not in session:

        return redirect("/admin-login")

    connection = sqlite3.connect("internship.db")

    total_students = connection.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    total_internships = connection.execute(
        "SELECT COUNT(*) FROM internships"
    ).fetchone()[0]

    total_applications = connection.execute(
        "SELECT COUNT(*) FROM applications"
    ).fetchone()[0]

    pending_applications = connection.execute(
        "SELECT COUNT(*) FROM applications WHERE status = 'Pending'"
    ).fetchone()[0]

    connection.close()

    return render_template(
        "admin_dashboard.html",
        total_students=total_students,
        total_internships=total_internships,
        total_applications=total_applications,
        pending_applications=pending_applications
    )


@app.route("/admin-applications")
def admin_applications():

    if "admin" not in session:

        return redirect("/admin-login")

    connection = sqlite3.connect("internship.db")

    applications = connection.execute("""
        SELECT
            applications.id,
            students.full_name,
            students.email,
            students.college_name,
            students.course,
            internships.internship_title,
            internships.company_name,
            applications.application_date,
            applications.status
        FROM applications
        JOIN students
        ON applications.student_id = students.id
        JOIN internships
        ON applications.internship_id = internships.id
        ORDER BY applications.id DESC
    """).fetchall()

    connection.close()

    return render_template(
        "admin_applications.html",
        applications=applications
    )


@app.route("/approve-application/<int:application_id>")
def approve_application(application_id):

    if "admin" not in session:

        return redirect("/admin-login")

    connection = sqlite3.connect("internship.db")

    connection.execute("""
        UPDATE applications
        SET status = 'Approved'
        WHERE id = ?
    """, (application_id,))

    connection.commit()
    connection.close()

    return redirect("/admin-applications")


@app.route("/reject-application/<int:application_id>")
def reject_application(application_id):

    if "admin" not in session:

        return redirect("/admin-login")

    connection = sqlite3.connect("internship.db")

    connection.execute("""
        UPDATE applications
        SET status = 'Rejected'
        WHERE id = ?
    """, (application_id,))

    connection.commit()
    connection.close()

    return redirect("/admin-applications")


@app.route("/admin-logout")
def admin_logout():

    session.pop("admin", None)

    return redirect("/")


if __name__ == "__main__":

    app.run(debug=True)