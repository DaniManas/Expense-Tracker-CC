# Spec: Registration

## Overview
This step wires up the registration form so new users can create an account. The `GET /register` route and `register.html` template already exist; this step adds the `POST /register` handler that validates input, hashes the password, inserts the user into the database, and redirects to the login page on success. It also adds the `create_user()` and `get_user_by_email()` helpers to `database/db.py` — keeping all DB logic out of the route function.

## Depends on
- Step 1 — Database setup (`users` table, `get_db()`, `init_db()`, `seed_db()` all complete)

## Routes
- `POST /register` — receive form data, validate, create user, redirect to `/login` — public

## Database changes
No new tables or columns. The `users` table from Step 1 is used as-is.

## Templates
- **Modify:** `templates/register.html`
  - Fix hardcoded `action="/register"` → `action="{{ url_for('register') }}"` (CLAUDE.md: never hardcode URLs)
  - Template already renders `{% if error %}` — no structural changes needed

## Files to change
- `app.py` — add `POST` method to the `/register` route, import `create_user` and `get_user_by_email`
- `database/db.py` — add `create_user()` and `get_user_by_email()`
- `templates/register.html` — fix hardcoded action URL

## Files to create
None.

## New dependencies
No new pip packages. Uses `werkzeug.security.generate_password_hash` (already installed).

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders) — never f-strings in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash` before insertion
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `create_user()` and `get_user_by_email()` must live in `database/db.py`, not in `app.py`
- Duplicate email must be caught and returned as a user-facing error (not a 500)
- Validate server-side: name non-empty, valid email format (basic check), password ≥ 8 chars
- On success: redirect to `/login` using `redirect(url_for('login'))`
- On failure: re-render `register.html` with an `error=` message — do not redirect
- `app.py` must import `redirect, url_for, request` from flask

## Definition of done
- [ ] Submitting the form with valid data creates a new row in the `users` table with a hashed password
- [ ] Submitting a duplicate email re-renders the form with an error message ("An account with that email already exists.")
- [ ] Submitting with a password shorter than 8 characters re-renders the form with an error message
- [ ] Submitting with an empty name re-renders the form with an error message
- [ ] Successful registration redirects to `/login`
- [ ] The form action uses `url_for('register')`, not a hardcoded URL
- [ ] No plaintext passwords are stored in the database
- [ ] App starts without errors on `python app.py`
