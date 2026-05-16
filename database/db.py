import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'spendly.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute(
        "SELECT id, name, email, password_hash, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return user


def get_user_by_email(email):
    conn = get_db()
    user = conn.execute(
        "SELECT id, name, email, password_hash FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    conn.close()
    return user


def update_user(user_id, name, password_hash=None):
    conn = get_db()
    if password_hash:
        conn.execute(
            "UPDATE users SET name = ?, password_hash = ? WHERE id = ?",
            (name, password_hash, user_id),
        )
    else:
        conn.execute(
            "UPDATE users SET name = ? WHERE id = ?",
            (name, user_id),
        )
    conn.commit()
    conn.close()


def create_user(name, email, password):
    password_hash = generate_password_hash(password)
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def get_expenses(user_id, start_date=None, end_date=None):
    conn = get_db()
    query = "SELECT id, amount, category, date, description FROM expenses WHERE user_id = ?"
    params = [user_id]
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += " ORDER BY date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def get_expense_stats(user_id, start_date=None, end_date=None):
    conn = get_db()

    base_where = " WHERE user_id = ?"
    params = [user_id]
    if start_date:
        base_where += " AND date >= ?"
        params.append(start_date)
    if end_date:
        base_where += " AND date <= ?"
        params.append(end_date)

    summary = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as total_spent, COUNT(*) as transaction_count FROM expenses" + base_where,
        params,
    ).fetchone()

    total_spent = summary["total_spent"]
    transaction_count = summary["transaction_count"]

    top_category = "—"
    if transaction_count > 0:
        cat_row = conn.execute(
            "SELECT category, SUM(amount) as cat_total FROM expenses" + base_where + " GROUP BY category ORDER BY cat_total DESC LIMIT 1",
            params,
        ).fetchone()
        if cat_row:
            top_category = cat_row["category"]

    conn.close()
    return {
        "total_spent": total_spent,
        "transaction_count": transaction_count,
        "top_category": top_category,
    }


def seed_db():
    conn = get_db()

    row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    if row[0] > 0:
        conn.close()
        return

    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    user_id = cursor.lastrowid

    sample_expenses = [
        (user_id, 12.50,  "Food",          "2026-04-01", "Lunch at cafe"),
        (user_id, 45.00,  "Transport",     "2026-04-02", "Monthly bus pass"),
        (user_id, 120.00, "Bills",         "2026-04-03", "Electricity bill"),
        (user_id, 30.00,  "Health",        "2026-04-05", "Pharmacy"),
        (user_id, 25.00,  "Entertainment", "2026-04-07", "Cinema tickets"),
        (user_id, 65.00,  "Shopping",      "2026-04-09", "Clothing"),
        (user_id, 8.75,   "Other",         "2026-04-10", "Miscellaneous"),
        (user_id, 18.20,  "Food",          "2026-04-10", "Groceries"),
    ]

    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        sample_expenses,
    )
    conn.commit()
    conn.close()
