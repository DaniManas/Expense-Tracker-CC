# Spec: Date Filter for Profile Page

## Overview
The profile page currently displays hardcoded stub transactions and stats. This step replaces those stubs with real data from the `expenses` table and adds a date range filter (start date / end date) so users can narrow the transaction list and summary stats to a specific period. The filter submits via `GET` so the URL remains shareable and the browser back button works naturally. Stats (total spent, transaction count, top category) and the category breakdown recalculate dynamically based on the filtered date range.

## Depends on
- Step 1 — Database setup (`expenses` table, `get_db()`)
- Step 3 — Login and Logout (session populated with `user_id`)
- Step 4 — Profile (route implemented, `get_user_by_id()` in place)
- Step 5 — Profile Page Design (layout and CSS in place)

## Routes
No new routes. The existing `GET /profile` handler in `app.py` is extended to accept `start_date` and `end_date` query parameters.

## Database changes
No new tables or columns. The existing `expenses` table is used as-is.

Two new helper functions must be added to `database/db.py`:
- `get_expenses(user_id, start_date=None, end_date=None)` — fetch all expenses for a user, optionally filtered by date range (inclusive). Returns rows ordered by `date DESC`.
- `get_expense_stats(user_id, start_date=None, end_date=None)` — return a dict with `total_spent` (sum of amount), `transaction_count` (row count), and `top_category` (category with highest total amount). Returns sensible defaults (`0`, `0`, `"—"`) when no rows match.

## Templates
- **Modify:** `templates/profile.html`
  - Add a date filter bar above the transaction list with two `<input type="date">` fields (`start_date`, `end_date`) and a Filter button
  - The form uses `method="GET"` and `action="{{ url_for('profile') }}"`
  - Pre-fill the date inputs with the current filter values from the template context
  - Show a "Showing results from X to Y" label when a filter is active; hide it when no filter is applied
  - Add a "Clear" link that points to `url_for('profile')` with no query params

## Files to change
- `app.py` — extend `GET /profile` to read `start_date` and `end_date` from `request.args`; call `get_expenses()` and `get_expense_stats()` instead of using hardcoded stub data; pass filter values to the template
- `database/db.py` — add `get_expenses()` and `get_expense_stats()`
- `templates/profile.html` — add date filter bar and wire up dynamic data

## Files to create
No new files.

## New dependencies
No new pip packages.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders) — never f-strings in SQL
- Passwords hashed with werkzeug (no password changes in this step, rule included for completeness)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `get_expenses()` and `get_expense_stats()` must live in `database/db.py`, not in `app.py`
- Date parameters are optional: when `start_date` or `end_date` is an empty string or absent, that bound is not applied
- SQL date comparison uses SQLite's ISO string ordering (`date >= ?` and `date <= ?`) — no date parsing in Python
- `get_expense_stats()` must handle zero-row results without raising exceptions (use `COALESCE` or Python fallbacks)
- The category breakdown passed to the template must be computed from real DB data, not hardcoded — derive `pct` as `round(category_amount / total_spent * 100)` in Python
- The filter form uses `method="GET"` — do not change it to POST
- Do not break the existing `POST /profile` handler (name/password updates) — only `GET` is modified in this step
- If session has no `user_id`, redirect to `/login` (existing guard, keep it)

## Definition of done
- [ ] Visiting `/profile` without query params shows all expenses for the logged-in user from the database (not hardcoded)
- [ ] Total spent, transaction count, and top category reflect real DB data
- [ ] Submitting the date filter form with a start date and end date filters the transaction list to that range (inclusive)
- [ ] Stats and category breakdown update to match the filtered date range
- [ ] The date inputs are pre-filled with the current filter values after submission
- [ ] A "Clear" link removes the filter and shows all transactions
- [ ] Filtering with only a start date (no end date) returns all transactions on or after that date
- [ ] Filtering with only an end date (no start date) returns all transactions on or before that date
- [ ] An empty date range (no expenses match) shows zero stats and an empty transaction list without errors
- [ ] App starts without errors on `python app.py`
