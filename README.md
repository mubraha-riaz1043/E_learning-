# 🎓 EduFlow — E-Learning Platform

A full-stack e-learning web application built with **Flask + MySQL + Bootstrap**.

---

## 📁 Folder Structure

```
elearning/
├── app.py                  # Flask application (all routes)
├── requirements.txt        # Python dependencies
├── schema.sql              # MySQL database schema + seed data
├── README.md               # This file
├── static/
│   ├── css/               # Custom stylesheets (if any)
│   └── js/                # Custom scripts (if any)
└── templates/
    ├── base.html           # Shared layout (navbar, flash, footer)
    ├── home.html           # Landing page
    ├── auth/
    │   ├── login.html
    │   └── register.html
    ├── student/
    │   ├── dashboard.html  # Student home after login
    │   ├── courses.html    # Browse all courses
    │   ├── course_detail.html
    │   ├── module.html     # Module content viewer
    │   ├── quiz.html       # Quiz attempt page
    │   ├── result.html     # Immediate quiz result
    │   └── results.html    # All past results
    └── admin/
        ├── dashboard.html
        ├── categories.html
        ├── courses.html
        ├── modules.html
        ├── questions.html
        └── users.html
```

---

## ✅ Prerequisites

- Python 3.9+
- MySQL 8.0+
- pip

---

## 🚀 Step-by-Step Setup Guide

### Step 1 — Clone / Download the project
```bash
# Place the elearning/ folder wherever you like
cd elearning
```

### Step 2 — Create a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Set up MySQL database

Open **MySQL Workbench** or the MySQL terminal and run:
```sql
source /full/path/to/elearning/schema.sql
```
Or paste the contents of `schema.sql` into MySQL Workbench and execute.

This creates the `elearning` database with all 11 tables and sample data.

### Step 5 — Configure database password

Open `app.py` and find this section near the top:
```python
DB_CONFIG = {
    'host':     'localhost',
    'user':     'root',
    'password': '',        # ← Change to your MySQL root password
    'database': 'elearning',
}
```

Update `password` with your MySQL password.

### Step 6 — Fix seed data passwords (one-time)

The schema seeds two demo accounts, but their passwords are placeholder hashes.
Run this once to set real passwords:

```bash
python fix_passwords.py
```

Or manually register via `/register` and use the admin panel to promote yourself.

**Quick fix** — run this in a Python shell inside the project folder:
```python
from werkzeug.security import generate_password_hash
import mysql.connector
db = mysql.connector.connect(host='localhost', user='root', password='YOUR_PW', database='elearning')
cur = db.cursor()
cur.execute("UPDATE user SET password=%s WHERE email='admin@elearn.com'",
            (generate_password_hash('admin123'),))
cur.execute("UPDATE user SET password=%s WHERE email='alice@elearn.com'",
            (generate_password_hash('alice123'),))
db.commit(); db.close(); print("Done!")
```

### Step 7 — Run the application
```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 🔑 Demo Accounts

| Role    | Email               | Password  |
|---------|---------------------|-----------|
| Admin   | admin@elearn.com    | admin123  |
| Student | alice@elearn.com    | alice123  |

---

## 🌐 Pages & Routes

| URL                     | Description                    |
|-------------------------|-------------------------------|
| `/`                     | Home / landing page            |
| `/register`             | Student registration           |
| `/login`                | Login page                     |
| `/logout`               | Logout                         |
| `/dashboard`            | Student dashboard              |
| `/courses`              | Browse all courses             |
| `/course/<id>`          | Course detail + enroll         |
| `/module/<id>`          | Module content reader          |
| `/quiz/<test_id>`       | Take quiz                      |
| `/results`              | My result history              |
| `/admin`                | Admin overview                 |
| `/admin/categories`     | CRUD categories                |
| `/admin/courses`        | CRUD courses                   |
| `/admin/modules`        | CRUD modules                   |
| `/admin/questions`      | CRUD questions + solutions     |
| `/admin/users`          | View all users                 |

---

## 🗄️ Database Entities

| Table         | PK           | Description                    |
|---------------|-------------|-------------------------------|
| user          | user_id      | Students and admins            |
| category      | category_id  | Course categories              |
| course        | course_id    | Courses with FK to category    |
| enrollment    | enroll_id    | User ↔ Course enrollment       |
| module        | module_id    | Modules with FK to course      |
| orders        | order_id     | Purchase records               |
| questions     | question_id  | MCQ questions per module       |
| solution      | solution_id  | Correct answer + explanation   |
| test          | test_id      | Test config per module         |
| result        | result_id    | User quiz scores               |
| attempt       | attempt_id   | Individual answer attempts     |

---

## 🔧 Troubleshooting

**"Access denied for user root"** → Check your MySQL password in `app.py`

**"Unknown database elearning"** → Run `schema.sql` first in MySQL

**Port 5000 in use** → Change `port=5000` to `port=5001` in `app.py`

**Module not found** → Activate your virtual environment and run `pip install -r requirements.txt`

---

## 📝 Notes

- Passwords are hashed with **Werkzeug PBKDF2-SHA256** (industry standard)
- Admin users have `role_id = 1`, students have `role_id = 2`
- Each module automatically gets a test when created via the admin panel
- The quiz timer is client-side only (cosmetic) — no server-side time limit
