# Spec: Delete Expense

## Overview
Step 9 completes the expense CRUD cycle by implementing the delete route. When a logged-in user clicks "Delete" on an expense row (from the profile page), the app confirms ownership, deletes the record from SQLite, and redirects back to the profile. No confirmation page is needed — the delete is immediate via a POST form submission to prevent accidental deletion via link crawlers or prefetching.

## Depends on
- Step 01 — database setup (expenses table exists)
- Step 03 — login/logout (session-based auth)
- Step 04 — profile page (where delete links appear)
- Step 07 — add expense (expenses exist to delete)
- Step 08 — edit expense (ownership check pattern established)

## Routes
- `POST /expenses/<int:id>/delete` — delete expense by id, redirect to profile — logged-in only

The existing stub `GET /expenses/<int:id>/delete` in `app.py` must be replaced with a `POST`-only route.

## Database changes
No database changes. The `expenses` table already exists with `user_id` foreign key for ownership checks.

A new helper `delete_expense(expense_id)` must be added to `database/db.py`.

## Templates
- **Create:** none
- **Modify:** `templates/profile.html` — replace the stub delete link with a `<form method="POST">` button pointing to `url_for('delete_expense', id=txn.id)`

## Files to change
- `app.py` — replace stub `delete_expense` route with POST implementation
- `database/db.py` — add `delete_expense(expense_id)` helper
- `templates/profile.html` — replace delete link with POST form button
- `app.py` imports — add `delete_expense` to the import from `database.db`

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`DELETE FROM expenses WHERE id = ?`)
- Passwords hashed with werkzeug (not relevant here, but maintain convention)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Route must be `POST` only — `GET /expenses/<id>/delete` stub must be replaced, not kept alongside
- Ownership check required: fetch expense by id, `abort(403)` if `expense['user_id'] != session['user_id']`
- `abort(404)` if expense not found
- After delete, redirect to `url_for('profile')` — preserve any query params if possible, or just redirect to bare profile
- Delete button in template must be inside a `<form method="POST">` — never a bare `<a>` tag

## Definition of done
- [ ] `POST /expenses/<id>/delete` deletes the expense and redirects to `/profile`
- [ ] Visiting `/expenses/<id>/delete` via GET returns 405 Method Not Allowed
- [ ] Deleting an expense belonging to another user returns 403
- [ ] Deleting a non-existent expense id returns 404
- [ ] After deletion, the expense no longer appears in the profile transaction list
- [ ] The delete button in `profile.html` is a form POST, not a link
- [ ] Logged-out user hitting the route is redirected to `/login`
