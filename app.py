"""
E-Learning Platform — Flask Backend
Run: python app.py
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'elearn_secret_2024_change_in_prod'

# ── DB Config ──────────────────────────────────────────────────
DB_CONFIG = {
    'host':     os.getenv('DB_HOST',     'localhost'),
    'user':     os.getenv('DB_USER',     'root'),
    'password': os.getenv('DB_PASSWORD', ''),          # ← change to your MySQL password
    'database': os.getenv('DB_NAME',     'elearning'),
    'autocommit': True,
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# ── Auth decorators ────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role_id') != 1:
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

# ═══════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ═══════════════════════════════════════════════════════════════
@app.route('/')
def home():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT c.*, cat.category_name FROM course c LEFT JOIN category cat ON c.category_id=cat.category_id LIMIT 6")
    courses = cur.fetchall()
    cur.execute("SELECT * FROM category")
    cats = cur.fetchall()
    cur.close(); db.close()
    return render_template('home.html', courses=courses, categories=cats)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email     = request.form['email']
        password  = generate_password_hash(request.form['password'])
        db = get_db(); cur = db.cursor()
        try:
            cur.execute("INSERT INTO user (full_name,email,password,role_id) VALUES (%s,%s,%s,2)",
                        (full_name, email, password))
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Email already registered.', 'danger')
        finally:
            cur.close(); db.close()
    return render_template('auth/register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM user WHERE email=%s", (email,))
        user = cur.fetchone(); cur.close(); db.close()
        if user and check_password_hash(user['password'], password):
            session.update({'user_id': user['user_id'], 'full_name': user['full_name'],
                            'email': user['email'], 'role_id': user['role_id']})
            flash(f"Welcome back, {user['full_name']}!", 'success')
            return redirect(url_for('admin_dashboard') if user['role_id'] == 1 else url_for('dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

# ═══════════════════════════════════════════════════════════════
#  STUDENT ROUTES
# ═══════════════════════════════════════════════════════════════
@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db(); cur = db.cursor(dictionary=True)
    uid = session['user_id']
    cur.execute("""
        SELECT e.*, c.course_name, c.description, cat.category_name
        FROM enrollment e
        JOIN course c ON e.course_id=c.course_id
        LEFT JOIN category cat ON c.category_id=cat.category_id
        WHERE e.user_id=%s""", (uid,))
    enrollments = cur.fetchall()
    cur.execute("""
        SELECT r.*, t.total_marks, m.module_title
        FROM result r JOIN test t ON r.test_id=t.test_id
        JOIN module m ON t.module_id=m.module_id
        WHERE r.user_id=%s ORDER BY r.taken_at DESC LIMIT 5""", (uid,))
    results = cur.fetchall()
    cur.close(); db.close()
    return render_template('student/dashboard.html', enrollments=enrollments, results=results)

@app.route('/courses')
def courses():
    cat_filter = request.args.get('cat','')
    db = get_db(); cur = db.cursor(dictionary=True)
    if cat_filter:
        cur.execute("""SELECT c.*, cat.category_name FROM course c
                       LEFT JOIN category cat ON c.category_id=cat.category_id
                       WHERE c.category_id=%s""", (cat_filter,))
    else:
        cur.execute("""SELECT c.*, cat.category_name FROM course c
                       LEFT JOIN category cat ON c.category_id=cat.category_id""")
    courses = cur.fetchall()
    cur.execute("SELECT * FROM category")
    cats = cur.fetchall()
    cur.close(); db.close()
    return render_template('student/courses.html', courses=courses, categories=cats, selected=cat_filter)

@app.route('/course/<int:cid>')
def course_detail(cid):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""SELECT c.*, cat.category_name FROM course c
                   LEFT JOIN category cat ON c.category_id=cat.category_id
                   WHERE c.course_id=%s""", (cid,))
    course = cur.fetchone()
    if not course:
        flash('Course not found.', 'danger'); return redirect(url_for('courses'))
    cur.execute("SELECT * FROM module WHERE course_id=%s ORDER BY order_no", (cid,))
    modules = cur.fetchall()
    enrolled = False
    if 'user_id' in session:
        cur.execute("SELECT 1 FROM enrollment WHERE user_id=%s AND course_id=%s",
                    (session['user_id'], cid))
        enrolled = cur.fetchone() is not None
    cur.close(); db.close()
    return render_template('student/course_detail.html', course=course, modules=modules, enrolled=enrolled)

@app.route('/enroll/<int:cid>', methods=['POST'])
@login_required
def enroll(cid):
    db = get_db(); cur = db.cursor()
    try:
        cur.execute("INSERT INTO enrollment (user_id,course_id,status) VALUES (%s,%s,'active')",
                    (session['user_id'], cid))
        flash('Enrolled successfully!', 'success')
    except mysql.connector.IntegrityError:
        flash('Already enrolled.', 'info')
    finally:
        cur.close(); db.close()
    return redirect(url_for('course_detail', cid=cid))

@app.route('/module/<int:mid>')
@login_required
def module_page(mid):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT m.*, c.course_name FROM module m JOIN course c ON m.course_id=c.course_id WHERE m.module_id=%s", (mid,))
    mod = cur.fetchone()
    if not mod:
        flash('Module not found.', 'danger'); return redirect(url_for('dashboard'))
    cur.execute("SELECT * FROM test WHERE module_id=%s", (mid,))
    test = cur.fetchone()
    cur.execute("SELECT * FROM module WHERE course_id=%s ORDER BY order_no", (mod['course_id'],))
    all_mods = cur.fetchall()
    cur.close(); db.close()
    return render_template('student/module.html', mod=mod, test=test, all_mods=all_mods)

@app.route('/quiz/<int:test_id>')
@login_required
def quiz(test_id):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM test WHERE test_id=%s", (test_id,))
    test = cur.fetchone()
    if not test:
        flash('Test not found.', 'danger'); return redirect(url_for('dashboard'))
    cur.execute("SELECT * FROM questions WHERE module_id=%s", (test['module_id'],))
    questions = cur.fetchall()
    cur.close(); db.close()
    return render_template('student/quiz.html', test=test, questions=questions)

@app.route('/submit_quiz/<int:test_id>', methods=['POST'])
@login_required
def submit_quiz(test_id):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM test WHERE test_id=%s", (test_id,))
    test = cur.fetchone()
    cur.execute("SELECT q.*, s.correct_option, s.explanation FROM questions q LEFT JOIN solution s ON q.question_id=s.question_id WHERE q.module_id=%s", (test['module_id'],))
    questions = cur.fetchall()

    score = 0; detailed = []
    for q in questions:
        selected = request.form.get(f"q_{q['question_id']}", '')
        correct  = q['correct_option'] or ''
        is_correct = (selected.upper() == correct.upper())
        if is_correct: score += 1
        # store attempt
        cur2 = db.cursor()
        cur2.execute("INSERT INTO attempt (user_id,question_id,selected_option,is_correct) VALUES (%s,%s,%s,%s)",
                     (session['user_id'], q['question_id'], selected, int(is_correct)))
        cur2.close()
        detailed.append({'question': q, 'selected': selected, 'correct': correct,
                         'is_correct': is_correct, 'explanation': q.get('explanation','')})

    total  = len(questions)
    marks  = round((score / total) * test['total_marks']) if total else 0
    passed = marks >= test['passing_marks']
    judgment = 'Pass' if passed else 'Fail'

    cur3 = db.cursor()
    cur3.execute("INSERT INTO result (user_id,test_id,score,judgment) VALUES (%s,%s,%s,%s)",
                 (session['user_id'], test_id, marks, judgment))
    cur3.close()
    cur.close(); db.close()
    return render_template('student/result.html', test=test, score=marks,
                           total=test['total_marks'], judgment=judgment,
                           passed=passed, detailed=detailed)

@app.route('/results')
@login_required
def my_results():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""SELECT r.*, t.total_marks, t.passing_marks, m.module_title, c.course_name
                   FROM result r JOIN test t ON r.test_id=t.test_id
                   JOIN module m ON t.module_id=m.module_id
                   JOIN course c ON m.course_id=c.course_id
                   WHERE r.user_id=%s ORDER BY r.taken_at DESC""", (session['user_id'],))
    results = cur.fetchall()
    cur.close(); db.close()
    return render_template('student/results.html', results=results)

# ═══════════════════════════════════════════════════════════════
#  ADMIN ROUTES
# ═══════════════════════════════════════════════════════════════
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS cnt FROM user WHERE role_id=2"); students = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM course");               total_courses = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM enrollment");           enrollments = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM result");               attempts = cur.fetchone()['cnt']
    cur.close(); db.close()
    return render_template('admin/dashboard.html',
                           students=students, total_courses=total_courses,
                           enrollments=enrollments, attempts=attempts)

# ── Admin: Categories ──────────────────────────────────────────
@app.route('/admin/categories')
@login_required
@admin_required
def admin_categories():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM category")
    cats = cur.fetchall(); cur.close(); db.close()
    return render_template('admin/categories.html', categories=cats)

@app.route('/admin/categories/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO category (category_name) VALUES (%s)", (request.form['category_name'],))
    cur.close(); db.close()
    flash('Category added.', 'success')
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/delete/<int:cid>')
@login_required
@admin_required
def delete_category(cid):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM category WHERE category_id=%s", (cid,))
    cur.close(); db.close()
    flash('Category deleted.', 'info')
    return redirect(url_for('admin_categories'))

# ── Admin: Courses ─────────────────────────────────────────────
@app.route('/admin/courses')
@login_required
@admin_required
def admin_courses():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""SELECT c.*, cat.category_name FROM course c
                   LEFT JOIN category cat ON c.category_id=cat.category_id""")
    courses = cur.fetchall()
    cur.execute("SELECT * FROM category"); cats = cur.fetchall()
    cur.close(); db.close()
    return render_template('admin/courses.html', courses=courses, categories=cats)

@app.route('/admin/courses/add', methods=['POST'])
@login_required
@admin_required
def add_course():
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO course (course_name,description,category_id) VALUES (%s,%s,%s)",
                (request.form['course_name'], request.form['description'], request.form['category_id']))
    cur.close(); db.close()
    flash('Course added.', 'success')
    return redirect(url_for('admin_courses'))

@app.route('/admin/courses/delete/<int:cid>')
@login_required
@admin_required
def delete_course(cid):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM course WHERE course_id=%s", (cid,))
    cur.close(); db.close()
    flash('Course deleted.', 'info')
    return redirect(url_for('admin_courses'))

# ── Admin: Modules ─────────────────────────────────────────────
@app.route('/admin/modules')
@login_required
@admin_required
def admin_modules():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""SELECT m.*, c.course_name FROM module m JOIN course c ON m.course_id=c.course_id ORDER BY c.course_name, m.order_no""")
    modules = cur.fetchall()
    cur.execute("SELECT * FROM course"); courses = cur.fetchall()
    cur.close(); db.close()
    return render_template('admin/modules.html', modules=modules, courses=courses)

@app.route('/admin/modules/add', methods=['POST'])
@login_required
@admin_required
def add_module():
    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO module (course_id,module_title,content,order_no) VALUES (%s,%s,%s,%s)",
                (request.form['course_id'], request.form['module_title'],
                 request.form['content'], request.form['order_no']))
    mid = cur.lastrowid
    cur.execute("INSERT INTO test (module_id,total_marks,passing_marks) VALUES (%s,%s,%s)",
                (mid, request.form.get('total_marks',10), request.form.get('passing_marks',6)))
    cur.close(); db.close()
    flash('Module + Test created.', 'success')
    return redirect(url_for('admin_modules'))

@app.route('/admin/modules/delete/<int:mid>')
@login_required
@admin_required
def delete_module(mid):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM module WHERE module_id=%s", (mid,))
    cur.close(); db.close()
    flash('Module deleted.', 'info')
    return redirect(url_for('admin_modules'))

# ── Admin: Questions ───────────────────────────────────────────
@app.route('/admin/questions')
@login_required
@admin_required
def admin_questions():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""SELECT q.*, m.module_title, s.correct_option, s.explanation
                   FROM questions q JOIN module m ON q.module_id=m.module_id
                   LEFT JOIN solution s ON q.question_id=s.question_id""")
    questions = cur.fetchall()
    cur.execute("SELECT * FROM module"); modules = cur.fetchall()
    cur.close(); db.close()
    return render_template('admin/questions.html', questions=questions, modules=modules)

@app.route('/admin/questions/add', methods=['POST'])
@login_required
@admin_required
def add_question():
    db = get_db(); cur = db.cursor()
    f = request.form
    cur.execute("""INSERT INTO questions (module_id,question_text,option_a,option_b,option_c,option_d)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (f['module_id'], f['question_text'], f['option_a'], f['option_b'], f['option_c'], f['option_d']))
    qid = cur.lastrowid
    cur.execute("INSERT INTO solution (question_id,correct_option,solution_text,explanation) VALUES (%s,%s,%s,%s)",
                (qid, f['correct_option'], f['solution_text'], f['explanation']))
    cur.close(); db.close()
    flash('Question + Solution added.', 'success')
    return redirect(url_for('admin_questions'))

@app.route('/admin/questions/delete/<int:qid>')
@login_required
@admin_required
def delete_question(qid):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM questions WHERE question_id=%s", (qid,))
    cur.close(); db.close()
    flash('Question deleted.', 'info')
    return redirect(url_for('admin_questions'))

# ── Admin: Users ───────────────────────────────────────────────
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT user_id, full_name, email, role_id FROM user ORDER BY role_id, full_name")
    users = cur.fetchall(); cur.close(); db.close()
    return render_template('admin/users.html', users=users)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
    
