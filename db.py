import sqlite3
import pandas as pd
import hashlib

DB_NAME = "tasks_v2.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Create Tasks Table with user_id
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            due_date TEXT,
            item_type TEXT DEFAULT 'Task',
            item_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed_pw = hash_password(password)
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed_pw = hash_password(password)
    c.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, hashed_pw))
    user = c.fetchone()
    conn.close()
    return user[0] if user else None

def add_task(user_id, task, category, due_date, item_type="Task", item_time=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO tasks (user_id, task, category, due_date, item_type, item_time) VALUES (?, ?, ?, ?, ?, ?)', 
              (user_id, task, category, due_date, item_type, str(item_time)))
    conn.commit()
    conn.close()

def get_tasks(user_id):
    conn = sqlite3.connect(DB_NAME)
    # Filter by user_id
    df = pd.read_sql_query("SELECT * FROM tasks WHERE user_id = ?", conn, params=(user_id,))
    conn.close()
    return df

def update_task_status(task_id, status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
