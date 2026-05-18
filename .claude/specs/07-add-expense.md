# Spec: Add Expense

## Overview
Step 7 replaces the stub `GET /expenses/add` route with a fully functional form that lets logged-in users record a new expense. The form collects amount, category, date, and an optional description, then inserts the row into the `expenses` table via a new `create_expense()` DB helper. On success the user is redirected to `/profile` so they can immediately see the new entry in their transaction list.

## Depends on
- Step 01 — database setup (`expenses` table exists)
- Step 03 — login/logout (session-based auth)
- Step 04 — profile page (redirect destination after save)

## Routes
- `GET /expenses/add` — render blank add-expense form — logged-in only
- `POST /expenses/add` — validate and insert expense, redirect to `/profile` — logged-in only

## Database changes
No new tables or columns. The `expenses` table already has all required columns:
`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`.

New DB helper needed in `database/db.py`:
```python
def create_expense(user_id, amount, category, date, description):
    ...
```

## Templates
- **Create:** `templates/add_expense.html` — form with fields: amount, category, date, description

## Files to change
- `app.py` — replace stub `add_expense()` with GET/POST implementation; import `create_expense`
- `database/db.py` — add `create_expense()` helper
- `templates/base.html` — optionally add "Add Expense" nav link (only shown when logged in)

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only
- Parameterised queries only — never f-strings in SQL
- Redirect to `url_for("profile")` on successful POST — never hardcode URLs
- Auth guard: if `session.get("user_id")` is falsy, redirect to `url_for("login")`
- `create_expense()` lives in `database/db.py`, not inline in the route
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Amount must be a positive float — reject zero or negative values
- Category must be one of: Food, Transport, Bills, Health, Entertainment, Shopping, Other
- Date must be a valid ISO date (YYYY-MM-DD) — use an HTML `<input type="date">` to enforce client-side; validate server-side too
- Description is optional — store `None` if blank

## Definition of done
- [ ] Visiting `/expenses/add` while logged out redirects to `/login`
- [ ] Visiting `/expenses/add` while logged in renders a form with fields: amount, category (select), date, description
- [ ] Submitting the form with valid data inserts a row into `expenses` and redirects to `/profile`
- [ ] The new expense appears in the transaction list on `/profile` immediately after redirect
- [ ] Submitting with a missing or zero amount re-renders the form with an error message
- [ ] Submitting with a missing date re-renders the form with an error message
- [ ] Submitting with an invalid category re-renders the form with an error message
- [ ] Previously entered values are re-populated on validation error (no data loss)
- [ ] `create_expense()` uses a parameterised query — no f-strings in SQL
