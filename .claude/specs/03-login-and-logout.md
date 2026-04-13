# Spec: Login and Logout

## Overview
This step wires up the login form and logout action so users can authenticate and end their session. The `GET /login` route and `login.html` template already exist; this step adds the `POST /login` handler that validates credentials, verifies the hashed password, stores the user's id in the Flask session, and redirects to the profile page on success. The `GET /logout` stub is replaced with a handler that clears the session and redirects to the landing page. A `get_user_by_id()` helper is added to `database/db.py` for use in future steps. `app.secret_key` must be set for session support.

## Depends on
- Step 1 — Database setup (`users` table, `get_db()` all complete)
- Step 2 — Registration (`get_user_by_email()` and `create_user()` complete, users table populated)

## Routes
- `POST /login` — receive form data, verify credentials, set session, redirect to `/profile` — public
- `GET /logout` — clear session, redirect to `/` — logged-in (no enforcement yet, just redirect)

## Database changes
No new tables or columns. Reads from the existing `users` table using `get_user_by_email()` (already implemented).

## Templates
- **Modify:** `templates/login.html`
  - Fix hardcoded `action="/login"` → `action="{{ url_for('login') }}"` (CLAUDE.md: never hardcode URLs)
  - Template already renders `{% if error %}` — no structural changes needed

## Files to change
- `app.py` — add `POST` method to `/login` route; implement `GET /logout`; import `session` and `check_password_hash`; set `app.secret_key`
- `database/db.py` — add `get_user_by_id()` helper
- `templates/login.html` — fix hardcoded action URL

## Files to create
None.

## New dependencies
No new pip packages. Uses `werkzeug.security.check_password_hash` (already installed) and `flask.session` (already installed).

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders) — never f-strings in SQL
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `get_user_by_id()` must live in `database/db.py`, not in `app.py`
- `app.secret_key` must be set before any session usage — use a hard-coded dev string for now (e.g. `"dev-secret-change-in-prod"`)
- On login success: store `session["user_id"] = user["id"]` then `redirect(url_for("profile"))`
- On login failure (bad email or wrong password): re-render `login.html` with a generic error — do not reveal which field was wrong
- On logout: call `session.clear()` then `redirect(url_for("landing"))`
- Import `session` from `flask` in `app.py`

## Definition of done
- [ ] Submitting valid credentials sets `session["user_id"]` and redirects to `/profile`
- [ ] Submitting an unknown email re-renders the form with an error message (no 500)
- [ ] Submitting a correct email with the wrong password re-renders the form with an error message
- [ ] The error message does not reveal whether the email or password was wrong
- [ ] Visiting `/logout` clears the session and redirects to `/`
- [ ] The form action uses `url_for('login')`, not a hardcoded URL
- [ ] `get_user_by_id()` exists in `database/db.py` and returns the user row or `None`
- [ ] App starts without errors on `python app.py`
