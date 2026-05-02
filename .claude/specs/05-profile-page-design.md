# Spec: Profile Page Design

## Overview
The profile page (`/profile`) is fully functional after Step 4, but it currently borrows the narrow `auth-section` / `auth-card` layout intended for login and register. This step replaces that layout with a proper two-column settings page: a fixed sidebar showing the user's avatar, name, and email alongside a main content area with labelled card sections for display-name editing and password change. The goal is a design that feels like an account settings page, not a login form, while keeping the Spendly design system (CSS variables, DM Serif / DM Sans, `var(--accent)` green).

## Depends on
- Step 1 — Database setup (`users` table, `get_db()`)
- Step 2 — Registration (`create_user()`, `get_user_by_email()`)
- Step 3 — Login and Logout (session populated)
- Step 4 — Profile (route implemented, `get_user_by_id()` and `update_user()` in place)

## Routes
No new routes. The existing `GET /profile` and `POST /profile` handlers in `app.py` are unchanged.

## Database changes
No database changes.

## Templates
- **Modify:** `templates/profile.html`
  - Remove `auth-section` / `auth-container` / `auth-card` wrapper classes
  - Replace with a `.profile-page` > `.profile-sidebar` + `.profile-main` two-column layout
  - Sidebar: avatar circle (initials from `user["name"]`), display name, email, member-since date, and a "Back to home" link
  - Main: two `.settings-card` sections — "Account details" (name field + Save button) and "Change password" (current / new / confirm fields + Update password button)
  - Error and success banners appear above the relevant section, not above the whole form
  - Keep a single `<form>` wrapping both sections (existing POST handler expects all fields in one request)

## Files to change
- `templates/profile.html` — new layout as described above
- `static/css/style.css` — add `.profile-page`, `.profile-sidebar`, `.profile-main`, `.profile-avatar`, `.settings-card`, `.settings-card-title`, and responsive rules; keep all existing auth-page rules untouched

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — no f-strings in SQL
- Passwords hashed with `werkzeug`
- Use CSS variables exclusively — never hardcode hex values (reference `--accent`, `--ink`, `--paper`, etc.)
- All templates extend `base.html`
- Avatar initials: take the first character of `user["name"]` uppercased; render in a circle using `--accent` background and `--paper` text
- The two-column layout uses CSS Grid (`grid-template-columns: 260px 1fr`) on wide screens; collapses to single column below 700 px
- Sidebar is `position: sticky; top: 80px` so it stays visible while scrolling the main area
- Each `.settings-card` has a visible title (`<h2 class="settings-card-title">`) and a bottom border separating sections
- The Save and Update password buttons must be `type="submit"` inside the shared form — do not add JS to split them
- Do not remove or rename existing CSS classes used by `auth-section`, `auth-card`, etc. — login and register pages still depend on them

## Definition of done
- [ ] `/profile` renders a two-column layout (sidebar left, settings cards right) on desktop
- [ ] Sidebar displays the user's initials in a coloured circle, full name, email, and member-since date
- [ ] "Account details" card contains the display-name field and a Save button
- [ ] "Change password" card contains current password, new password, and confirm password fields plus an Update password button
- [ ] Success and error banners appear inside the appropriate card, not floating above the page
- [ ] Layout collapses to a single column on screens narrower than 700 px (sidebar stacks above cards)
- [ ] No hex colours appear in the new CSS — only CSS variable references
- [ ] Login and register pages are visually unaffected (existing auth-* classes intact)
- [ ] App starts without errors on `python app.py`
- [ ] All existing profile POST functionality (name update, password update, validation) still works correctly
