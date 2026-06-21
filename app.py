from flask import Flask, render_template, request, jsonify, redirect, url_for
import pymysql

app = Flask(__name__)

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
    return render_template("dashboard.html")

# Login API
@app.route("/login", methods=["POST"])
def login():

    email = request.form.get("email")
    password = request.form.get("password")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=%s AND password=%s",
        (email, password)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        return jsonify({
            "status": "success"
        })

    return jsonify({
        "status": "failed"
    }), 401


# Signup API
@app.route("/signup", methods=["POST"])
def signup():

    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO users(username,email,password)
        VALUES(%s,%s,%s)
        """,
        (username, email, password)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "User Created Successfully"
    })


if __name__ == "__main__":
    app.run(debug=True)