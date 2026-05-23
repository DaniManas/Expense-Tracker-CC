# Date Filter for Profile Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace hardcoded stub data on the profile page with real DB queries and add a date range filter that updates stats, transactions, and category breakdown.

**Architecture:** Two new DB helpers (`get_expenses`, `get_expense_stats`) in `database/db.py` handle all SQL. The `GET /profile` route reads optional `start_date`/`end_date` query params and passes real data to the template. The template adds a `method="GET"` filter form above the transaction list.

**Tech Stack:** Flask, SQLite (via `sqlite3`), Jinja2, vanilla HTML date inputs — no new packages.

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `database/db.py` | Modify | Add `get_expenses()` and `get_expense_stats()` |
| `app.py` | Modify | Replace stub data in `GET /profile` with real DB calls; read query params |
| `templates/profile.html` | Modify | Add date filter bar; wire transactions/stats/categories to dynamic data |
| `tests/test_db_expenses.py` | Create | Unit tests for `get_expenses` and `get_expense_stats` |
| `tests/test_profile_filter.py` | Create | Integration tests for filtered `GET /profile` route |

---

## Task 1: DB helper — `get_expenses()`

**Files:**
- Modify: `database/db.py`
- Create: `tests/test_db_expenses.py`

- [ ] **Step 1: Create test file with failing test for `get_expenses`**

```python
# tests/test_db_expenses.py
import pytest
import sqlite3
from database.db import get_db, init_db, get_expenses
from werkzeug.security import generate_password_hash


@pytest.fixture
def db_conn(tmp_path, monkeypatch):
    """Isolated in-memory-style DB using a temp file."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("database.db.DB_PATH", db_path)
    init_db()
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User", "test@test.com", generate_password_hash("password")),
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
    return user_id


def test_get_expenses_no_filter_returns_all(db_conn):
    rows = get_expenses(db_conn)
    assert len(rows) == 3


def test_get_expenses_start_date_filter(db_conn):
    rows = get_expenses(db_conn, start_date="2026-04-15")
    assert len(rows) == 2
    assert all(r["date"] >= "2026-04-15" for r in rows)


def test_get_expenses_end_date_filter(db_conn):
    rows = get_expenses(db_conn, end_date="2026-04-15")
    assert len(rows) == 2
    assert all(r["date"] <= "2026-04-15" for r in rows)


def test_get_expenses_date_range_filter(db_conn):
    rows = get_expenses(db_conn, start_date="2026-04-15", end_date="2026-04-15")
    assert len(rows) == 1
    assert rows[0]["date"] == "2026-04-15"


def test_get_expenses_ordered_desc(db_conn):
    rows = get_expenses(db_conn)
    dates = [r["date"] for r in rows]
    assert dates == sorted(dates, reverse=True)


def test_get_expenses_empty_string_dates_ignored(db_conn):
    rows = get_expenses(db_conn, start_date="", end_date="")
    assert len(rows) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/manasdani/Documents/Claude\ Expense\ Tracker/expense-tracker
source venv/bin/activate
pytest tests/test_db_expenses.py -v
```

Expected: `ImportError` or `AttributeError` — `get_expenses` not defined yet.

- [ ] **Step 3: Add `get_expenses()` to `database/db.py`**

Add after the existing `create_user` function:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_db_expenses.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add database/db.py tests/test_db_expenses.py
git commit -m "feat: add get_expenses() DB helper with optional date range filter"
```

---

## Task 2: DB helper — `get_expense_stats()`

**Files:**
- Modify: `database/db.py`
- Modify: `tests/test_db_expenses.py`

- [ ] **Step 1: Add failing tests for `get_expense_stats`**

Append to `tests/test_db_expenses.py`:

```python
from database.db import get_expense_stats


def test_get_expense_stats_no_filter(db_conn):
    stats = get_expense_stats(db_conn)
    assert stats["total_spent"] == pytest.approx(60.00)
    assert stats["transaction_count"] == 3
    assert stats["top_category"] == "Bills"


def test_get_expense_stats_with_date_range(db_conn):
    stats = get_expense_stats(db_conn, start_date="2026-04-01", end_date="2026-04-30")
    assert stats["total_spent"] == pytest.approx(30.00)
    assert stats["transaction_count"] == 2
    assert stats["top_category"] == "Transport"


def test_get_expense_stats_no_rows_returns_defaults(db_conn):
    stats = get_expense_stats(db_conn, start_date="2099-01-01")
    assert stats["total_spent"] == 0
    assert stats["transaction_count"] == 0
    assert stats["top_category"] == "—"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_db_expenses.py::test_get_expense_stats_no_filter -v
