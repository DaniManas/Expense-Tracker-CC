import pytest
from database.db import get_db, init_db, get_expenses
from werkzeug.security import generate_password_hash
import database.db as db_module


@pytest.fixture
def user_id(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    init_db()
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User", "test@test.com", generate_password_hash("password")),
    )
    conn.commit()
    uid = conn.execute("SELECT id FROM users WHERE email = 'test@test.com'").fetchone()["id"]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [
            (uid, 10.00, "Food",      "2026-04-01", "Lunch"),
            (uid, 20.00, "Transport", "2026-04-15", "Bus"),
            (uid, 30.00, "Bills",     "2026-05-01", "Electric"),
        ],
    )
    conn.commit()
    conn.close()
    return uid


def test_get_expenses_no_filter_returns_all(user_id):
    rows = get_expenses(user_id)
    assert len(rows) == 3


def test_get_expenses_start_date_filter(user_id):
    rows = get_expenses(user_id, start_date="2026-04-15")
    assert len(rows) == 2
    assert all(r["date"] >= "2026-04-15" for r in rows)


def test_get_expenses_end_date_filter(user_id):
    rows = get_expenses(user_id, end_date="2026-04-15")
    assert len(rows) == 2
    assert all(r["date"] <= "2026-04-15" for r in rows)


def test_get_expenses_date_range_filter(user_id):
    rows = get_expenses(user_id, start_date="2026-04-15", end_date="2026-04-15")
    assert len(rows) == 1
    assert rows[0]["date"] == "2026-04-15"


def test_get_expenses_ordered_desc(user_id):
    rows = get_expenses(user_id)
    dates = [r["date"] for r in rows]
    assert dates == sorted(dates, reverse=True)


def test_get_expenses_empty_string_dates_ignored(user_id):
    rows = get_expenses(user_id, start_date="", end_date="")
    assert len(rows) == 3


from database.db import get_expense_stats


def test_get_expense_stats_no_filter(user_id):
    stats = get_expense_stats(user_id)
    assert stats["total_spent"] == pytest.approx(60.00)
    assert stats["transaction_count"] == 3
    assert stats["top_category"] == "Bills"


def test_get_expense_stats_with_date_range(user_id):
    stats = get_expense_stats(user_id, start_date="2026-04-01", end_date="2026-04-30")
    assert stats["total_spent"] == pytest.approx(30.00)
    assert stats["transaction_count"] == 2
    assert stats["top_category"] == "Transport"


def test_get_expense_stats_no_rows_returns_defaults(user_id):
    stats = get_expense_stats(user_id, start_date="2099-01-01")
    assert stats["total_spent"] == 0
    assert stats["transaction_count"] == 0
    assert stats["top_category"] == "—"
