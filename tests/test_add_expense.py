"""
Tests for Step 07 — Add Expense feature.

Routes under test:
  GET  /expenses/add   — render blank form (auth required)
  POST /expenses/add   — validate and insert expense, redirect to /profile (auth required)
"""

import pytest
import database.db as db_module
from database.db import get_db, init_db
from app import app as flask_app
from werkzeug.security import generate_password_hash


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def patched_db(tmp_path, monkeypatch):
    """Point DB_PATH to a fresh temp file for every test."""
    db_path = str(tmp_path / "test_add_expense.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    init_db()
    return db_path


@pytest.fixture
def app(patched_db):
    """Flask test app wired to the temp DB; no seed data."""
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret",
        WTF_CSRF_ENABLED=False,
    )
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def registered_user(patched_db):
    """Insert a test user directly into the temp DB; return (email, password, user_id)."""
    email = "tester@pocketlog.com"
    password = "securepass1"
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Tester", email, generate_password_hash(password)),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return {"email": email, "password": password, "user_id": user_id}


@pytest.fixture
def auth_client(client, registered_user):
    """Test client with an active session for the registered test user."""
    client.post(
        "/login",
        data={"email": registered_user["email"], "password": registered_user["password"]},
        follow_redirects=False,
    )
    return client


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _count_expenses(user_id):
    """Return the number of expense rows for user_id in the temp DB."""
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM expenses WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return row["cnt"]


