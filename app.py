from flask import Flask, render_template, request, jsonify, redirect, session
import pymysql
import bcrypt

app = Flask(__name__)

# Secret key for sessions
app.secret_key = "BhushanSuperSecretKey123"

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "loginuser",
    "password": "Login@123",
    "database": "login_app",
    "cursorclass": pymysql.cursors.DictCursor
}


def get_db():
    return pymysql.connect(**DB_CONFIG)


# ----------------------------
# Home Page
# ----------------------------
@app.route("/")
def home():
    return render_template("home.html")


# ----------------------------
# Login Page
# ----------------------------
@app.route("/login")
def login_page():
    return render_template("login.html")


# ----------------------------
# Signup Page
# ----------------------------
@app.route("/signup")
def signup_page():
    return render_template("signup.html")


# ----------------------------
# Dashboard
# ----------------------------
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        username=session["username"],
        email=session["email"],
        role=session["role"]
    )


# ----------------------------
# Admin
# ----------------------------
@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/dashboard")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               username,
               email,
               role,
               created_at
        FROM users
        ORDER BY id
    """)

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin.html",
        users=users
    )


# ----------------------------
# Delete User
# ----------------------------
@app.route("/delete-user/<int:user_id>")
def delete_user(user_id):

    if session["role"] != "admin":
        return redirect("/dashboard")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM users WHERE id=%s",
        (user_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin")

# ----------------------------
# Profile
# ----------------------------
@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    return render_template(
        "profile.html",
        username=session["username"],
        email=session["email"]
    )

# ----------------------------
# Logout
# ----------------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ----------------------------
# Signup API
# ----------------------------
@app.route("/signup", methods=["POST"])
def signup():

    try:

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()
        cursor = conn.cursor()

        # Check if email exists
        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            cursor.close()
            conn.close()

            return jsonify({
                "status": "failed",
                "message": "Email already exists"
            })

        # Hash password
        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        cursor.execute(
            """
            INSERT INTO users
            (username,email,password)
            VALUES (%s,%s,%s)
            """,
            (
                username,
                email,
                hashed_password
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "User Created Successfully"
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ----------------------------
# Login API
# ----------------------------
@app.route("/login", methods=["POST"])
def login():

    try:

        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email=%s
            """,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user:

            return jsonify({
                "status": "failed",
                "message": "Invalid Email"
            }), 401

        if bcrypt.checkpw(
            password.encode("utf-8"),
            user["password"].encode("utf-8")
        ):

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            return jsonify({
                "status": "success",
                "message": "Login Successful"
            })

        return jsonify({
            "status": "failed",
            "message": "Invalid Password"
        }), 401

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ----------------------------
# Health Check
# ----------------------------
@app.route("/health")
def health():

    try:

        conn = get_db()
        conn.close()

        return jsonify({
            "status": "healthy"
        })

    except Exception as e:

        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        })


# ----------------------------
# Run App
# ----------------------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )