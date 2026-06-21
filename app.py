from flask import Flask, render_template, request, jsonify, redirect, session
import pymysql
import bcrypt
from itsdangerous import URLSafeTimedSerializer
import re
from email_service import send_email

app = Flask(__name__)

# Secret key for sessions
app.secret_key = "BhushanSuperSecretKey123"

serializer = URLSafeTimedSerializer(
    app.secret_key
)

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

# Forgot Password

@app.route(
    "/forgot-password",
    methods=["GET","POST"]
)
def forgot_password():

    if request.method == "GET":
        return render_template(
            "forgot_password.html"
        )

    email = request.form.get("email")

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

    if not user:
        return "Email not found"

    token = serializer.dumps(
        email,
        salt="password-reset"
    )

    print(
        f"Reset Link: "
        f"http://localhost:5000/reset-password/{token}"
    )

    log_action(
        user["username"],
        "Password Reset Requested"
    )

    return """
    Password reset link generated.
    Check terminal output.
    """

# reset password

@app.route(
    "/reset-password/<token>",
    methods=["GET","POST"]
)
def reset_password(token):

    try:

        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=3600
        )

    except Exception:

        return "Invalid or Expired Link"

    if request.method == "GET":

        return render_template(
            "reset_password.html",
            token=token
        )

    password = request.form.get(
        "password"
    )

    is_valid, message = validate_password(password)

    if not is_valid:
        return message

    hashed_password = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET password=%s
        WHERE email=%s
        """,
        (
            hashed_password,
            email
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/login")

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
            account_locked,
            email_verified,
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
        
        is_valid, message = validate_password(password)

        if not is_valid:
            return jsonify({
                "status": "failed",
                "message": message
            }), 400

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


        verification_token = serializer.dumps(
            email,
            salt="email-verification"
        )

        verification_link = (
            f"http://localhost:5000/verify-email/{verification_token}"
        )

        html_body = f"""
        <h2>Welcome {username}</h2>

        <p>
        Please verify your email address.
        </p>

        <p>
        <a href="{verification_link}">
        Verify Email
        </a>
        </p>
        """

        send_email(
            email,
            "Verify Your Email",
            html_body
        )
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

# Unlock User

@app.route("/unlock-user/<int:user_id>")
def unlock_user(user_id):

    if session["role"] != "admin":
        return redirect("/dashboard")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET
            failed_attempts = 0,
            account_locked = FALSE
        WHERE id=%s
    """, (user_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin")


# Email Verification

@app.route("/verify-email/<token>")
def verify_email(token):

    try:

        email = serializer.loads(
            token,
            salt="email-verification",
            max_age=86400
        )

    except Exception:

        return """
        Verification link expired
        """

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET email_verified=TRUE
        WHERE email=%s
        """,
        (email,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return """
    Email verified successfully.
    You can now login.
    """

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

        # User not found
        if not user:

            cursor.close()
            conn.close()

            return jsonify({
                "status": "failed",
                "message": "User not found"
            }), 404

        # Email verification check
        if not user["email_verified"]:

            cursor.close()
            conn.close()

            return jsonify({
                "status": "failed",
                "message": "Please verify your email before login."
            }), 403

        # Account locked check
        if user["account_locked"]:

            cursor.close()
            conn.close()

            return jsonify({
                "status": "failed",
                "message": "Account Locked. Contact Administrator."
            }), 403

        # Password validation
        if bcrypt.checkpw(
            password.encode("utf-8"),
            user["password"].encode("utf-8")
        ):

            # Reset failed attempts
            cursor.execute(
                """
                UPDATE users
                SET
                    failed_attempts = 0
                WHERE id=%s
                """,
                (user["id"],)
            )

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            log_action(
                user["username"],
                "User Login"
            )

            ip_address = request.remote_addr

            cursor.execute(
                """
                INSERT INTO login_history
                (
                    username,
                    ip_address
                )
                VALUES
                (
                    %s,
                    %s
                )
                """,
                (
                    user["username"],
                    ip_address
                )
            )

            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({
                "status": "success",
                "message": "Login Successful"
            })

        # Invalid password
        cursor.execute(
            """
            UPDATE users
            SET failed_attempts = failed_attempts + 1
            WHERE id=%s
            """,
            (user["id"],)
        )

        cursor.execute(
            """
            SELECT failed_attempts
            FROM users
            WHERE id=%s
            """,
            (user["id"],)
        )

        attempts = cursor.fetchone()["failed_attempts"]

        if attempts >= 5:

            cursor.execute(
                """
                UPDATE users
                SET account_locked = TRUE
                WHERE id=%s
                """,
                (user["id"],)
            )

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "status": "failed",
            "message": f"Invalid Password. Attempts: {attempts}/5"
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


# Login History

@app.route("/login-history")
def login_history():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM login_history
        ORDER BY login_time DESC
    """)

    logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "login_history.html",
        logs=logs
    )


# Password Validation

def validate_password(password):

    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain an uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain a lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain a number"

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain a special character"

    return True, "Valid Password"

# Run App
 
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )