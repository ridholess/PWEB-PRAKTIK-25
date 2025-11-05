import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.config["MYSQL_HOST"] = "localhost"
app.config['MYSQL_PORT'] = 3306
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] =  ""
app.config["MYSQL_DB"] = "db_course"
mysql = MySQL(app)

@app.route('/')
def index():
    if 'is_logged_in' not in session:
        return redirect(url_for('login'))
    user_id = session.get('user_id')
    cur = mysql.connection.cursor()
    if request.args.get('order') == 'asc':
        cur.execute("SELECT * FROM courses WHERE user_id=%s ORDER BY created_at ASC",
                    (user_id,))
    else:
        cur.execute("SELECT * FROM courses WHERE user_id=%s ORDER BY created_at DESC",
                    (user_id,))
    courses = cur.fetchall()
    cur.close()
    return render_template('index.html', courses=courses)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conf_password = request.form['conf_password']
        if password != conf_password:
            flash('Kata sandi tidak sama')
            return redirect(url_for('register'))
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        if user:
            flash('Email sudah digunakan')
            return render_template('register.html')
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(email, password) VALUES(%s, %s)",
                    (email, generate_password_hash(password)))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        if user:
            if check_password_hash(user[2], password):
                session['is_logged_in'] = True
                session['user_id'] = user[0]
                print(f"DEBUG LOGIN: user_id set to {user[0]}")  # Debug
                return redirect(url_for('index'))
            flash("Kata sandi salah")
            return redirect(url_for('login'))
        flash("Email tidak terdaftar")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
def add_course():
    if 'is_logged_in' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title_course = request.form['title_course']
        creator = request.form['creator']
        user_id = session.get('user_id')
        print(f"DEBUG ADD_COURSE: user_id from session = {user_id}")  # Debug
        cur = mysql.connection.cursor()
        # store the owning user_id so we can list per-user courses
        cur.execute("INSERT INTO courses(title_course, creator, user_id) VALUES(%s, %s, %s)", 
                    (title_course, creator, user_id))
        mysql.connection.commit()
        cur.close()
        print(f"DEBUG ADD_COURSE: Course added with user_id = {user_id}")  # Debug
        return redirect(url_for('index'))
    return render_template('add_course.html')

@app.route('/delete/<int:course_id>')
def delete_course(course_id):
    if 'is_logged_in' not in session:
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    # only delete if the logged-in user owns the course
    cur.execute("DELETE FROM course WHERE id = %s AND user_id = %s", (course_id, session.get('user_id')))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('index'))

@app.route("/edit/<int:course_id>", methods=["GET", "POST"])
def edit_course(course_id):
    if 'is_logged_in' not in session:
        return redirect(url_for('login'))
    if request.method == "POST":
        new_title_course = request.form.get("title_course")
        new_creator = request.form.get("creator")
        cur = mysql.connection.cursor()
        # only update if the logged-in user owns the course
        cur.execute("UPDATE courses SET title_course = %s, creator = %s WHERE id = %s AND user_id = %s", 
                    (new_title_course, new_creator, course_id, session.get('user_id')))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('index'))
    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM courses WHERE id = %s AND user_id = %s", (course_id, session.get('user_id')))
        courses = cur.fetchone()
        cur.close()
        # render only if the course exists and belongs to the user
        if courses:
            return render_template("edit.html",
                                    title_course=courses[1],
                                    creator=courses[2])

if __name__ == '__main__':
    app.run(debug=True)
