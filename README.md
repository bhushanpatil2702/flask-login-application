# Flask Login Application

A simple Login and Signup application built using:

* Python Flask
* MySQL
* HTML
* CSS
* JavaScript

## Features

* Home Page
* User Registration (Sign Up)
* User Login
* Dashboard Page
* MySQL Database Integration
* Form Validation
* Responsive UI

---

## Project Structure

```text
login/
│
├── app.py
│
├── templates/
│   ├── home.html
│   ├── login.html
│   ├── signup.html
│   └── dashboard.html
│
├── static/
│   └── style.css
│
├── requirements.txt
│
└── README.md
```

---

## Prerequisites

* Python 3.12+
* MySQL 8.x
* pip
* Virtual Environment (venv)

---

## Create Virtual Environment

```bash
python3 -m venv venv
```

Activate Virtual Environment:

### Linux / Mac

```bash
source venv/bin/activate
```

### Windows

```cmd
venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install flask pymysql
```

Generate requirements file:

```bash
pip freeze > requirements.txt
```

---

## MySQL Database Setup

Login to MySQL:

```bash
mysql -u root -p
```

Create Database:

```sql
CREATE DATABASE login_app;
```

Use Database:

```sql
USE login_app;
```

Create Users Table:

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    password VARCHAR(255)
);
```

Create Application User:

```sql
CREATE USER 'loginuser'@'localhost'
IDENTIFIED BY 'Login@123';

GRANT ALL PRIVILEGES
ON login_app.*
TO 'loginuser'@'localhost';

FLUSH PRIVILEGES;
```

---

## Configure Database Connection

Update `app.py`:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "loginuser",
    "password": "Login@123",
    "database": "login_app"
}
```

---

## Run Application

```bash
python3 app.py
```

Application will start on:

```text
http://localhost:5000
```

---

## Application Flow

```text
Home Page
    |
    +--> Login
    |
    +--> Sign Up
              |
              v
         MySQL Database
              |
              v
         Dashboard
```

---

## API Endpoints

### Home Page

```http
GET /
```

### Login Page

```http
GET /login
```

### Login API

```http
POST /login
```

### Signup Page

```http
GET /signup
```

### Signup API

```http
POST /signup
```

### Dashboard

```http
GET /dashboard
```

---

## Example User

```text
Email: bhushan@gmail.com
Password: Password123
```

---

## Security Improvements (Recommended)

Current version stores passwords in plain text for learning purposes.

For production:

* Use bcrypt password hashing
* Flask Sessions
* CSRF Protection
* JWT Authentication
* Input Validation
* HTTPS
* Environment Variables for Secrets

---

## Future Enhancements

* Forgot Password
* Email Verification
* User Profile
* Admin Dashboard
* Role Based Access Control
* Docker Support
* AWS Deployment
* GitLab CI/CD Pipeline

---

## Author

Bhushan Patil

DevOps | Cloud | AWS | Python | Flask
