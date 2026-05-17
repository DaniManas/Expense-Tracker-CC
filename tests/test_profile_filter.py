import pytest
import database.db as db_module
from app import app
from database.db import get_db, init_db
from werkzeug.security import generate_password_hash


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    init_db()

    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User", "test@test.com", generate_password_hash("password123")),
    )
    conn.commit()
    user_id = conn.execute("SELECT id FROM users WHERE email = 'test@test.com'").fetchone()["id"]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, 10.00, "Food",      "2026-04-01", "Lunch"),
            (user_id, 20.00, "Transport", "2026-04-15", "Bus"),
            (user_id, 30.00, "Bills",     "2026-05-01", "Electric"),
        ],
    )
    conn.commit()
    conn.close()

    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["user_id"] = user_id
        yield c


def test_profile_no_filter_shows_all_transactions(client):
    res = client.get("/profile")
    assert res.status_code == 200
    assert b"Lunch" in res.data
    assert b"Bus" in res.data
    assert b"Electric" in res.data


def test_profile_filter_by_start_date(client):
    res = client.get("/profile?start_date=2026-04-15")
    assert res.status_code == 200
    assert b"Bus" in res.data
    assert b"Electric" in res.data
    assert b"Lunch" not in res.data


def test_profile_filter_by_end_date(client):
    res = client.get("/profile?end_date=2026-04-15")
    assert res.status_code == 200
    assert b"Lunch" in res.data
    assert b"Bus" in res.data
    assert b"Electric" not in res.data


def test_profile_filter_by_date_range(client):
    res = client.get("/profile?start_date=2026-04-15&end_date=2026-04-15")
    assert res.status_code == 200
    assert b"Bus" in res.data
    assert b"Lunch" not in res.data
    assert b"Electric" not in res.data


def test_profile_no_results_no_error(client):
    res = client.get("/profile?start_date=2099-01-01")
    assert res.status_code == 200
    assert b"$0.00" in res.data