```

Expected: `ImportError` — `get_expense_stats` not defined.

- [ ] **Step 3: Add `get_expense_stats()` to `database/db.py`**

Add after `get_expenses`:

```python
def get_expense_stats(user_id, start_date=None, end_date=None):
    conn = get_db()
    query = "SELECT COALESCE(SUM(amount), 0) as total_spent, COUNT(*) as transaction_count FROM expenses WHERE user_id = ?"
    params = [user_id]
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    row = conn.execute(query, params).fetchone()

    total_spent = row["total_spent"]
    transaction_count = row["transaction_count"]

    top_category = "—"
    if transaction_count > 0:
        cat_query = (
            "SELECT category, SUM(amount) as cat_total FROM expenses WHERE user_id = ?"
        )
        cat_params = [user_id]
        if start_date:
            cat_query += " AND date >= ?"
            cat_params.append(start_date)
        if end_date:
            cat_query += " AND date <= ?"
            cat_params.append(end_date)
        cat_query += " GROUP BY category ORDER BY cat_total DESC LIMIT 1"
        cat_row = conn.execute(cat_query, cat_params).fetchone()
        if cat_row:
            top_category = cat_row["category"]

    conn.close()
    return {
        "total_spent": total_spent,
        "transaction_count": transaction_count,
        "top_category": top_category,
    }
```

- [ ] **Step 4: Run all DB tests to verify they pass**

```bash
pytest tests/test_db_expenses.py -v
```

Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add database/db.py tests/test_db_expenses.py
git commit -m "feat: add get_expense_stats() DB helper with date filter support"
```

---

## Task 3: Route update — `GET /profile`

**Files:**
- Modify: `app.py`
- Create: `tests/test_profile_filter.py`

- [ ] **Step 1: Create failing route tests**

```python
# tests/test_profile_filter.py
import pytest
from app import app
from database.db import get_db, init_db, DB_PATH
from werkzeug.security import generate_password_hash
import os


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("database.db.DB_PATH", db_path)
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_profile_filter.py -v
```

Expected: Tests fail — profile route returns hardcoded data, not DB data.

- [ ] **Step 3: Update `app.py` `GET /profile` handler**

Replace the current `profile` route function with:

```python
from database.db import get_db, init_db, seed_db, get_user_by_email, get_user_by_id, update_user, create_user, get_expenses, get_expense_stats

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        error = None
        success = None

        if new_password:
            if not check_password_hash(user["password_hash"], current_password):
                error = "Current password is incorrect."
            elif len(new_password) < 8:
                error = "New password must be at least 8 characters."
            elif new_password != confirm_password:
                error = "New passwords do not match."
            else:
                from werkzeug.security import generate_password_hash
                update_user(session["user_id"], name or user["name"], generate_password_hash(new_password))
                success = "Password updated successfully."
                user = get_user_by_id(session["user_id"])
        elif name and name != user["name"]:
            update_user(session["user_id"], name)
            success = "Name updated successfully."
            user = get_user_by_id(session["user_id"])

        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()
        transactions = get_expenses(session["user_id"], start_date or None, end_date or None)
        stats = get_expense_stats(session["user_id"], start_date or None, end_date or None)
        categories = _build_categories(transactions, stats["total_spent"])
        return render_template("profile.html", user=user, stats=stats,
                               transactions=transactions, categories=categories,
                               start_date=start_date, end_date=end_date,
                               error=error, success=success)

    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    transactions = get_expenses(session["user_id"], start_date or None, end_date or None)
    stats = get_expense_stats(session["user_id"], start_date or None, end_date or None)
    categories = _build_categories(transactions, stats["total_spent"])

    return render_template("profile.html", user=user, stats=stats,
                           transactions=transactions, categories=categories,
                           start_date=start_date, end_date=end_date)


def _build_categories(transactions, total_spent):
    """Compute per-category totals and percentages from a list of expense rows."""
    cat_totals = {}
    for txn in transactions:
        cat_totals[txn["category"]] = cat_totals.get(txn["category"], 0) + txn["amount"]
    categories = []
    for name, amount in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
        pct = round(amount / total_spent * 100) if total_spent else 0
        categories.append({"name": name, "amount": amount, "pct": pct})
    return categories
```

> **Note:** `_build_categories` is a module-level helper in `app.py`, defined before the `profile` route. It is NOT a route function — no `@app.route` decorator.

- [ ] **Step 4: Run route tests to verify they pass**

