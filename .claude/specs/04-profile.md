# Spec: Profile

## Overview
This step implements the user profile page, giving logged-in users a place to view their account details and update their display name or password. The `/profile` route currently returns a stub string; this step replaces it with a real `GET/POST` handler that reads from the session, fetches the user record, validates changes, and persists updates. It also adds the `get_user_by_id()` and `update_user()` DB helpers that the profile route needs.

## Depends on
- Step 1 — Database setup (`users` table, `get_db()` in place)
- Step 2 — Registration (`create_user()`, `get_user_by_email()` in place)
- Step 3 — Login and Logout (Flask `session` populated with `user_id` on login; `/logout` clears it)

## Routes
- `GET /profile` — render profile page with current user data — logged-in only (redirect to `/login` if no session)
- `POST /profile` — handle name and/or password update, re-render with success or error message — logged-in only

## Database changes
No new tables or columns. The existing `users` table (id, name, email, password_hash, created_at) covers all required fields.

Two new helper functions must be added to `database/db.py`:
- `get_user_by_id(user_id)` — fetch a single user row by primary key
- `update_user(user_id, name, password_hash=None)` — update `name`; only update `password_hash` when a new password is provided

## Templates
- **Create:** `templates/profile.html`
  - Extends `base.html`
  - Displays: user's name, email (read-only), member-since date
  - Form with two optional sections:
    1. Change display name (text input pre-filled with current name)
    2. Change password (current password, new password, confirm new password)
  - Renders `{% if error %}` and `{% if success %}` feedback blocks
  - All form actions use `url_for('profile')`

## Files to change
- `app.py` — replace stub `/profile` route with `GET/POST` handler; import `get_user_by_id` and `update_user`
- `database/db.py` — add `get_user_by_id()` and `update_user()`

## Files to create
- `templates/profile.html`

## New dependencies
No new pip packages. Uses `werkzeug.security.check_password_hash` and `generate_password_hash` (already installed).

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders) — never f-strings in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash`; current password verified with `check_password_hash` before allowing a password change
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `get_user_by_id()` and `update_user()` must live in `database/db.py`, not in `app.py`
- If the session has no `user_id`, redirect to `/login` immediately — do not render the profile page
- Name update and password update are independent: submitting only a new name must not touch the password hash, and vice versa
- If new password is provided: require current password verification, new password ≥ 8 chars, and new password == confirm password
- On success: re-render `profile.html` with a `success=` message — do not redirect (prevents accidental double-submit)
- On validation failure: re-render `profile.html` with an `error=` message
- Email is display-only — it must not be editable on this page

## Definition of done
- [ ] Visiting `/profile` while logged out redirects to `/login`
- [ ] Visiting `/profile` while logged in renders the user's name, email, and member-since date
- [ ] Submitting a new name updates the `name` column in the database and the page reflects the change
- [ ] Submitting a new password with a correct current password updates the `password_hash` and shows a success message
- [ ] Submitting a new password with an incorrect current password shows an error and does not update the hash
- [ ] Submitting mismatched new/confirm password shows an error
- [ ] Submitting a new password shorter than 8 characters shows an error
- [ ] Email field is visible but cannot be changed via this form
- [ ] App starts without errors on `python app.py`
