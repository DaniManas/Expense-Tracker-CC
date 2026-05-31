# Spec: Edit Expense

## Overview
Step 08 replaces the `GET /expenses/<id>/edit` stub with a full edit-expense flow. Users can click "Edit" on any expense in their profile transaction list, update the amount, category, date, and description, and save the changes back to the database. The form is pre-populated with the existing values so users only need to change what they want. Access is restricted to logged-in users who own the expense — attempting to edit another user's expense returns 403.

## Depends on
- Step 01 — database and schema
- Step 02 — user registration (users table)
- Step 05 / 06 — profile page with transaction list (where Edit links live)
- Step 07 — add-expense (establishes `create_expense`, `VALID_CATEGORIES`, and `add_expense.html` as a reference form)

## Routes
- `GET  /expenses/<int:id>/edit` — render pre-filled edit form — logged-in only
- `POST /expenses/<int:id>/edit` — validate and save updated expense — logged-in only

## Database changes
No new tables or columns. This step adds two new DB helper functions to `database/db.py`:
- `get_expense_by_id(expense_id)` — fetch a single expense row by primary key
- `update_expense(expense_id, amount, category, date, description)` — UPDATE the row in place

## Templates
- **Create:** `templates/edit_expense.html` — edit form that extends `base.html`
- **Modify:** `templates/profile.html` — ensure each row in the transaction list has an Edit link pointing to `url_for('edit_expense', id=txn['id'])`

## Files to change
- `app.py` — implement `edit_expense` route (GET + POST); import new DB helpers
- `database/db.py` — add `get_expense_by_id` and `update_expense`
- `templates/profile.html` — add Edit links per transaction row

## Files to create
- `templates/edit_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only
- Parameterised queries only — never f-strings in SQL
- Ownership check required: if `expense["user_id"] != session["user_id"]`, call `abort(403)`
- If expense not found, call `abort(404)`
- Validation mirrors add-expense: amount > 0, category in `VALID_CATEGORIES`, date non-empty and valid ISO format
- On validation error re-render the form with the `error` message and the submitted values (not the DB values) so the user sees what they typed
- On success redirect to `url_for('profile')` — no flash messages needed
- Use CSS variables — never hardcode hex values in templates or CSS
- All templates extend `base.html`
- `get_expense_by_id` must use `try/finally` to close the connection (same pattern as `get_expenses`)
- Import `get_expense_by_id` and `update_expense` in `app.py` alongside existing imports
- Export list in `app.py` import line must stay on one `from database.db import ...` line

## Definition of done
- [ ] `GET /expenses/<id>/edit` renders a form pre-filled with the expense's current amount, category, date, and description
- [ ] Submitting the form with valid data updates the expense in the database and redirects to `/profile`
- [ ] Submitting with an invalid amount (non-numeric, zero, negative) re-renders the form with an error
- [ ] Submitting with an invalid category re-renders the form with an error
- [ ] Submitting with a missing or malformed date re-renders the form with an error
- [ ] Visiting `/expenses/<id>/edit` for an expense owned by a different user returns 403
- [ ] Visiting `/expenses/99999/edit` (non-existent ID) returns 404
- [ ] A logged-out user visiting the edit URL is redirected to `/login`
- [ ] Each expense row in the profile transaction list has a visible Edit link
- [ ] Edit link on the profile page uses `url_for('edit_expense', id=txn['id'])`