```bash
pytest tests/test_profile_filter.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Run full test suite to verify no regressions**

```bash
pytest -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_profile_filter.py
git commit -m "feat: wire profile route to real DB data with date range filter support"
```

---

## Task 4: Template — date filter bar

**Files:**
- Modify: `templates/profile.html`

- [ ] **Step 1: Add filter bar above the transaction table**

In `templates/profile.html`, insert the following block immediately before `<section class="profile-card">` (the "Recent Transactions" section, around line 40):

```html
<!-- ── Date filter ── -->
<div class="filter-bar">
    <form method="GET" action="{{ url_for('profile') }}" class="filter-form">
        <label for="start_date" class="filter-label">From</label>
        <input type="date" id="start_date" name="start_date"
               value="{{ start_date }}" class="filter-input">
        <label for="end_date" class="filter-label">To</label>
        <input type="date" id="end_date" name="end_date"
               value="{{ end_date }}" class="filter-input">
        <button type="submit" class="btn-accent filter-btn">Filter</button>
        {% if start_date or end_date %}
        <a href="{{ url_for('profile') }}" class="filter-clear">Clear</a>
        {% endif %}
    </form>
    {% if start_date or end_date %}
    <p class="filter-active-label">
        Showing results
        {% if start_date %}from <strong>{{ start_date }}</strong>{% endif %}
        {% if end_date %}to <strong>{{ end_date }}</strong>{% endif %}
    </p>
    {% endif %}
</div>
```

- [ ] **Step 2: Add CSS for filter bar to `static/css/style.css`**

Append to the end of `static/css/style.css`:

```css
/* ── Date filter bar ── */
.filter-bar {
    margin-bottom: 1.5rem;
}

.filter-form {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.filter-label {
    font-size: 0.875rem;
    color: var(--ink-muted, #666);
    font-weight: 500;
}

.filter-input {
    padding: 0.4rem 0.6rem;
    border: 1px solid var(--border, #ddd);
    border-radius: 6px;
    font-size: 0.875rem;
    background: var(--paper, #fff);
    color: var(--ink, #111);
}

.filter-btn {
    padding: 0.4rem 1rem;
    font-size: 0.875rem;
}

.filter-clear {
    font-size: 0.875rem;
    color: var(--ink-muted, #666);
    text-decoration: underline;
}

.filter-active-label {
    margin-top: 0.5rem;
    font-size: 0.875rem;
    color: var(--ink-muted, #666);
}
```

- [ ] **Step 3: Verify empty transaction state renders without errors**

Start the app and visit `/profile?start_date=2099-01-01`:

```bash
python app.py
```

Open browser: `http://localhost:5001/profile?start_date=2099-01-01`

Expected:
- Filter inputs are pre-filled (`start_date` = `2099-01-01`)
- "Clear" link visible
- Stats show `$0.00`, `0`, `—`
- Transaction table has no rows
- Category breakdown is empty
- No Python errors in terminal

- [ ] **Step 4: Verify filter round-trip with real data**

Log in as demo user (`demo@spendly.com` / `demo123`), apply filter `2026-04-01` to `2026-04-07`.

Expected:
- Only transactions with dates 2026-04-01 through 2026-04-07 appear
- Stats reflect filtered totals only
- Date inputs retain the submitted values
- "Showing results from 2026-04-01 to 2026-04-07" label visible

- [ ] **Step 5: Commit**

```bash
git add templates/profile.html static/css/style.css
git commit -m "feat: add date filter bar to profile page"
```

---

## Self-Review

### Spec coverage

| Spec requirement | Task covering it |
|---|---|
| Replace stub data with real DB data | Task 3 (route), Tasks 1+2 (helpers) |
| `get_expenses()` with optional date filter | Task 1 |
| `get_expense_stats()` with defaults on zero rows | Task 2 |
| Filter form `method="GET"` | Task 4 |
| Pre-fill date inputs | Task 4 |
| "Showing results from X to Y" label | Task 4 |
| "Clear" link to unfiltered profile | Task 4 |
| Stats update to reflect filtered range | Task 3 |
| Category breakdown from real data | Task 3 (`_build_categories`) |
| Only `start_date` filter works | Task 1 (test), Task 3 (route) |
| Only `end_date` filter works | Task 1 (test), Task 3 (route) |
| Empty string dates treated as no filter | Task 1 (test), Task 3 (route) |
| POST /profile handler not broken | Task 3 (POST branch preserved) |
| Session guard kept | Task 3 (guard on line 1 of route) |

### Placeholder scan

No TBD, TODO, or vague steps found.

### Type consistency

- `get_expenses` returns list of `sqlite3.Row` — template accesses `txn["date"]`, `txn["description"]`, `txn["category"]`, `txn["amount"]` — all selected in the query ✓
- `get_expense_stats` returns dict with keys `total_spent`, `transaction_count`, `top_category` — template uses `stats.total_spent`, `stats.transaction_count`, `stats.top_category` — Jinja2 supports both dot and bracket on dicts ✓
- `_build_categories` returns list of `{"name": ..., "amount": ..., "pct": ...}` — template uses `cat.name`, `cat.amount`, `cat.pct` ✓
- `start_date` / `end_date` passed to template as strings, used in `value="{{ start_date }}"` ✓