def _fetch_latest_expense(user_id):
    """Return the most recently inserted expense row for user_id."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    return row


VALID_POST = {
    "amount": "29.99",
    "category": "Food",
    "date": "2026-05-17",
    "description": "Test lunch",
}


# ---------------------------------------------------------------------------
# Auth guard tests
# ---------------------------------------------------------------------------

class TestAuthGuard:
    def test_get_add_expense_unauthenticated_redirects_to_login(self, client):
        response = client.get("/expenses/add", follow_redirects=False)
        assert response.status_code == 302, "Unauthenticated GET should redirect"
        assert "/login" in response.headers["Location"], (
            "Redirect target must be /login"
        )

    def test_post_add_expense_unauthenticated_redirects_to_login(self, client):
        response = client.post(
            "/expenses/add",
            data=VALID_POST,
            follow_redirects=False,
        )
        assert response.status_code == 302, "Unauthenticated POST should redirect"
        assert "/login" in response.headers["Location"], (
            "Redirect target must be /login"
        )

    def test_get_add_expense_unauthenticated_does_not_reach_form(self, client):
        response = client.get("/expenses/add", follow_redirects=True)
        assert b"Login" in response.data or b"login" in response.data, (
            "Following redirect should land on login page"
        )


# ---------------------------------------------------------------------------
# GET — form rendering
# ---------------------------------------------------------------------------

class TestGetAddExpenseForm:
    def test_get_returns_200(self, auth_client):
        response = auth_client.get("/expenses/add")
        assert response.status_code == 200, "Logged-in GET should return 200"

    def test_form_contains_amount_field(self, auth_client):
        response = auth_client.get("/expenses/add")
        assert b'name="amount"' in response.data, "Form must contain an amount input"

    def test_form_contains_category_select(self, auth_client):
        response = auth_client.get("/expenses/add")
        assert b'name="category"' in response.data, "Form must contain a category field"
        # A <select> element is expected
        assert b"<select" in response.data or b"select" in response.data.lower(), (
            "Category field should be a select element"
        )

    def test_form_contains_date_field(self, auth_client):
        response = auth_client.get("/expenses/add")
        assert b'name="date"' in response.data, "Form must contain a date input"

    def test_form_contains_description_field(self, auth_client):
        response = auth_client.get("/expenses/add")
        assert b'name="description"' in response.data, (
            "Form must contain a description field"
        )

    @pytest.mark.parametrize("category", [
        "Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"
    ])
    def test_form_renders_all_valid_categories(self, auth_client, category):
        response = auth_client.get("/expenses/add")
        assert category.encode() in response.data, (
            f"Category '{category}' must appear as an option in the form"
        )

    def test_form_extends_base_template(self, auth_client):
        """Verify the page uses the shared layout (base.html includes nav or standard chrome)."""
        response = auth_client.get("/expenses/add")
        # base.html renders a <body> tag at minimum
        assert b"<body" in response.data or b"<!DOCTYPE" in response.data, (
            "Page must extend base.html and render a full HTML document"
        )


# ---------------------------------------------------------------------------
# POST — happy path
# ---------------------------------------------------------------------------

class TestPostAddExpenseHappyPath:
    def test_valid_post_redirects_to_profile(self, auth_client):
        response = auth_client.post(
            "/expenses/add",
            data=VALID_POST,
            follow_redirects=False,
        )
        assert response.status_code == 302, "Valid POST should redirect"
        assert "/profile" in response.headers["Location"], (
            "Redirect must point to /profile"
        )

    def test_valid_post_inserts_row_in_db(self, auth_client, registered_user):
        before = _count_expenses(registered_user["user_id"])
        auth_client.post("/expenses/add", data=VALID_POST)
        after = _count_expenses(registered_user["user_id"])
        assert after == before + 1, "Exactly one new expense row should be inserted"

    def test_valid_post_stores_correct_amount(self, auth_client, registered_user):
        auth_client.post("/expenses/add", data=VALID_POST)
        row = _fetch_latest_expense(registered_user["user_id"])
        assert row is not None, "Expense row must exist in DB"
        assert abs(row["amount"] - 29.99) < 0.001, (
            f"Stored amount {row['amount']} does not match submitted 29.99"
        )

    def test_valid_post_stores_correct_category(self, auth_client, registered_user):
        auth_client.post("/expenses/add", data=VALID_POST)
        row = _fetch_latest_expense(registered_user["user_id"])
        assert row["category"] == "Food", (
            f"Stored category '{row['category']}' does not match submitted 'Food'"
        )

    def test_valid_post_stores_correct_date(self, auth_client, registered_user):
        auth_client.post("/expenses/add", data=VALID_POST)
        row = _fetch_latest_expense(registered_user["user_id"])
        assert row["date"] == "2026-05-17", (
            f"Stored date '{row['date']}' does not match submitted '2026-05-17'"
        )

    def test_valid_post_stores_correct_description(self, auth_client, registered_user):
        auth_client.post("/expenses/add", data=VALID_POST)
        row = _fetch_latest_expense(registered_user["user_id"])
        assert row["description"] == "Test lunch", (
            f"Stored description '{row['description']}' does not match submitted value"
        )

    def test_valid_post_stores_correct_user_id(self, auth_client, registered_user):
        auth_client.post("/expenses/add", data=VALID_POST)
        row = _fetch_latest_expense(registered_user["user_id"])
        assert row["user_id"] == registered_user["user_id"], (
            "Stored user_id must match the logged-in user"
        )

    def test_new_expense_appears_on_profile(self, auth_client):
        auth_client.post("/expenses/add", data=VALID_POST)
        response = auth_client.get("/profile", follow_redirects=True)
        assert b"Test lunch" in response.data or b"Food" in response.data, (
            "Submitted expense should appear in the profile transaction list"
        )

    def test_blank_description_stored_as_none(self, auth_client, registered_user):
        data = {**VALID_POST, "description": ""}
        auth_client.post("/expenses/add", data=data)
        row = _fetch_latest_expense(registered_user["user_id"])
        assert row["description"] is None, (
            "Blank description should be stored as NULL in the DB"
        )

    def test_whitespace_only_description_stored_as_none(self, auth_client, registered_user):
        data = {**VALID_POST, "description": "   "}
        auth_client.post("/expenses/add", data=data)
        row = _fetch_latest_expense(registered_user["user_id"])
        assert row["description"] is None, (
            "Whitespace-only description should be stored as NULL in the DB"
        )


# ---------------------------------------------------------------------------
# POST — validation errors
# ---------------------------------------------------------------------------

class TestPostAddExpenseValidation:

    @pytest.mark.parametrize("amount_val, label", [
        ("", "missing amount"),
        ("0", "zero amount"),
        ("-5.00", "negative amount"),
        ("0.00", "zero as float string"),
        ("abc", "non-numeric amount"),
        ("!@#", "special characters"),
    ])
    def test_invalid_amount_rerenders_form_not_redirect(
        self, auth_client, amount_val, label
    ):
        data = {**VALID_POST, "amount": amount_val}
        response = auth_client.post("/expenses/add", data=data, follow_redirects=False)
        assert response.status_code == 200, (
            f"[{label}] Invalid amount should re-render form (200), not redirect"
        )

    @pytest.mark.parametrize("amount_val, label", [
        ("", "missing amount"),
        ("0", "zero amount"),
        ("-5.00", "negative amount"),
        ("abc", "non-numeric amount"),
    ])
    def test_invalid_amount_shows_error_message(
        self, auth_client, amount_val, label
    ):
        data = {**VALID_POST, "amount": amount_val}
        response = auth_client.post("/expenses/add", data=data)
        data_lower = response.data.lower()
        assert b"amount" in data_lower or b"error" in data_lower or b"valid" in data_lower, (
            f"[{label}] Response must contain an error related to amount"
        )

    @pytest.mark.parametrize("amount_val, label", [
        ("", "missing amount"),
        ("0", "zero amount"),
        ("-5.00", "negative amount"),
        ("abc", "non-numeric amount"),
    ])
    def test_invalid_amount_does_not_insert_row(
        self, auth_client, registered_user, amount_val, label
    ):
        before = _count_expenses(registered_user["user_id"])
        data = {**VALID_POST, "amount": amount_val}
        auth_client.post("/expenses/add", data=data)
        after = _count_expenses(registered_user["user_id"])
        assert after == before, (
            f"[{label}] No DB row should be inserted when amount is invalid"
        )

    def test_missing_date_rerenders_form(self, auth_client):
        data = {**VALID_POST, "date": ""}
        response = auth_client.post("/expenses/add", data=data, follow_redirects=False)
        assert response.status_code == 200, (
            "Missing date should re-render the form (200)"
        )

    def test_missing_date_shows_error_message(self, auth_client):
        data = {**VALID_POST, "date": ""}
        response = auth_client.post("/expenses/add", data=data)
        data_lower = response.data.lower()
        assert b"date" in data_lower or b"error" in data_lower or b"required" in data_lower, (
            "Response must contain an error message about the missing date"
        )

    def test_missing_date_does_not_insert_row(self, auth_client, registered_user):
        before = _count_expenses(registered_user["user_id"])
        data = {**VALID_POST, "date": ""}
        auth_client.post("/expenses/add", data=data)
        after = _count_expenses(registered_user["user_id"])
        assert after == before, "No DB row should be inserted when date is missing"

    @pytest.mark.parametrize("bad_category, label", [
        ("", "empty category"),
        ("Groceries", "unlisted category"),
        ("food", "lowercase valid name"),
        ("FOOD", "uppercase valid name"),
        ("<script>", "injection attempt"),
        ("123", "numeric string"),
    ])
    def test_invalid_category_rerenders_form(self, auth_client, bad_category, label):
        data = {**VALID_POST, "category": bad_category}
        response = auth_client.post("/expenses/add", data=data, follow_redirects=False)
        assert response.status_code == 200, (
            f"[{label}] Invalid category should re-render form (200)"
        )

    @pytest.mark.parametrize("bad_category, label", [
        ("", "empty category"),
        ("Groceries", "unlisted category"),
        ("food", "lowercase valid name"),
    ])
    def test_invalid_category_shows_error_message(self, auth_client, bad_category, label):
        data = {**VALID_POST, "category": bad_category}
        response = auth_client.post("/expenses/add", data=data)
        data_lower = response.data.lower()
        assert b"category" in data_lower or b"error" in data_lower or b"valid" in data_lower, (
            f"[{label}] Response must contain an error related to category"
        )

    @pytest.mark.parametrize("bad_category, label", [
        ("", "empty category"),
        ("Groceries", "unlisted category"),
        ("food", "lowercase valid name"),
    ])
    def test_invalid_category_does_not_insert_row(
        self, auth_client, registered_user, bad_category, label
    ):
        before = _count_expenses(registered_user["user_id"])
        data = {**VALID_POST, "category": bad_category}
        auth_client.post("/expenses/add", data=data)
        after = _count_expenses(registered_user["user_id"])
        assert after == before, (
            f"[{label}] No DB row should be inserted when category is invalid"
        )


# ---------------------------------------------------------------------------
# Form re-population on validation error
# ---------------------------------------------------------------------------

class TestFormRepopulation:
    def test_amount_repopulated_on_category_error(self, auth_client):
        data = {**VALID_POST, "category": "InvalidCat", "amount": "42.50"}
        response = auth_client.post("/expenses/add", data=data)
        assert b"42.50" in response.data, (
            "Previously entered amount should be re-populated after a validation error"
        )

    def test_date_repopulated_on_amount_error(self, auth_client):
        data = {**VALID_POST, "amount": "0", "date": "2026-05-17"}
        response = auth_client.post("/expenses/add", data=data)
        assert b"2026-05-17" in response.data, (
            "Previously entered date should be re-populated after a validation error"
        )

    def test_description_repopulated_on_amount_error(self, auth_client):
        data = {**VALID_POST, "amount": "-1", "description": "My test note"}
        response = auth_client.post("/expenses/add", data=data)
        assert b"My test note" in response.data, (
            "Previously entered description should be re-populated after a validation error"
        )

    def test_category_repopulated_on_amount_error(self, auth_client):
        data = {**VALID_POST, "amount": "abc", "category": "Health"}
        response = auth_client.post("/expenses/add", data=data)
        assert b"Health" in response.data, (
            "Previously selected category should be re-populated after a validation error"
        )

    def test_amount_repopulated_on_missing_date(self, auth_client):
        data = {**VALID_POST, "date": "", "amount": "19.95"}
        response = auth_client.post("/expenses/add", data=data)
        assert b"19.95" in response.data, (
            "Entered amount should survive a missing-date validation error"
        )


# ---------------------------------------------------------------------------
# Edge cases and security
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_very_large_amount_accepted(self, auth_client, registered_user):
        """A very large but valid positive float should be accepted."""
        data = {**VALID_POST, "amount": "9999999.99"}
        response = auth_client.post("/expenses/add", data=data, follow_redirects=False)
        assert response.status_code == 302, (
            "A large valid amount should be accepted and redirect"
        )
        row = _fetch_latest_expense(registered_user["user_id"])
        assert row is not None and abs(row["amount"] - 9999999.99) < 0.01

    def test_sql_injection_in_description_is_stored_safely(
        self, auth_client, registered_user
    ):
        """SQL injection in description should be stored as literal text, not executed."""
        malicious = "'; DROP TABLE expenses; --"
        data = {**VALID_POST, "description": malicious}
        auth_client.post("/expenses/add", data=data)
        row = _fetch_latest_expense(registered_user["user_id"])
        assert row is not None, "Expense table must still exist after injection attempt"
        assert row["description"] == malicious, (
            "Injection string must be stored verbatim, not interpreted"
        )

    def test_xss_in_description_stored_safely(self, auth_client, registered_user):
        """Script tags in description are stored as text (template escaping handles display)."""
        xss = "<script>alert('xss')</script>"
        data = {**VALID_POST, "description": xss}
        response = auth_client.post("/expenses/add", data=data, follow_redirects=False)
        assert response.status_code == 302, (
            "XSS string in description should be accepted and stored"
        )
        row = _fetch_latest_expense(registered_user["user_id"])
        assert row is not None

    def test_each_valid_category_can_be_submitted(self, auth_client, registered_user):
        """Every category in the allowed list should successfully insert a row."""
        valid_categories = [
            "Food", "Transport", "Bills", "Health",
            "Entertainment", "Shopping", "Other",
        ]
        for category in valid_categories:
            data = {**VALID_POST, "category": category}
            response = auth_client.post(
                "/expenses/add", data=data, follow_redirects=False
            )
            assert response.status_code == 302, (
                f"Category '{category}' should be accepted and redirect to /profile"
            )

    def test_submitting_valid_expense_does_not_affect_other_users(
        self, auth_client, registered_user, patched_db
    ):
        """An expense inserted for the test user must not appear under a different user_id."""
        auth_client.post("/expenses/add", data=VALID_POST)
        conn = get_db()
        other_user_rows = conn.execute(
            "SELECT COUNT(*) as cnt FROM expenses WHERE user_id != ?",
            (registered_user["user_id"],),
        ).fetchone()
        conn.close()
        assert other_user_rows["cnt"] == 0, (
            "Expense must only be associated with the authenticated user"
        )

    def test_minimum_valid_amount(self, auth_client, registered_user):
        """The smallest positive float should be accepted."""
        data = {**VALID_POST, "amount": "0.01"}
        response = auth_client.post("/expenses/add", data=data, follow_redirects=False)
        assert response.status_code == 302, "0.01 is a valid positive amount"
        row = _fetch_latest_expense(registered_user["user_id"])
        assert row is not None and abs(row["amount"] - 0.01) < 0.001
