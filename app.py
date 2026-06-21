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


 
# Home Page
 
@app.route("/")
def home():
    return render_template("home.html")


 
# Login Page
 
@app.route("/login")
def login_page():
    return render_template("login.html")


 
# Signup Page
 
@app.route("/signup")
def signup_page():
    return render_template("signup.html")


 
# Dashboard
 
@app.route("/dashboard")
def dashboard():

    # Check if user is logged in
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    # Total Users
    cursor.execute(
        "SELECT COUNT(*) AS total FROM users"
    )
    total_users = cursor.fetchone()["total"]

    # Total Admin Users
    cursor.execute(
        "SELECT COUNT(*) AS total FROM users WHERE role='admin'"
    )
    admin_users = cursor.fetchone()["total"]

    # Total Regular Users
    cursor.execute(
        "SELECT COUNT(*) AS total FROM users WHERE role='user'"
    )
    regular_users = cursor.fetchone()["total"]

    # Recent 5 Users
    cursor.execute("""
        SELECT
            username,
            email,
            role,
            created_at
        FROM users
        ORDER BY created_at DESC
        LIMIT 5
    """)

    recent_users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        email=session["email"],
        role=session["role"],
        total_users=total_users,
        admin_users=admin_users,
        regular_users=regular_users,
        recent_users=recent_users
    )


 
# Admin
 
@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/dashboard")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
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


 
# Delete User
 
@app.route("/delete-user/<int:user_id>")
def delete_user(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/dashboard")

    if user_id == session["user_id"]:
        return redirect("/admin")

    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT username FROM users WHERE id=%s",
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.execute(
        "DELETE FROM users WHERE id=%s",
        (user_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    log_action(
        session["username"],
        f"Deleted User {user['username']}"
    )

    return redirect("/admin")


 
# Edit User
 
@app.route("/edit-user/<int:user_id>")
def edit_user(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/dashboard")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE id=%s
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "edit_user.html",
        user=user
    )



 
# Update User
 
@app.route("/update-user/<int:user_id>", methods=["POST"])
def update_user(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/dashboard")

    username = request.form.get("username")
    email = request.form.get("email")
    role = request.form.get("role")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET username=%s,
            email=%s,
            role=%s
        WHERE id=%s
        """,
        (
            username,
            email,
            role,
            user_id
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    log_action(
        session["username"],
        f"Updated User ID {user_id}"
    )

    return redirect("/admin")

 
# Profile
 
@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE id=%s
        """,
        (session["user_id"],)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "profile.html",
        user=user
    )


# Profile Update

@app.route("/update-profile", methods=["POST"])
def update_profile():

    if "user_id" not in session:
        return redirect("/login")

    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    phone = request.form.get("phone")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET first_name=%s,
            last_name=%s,
            phone=%s
        WHERE id=%s
        """,
        (
            first_name,
            last_name,
            phone,
            session["user_id"]
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    log_action(
        session["username"],
        "Updated Profile"
    )

    return redirect("/profile")


# change password

@app.route("/change-password")
def change_password():

    if "user_id" not in session:
        return redirect("/login")

    return render_template(
        "change_password.html"
    )

# Update Password

@app.route("/update-password", methods=["POST"])
def update_password():

    if "user_id" not in session:
        return redirect("/login")

    current_password = request.form.get(
        "current_password"
    )

    new_password = request.form.get(
        "new_password"
    )

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE id=%s
        """,
        (session["user_id"],)
    )

    user = cursor.fetchone()

    if not bcrypt.checkpw(
        current_password.encode(),
        user["password"].encode()
    ):
        return "Current password incorrect"

    hashed_password = bcrypt.hashpw(
        new_password.encode(),
        bcrypt.gensalt()
    ).decode()

    cursor.execute(
        """
        UPDATE users
        SET password=%s
        WHERE id=%s
        """,
        (
            hashed_password,
            session["user_id"]
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    log_action(
        session["username"],
        "Changed Password"
    )

    return redirect("/profile")


# Logout
 
@app.route("/logout")
def logout():

    if "username" in session:

        log_action(
            session["username"],
            "User Logout"
        )

    session.clear()

    return redirect("/")
 
# Signup API
 
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
        log_action(
            username,
            "New User Registered"
        )

        return jsonify({
            "status": "success",
            "message": "User Created Successfully"
        })
    

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


 
# Login API
 
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

            log_action(
                user["username"],
                "User Login"
            )

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


 
# Health Check
 
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

# Audit Log

@app.route("/audit-logs")
def audit_logs():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return redirect("/dashboard")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM audit_logs
        ORDER BY created_at DESC
        LIMIT 100
    """)

    logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "audit_logs.html",
        logs=logs
    )

 
# Audit Logging

def log_action(username, action):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO audit_logs
        (
            username,
            action
        )
        VALUES
        (
            %s,
            %s
        )
        """,
        (
            username,
            action
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

 
# Run App
 
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )