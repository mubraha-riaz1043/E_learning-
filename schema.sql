-- ============================================================
--  E-Learning Platform — MySQL Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS elearning;
USE elearning;

-- 1. Category
CREATE TABLE IF NOT EXISTS category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL
);

-- 2. User
CREATE TABLE IF NOT EXISTS user (
    user_id     INT AUTO_INCREMENT PRIMARY KEY,
    full_name   VARCHAR(150) NOT NULL,
    email       VARCHAR(150) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    role_id     INT NOT NULL DEFAULT 2   -- 1=admin, 2=student
);

-- 3. Course
CREATE TABLE IF NOT EXISTS course (
    course_id   INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id INT,
    FOREIGN KEY (category_id) REFERENCES category(category_id) ON DELETE SET NULL
);

-- 4. Enrollment
CREATE TABLE IF NOT EXISTS enrollment (
    enroll_id   INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    course_id   INT NOT NULL,
    status      VARCHAR(50) DEFAULT 'active',
    enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES user(user_id)   ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES course(course_id) ON DELETE CASCADE,
    UNIQUE KEY uq_enroll (user_id, course_id)
);

-- 5. Module
CREATE TABLE IF NOT EXISTS module (
    module_id    INT AUTO_INCREMENT PRIMARY KEY,
    course_id    INT NOT NULL,
    module_title VARCHAR(200) NOT NULL,
    content      TEXT,
    order_no     INT DEFAULT 1,
    FOREIGN KEY (course_id) REFERENCES course(course_id) ON DELETE CASCADE
);

-- 6. Orders
CREATE TABLE IF NOT EXISTS orders (
    order_id   INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    module_id  INT NOT NULL,
    price      DECIMAL(10,2) DEFAULT 0.00,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES user(user_id)   ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES module(module_id) ON DELETE CASCADE
);

-- 7. Questions
CREATE TABLE IF NOT EXISTS questions (
    question_id   INT AUTO_INCREMENT PRIMARY KEY,
    module_id     INT NOT NULL,
    question_text TEXT NOT NULL,
    option_a      VARCHAR(255),
    option_b      VARCHAR(255),
    option_c      VARCHAR(255),
    option_d      VARCHAR(255),
    FOREIGN KEY (module_id) REFERENCES module(module_id) ON DELETE CASCADE
);

-- 8. Solution
CREATE TABLE IF NOT EXISTS solution (
    solution_id    INT AUTO_INCREMENT PRIMARY KEY,
    question_id    INT NOT NULL UNIQUE,
    correct_option CHAR(1) NOT NULL,   -- 'A','B','C','D'
    solution_text  TEXT,
    explanation    TEXT,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);

-- 9. Test
CREATE TABLE IF NOT EXISTS test (
    test_id       INT AUTO_INCREMENT PRIMARY KEY,
    module_id     INT NOT NULL,
    total_marks   INT DEFAULT 0,
    passing_marks INT DEFAULT 0,
    FOREIGN KEY (module_id) REFERENCES module(module_id) ON DELETE CASCADE
);

-- 10. Result
CREATE TABLE IF NOT EXISTS result (
    result_id  INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    test_id    INT NOT NULL,
    score      INT DEFAULT 0,
    judgment   ENUM('Pass','Fail') DEFAULT 'Fail',
    taken_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)  REFERENCES user(user_id)  ON DELETE CASCADE,
    FOREIGN KEY (test_id)  REFERENCES test(test_id)  ON DELETE CASCADE
);

-- 11. Attempt
CREATE TABLE IF NOT EXISTS attempt (
    attempt_id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    question_id     INT NOT NULL,
    selected_option CHAR(1),
    is_correct      TINYINT(1) DEFAULT 0,
    attempted_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)     REFERENCES user(user_id)      ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(question_id) ON DELETE CASCADE
);

-- ============================================================
--  Seed Data
-- ============================================================
INSERT INTO category (category_name) VALUES
    ('Programming'),('Data Science'),('Design'),('Business'),('Marketing');

INSERT INTO user (full_name, email, password, role_id) VALUES
    ('Admin User', 'admin@elearn.com',
     'pbkdf2:sha256:260000$placeholder$adminpasswordhash', 1),
    ('Alice Student', 'alice@elearn.com',
     'pbkdf2:sha256:260000$placeholder$studentpasswordhash', 2);

INSERT INTO course (course_name, description, category_id) VALUES
    ('Python for Beginners',      'Learn Python from scratch.',              1),
    ('Web Development Bootcamp',  'HTML, CSS, JS and more.',                1),
    ('Data Science Fundamentals', 'Intro to data analysis and ML.',         2),
    ('UI/UX Design Principles',   'Design beautiful user interfaces.',      3),
    ('Digital Marketing 101',     'Grow your brand online.',                5);

INSERT INTO module (course_id, module_title, content, order_no) VALUES
    (1,'Introduction to Python',   'Python basics: variables, data types, operators.', 1),
    (1,'Control Flow',             'if/else, loops, and functions in Python.',         2),
    (2,'HTML Fundamentals',        'Tags, attributes, and document structure.',        1),
    (2,'CSS Styling',              'Selectors, box model, flexbox.',                   2),
    (3,'Data Analysis with Pandas','DataFrames, series, and data cleaning.',           1);

INSERT INTO test (module_id, total_marks, passing_marks) VALUES
    (1, 10, 6),(2, 10, 6),(3, 10, 6),(4, 10, 6),(5, 10, 6);

INSERT INTO questions (module_id, question_text, option_a, option_b, option_c, option_d) VALUES
    (1,'What is the output of print(2 + 3)?','4','5','23','Error'),
    (1,'Which keyword is used to define a function in Python?','func','def','define','function'),
    (1,'What data type is [1, 2, 3]?','Tuple','Dictionary','List','Set'),
    (2,'Which loop runs at least once?','for','while','do-while','loop'),
    (2,'What does "break" do in a loop?','Skips iteration','Exits loop','Continues','None');

INSERT INTO solution (question_id, correct_option, solution_text, explanation) VALUES
    (1,'B','5','2 + 3 equals 5 in Python.'),
    (2,'B','def','Python uses the def keyword to define functions.'),
    (3,'C','List','Square brackets denote a list in Python.'),
    (4,'C','do-while','A do-while loop executes body before checking condition.'),
    (5,'B','Exits loop','break terminates the nearest enclosing loop.');

INSERT INTO attempt (user_id, question_id, selected_option, is_correct) VALUES
    (2, 1, 'B', 1),(2, 2, 'A', 0),(2, 3, 'C', 1);

INSERT INTO result (user_id, test_id, score, judgment) VALUES (2, 1, 6, 'Pass');

INSERT INTO enrollment (user_id, course_id, status) VALUES (2, 1, 'active'),(2, 2, 'active');
