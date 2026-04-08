from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')

    columns = [col[1] for col in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "score" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN score INTEGER DEFAULT 0")

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('intro'))   # 🔥 changed
    return redirect(url_for('login'))

# 🔥 NEW
@app.route('/intro')
def intro():
    return render_template('intro.html')

# 🔥 NEW
@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            error = "Please fill all fields"
            return render_template('signup.html', error=error)

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            error = "User already exists!"
            return render_template('signup.html', error=error)

    return render_template('signup.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            error = "Please fill all fields"
            return render_template('login.html', error=error)

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['user'] = username
            session['user_id'] = user['id']
            return redirect(url_for('intro'))   # 🔥 changed
        else:
            error = "Invalid username or password"

    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session['user_id'],)
    ).fetchone()
    conn.close()

    score = user['score'] if user and 'score' in user.keys() else 0

    return render_template('day1.html', user=session['user'], score=score)

@app.route('/update_score', methods=['POST'])
def update_score():
    if 'user_id' not in session:
        return "Not logged in", 401

    score = request.form.get('score')

    conn = get_db()
    conn.execute(
        "UPDATE users SET score=? WHERE id=?",
        (score, session['user_id'])
    )
    conn.commit()
    conn.close()

    return "Score updated"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
