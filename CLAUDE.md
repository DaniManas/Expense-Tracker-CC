# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (port 5001, debug mode)
python3 app.py

# Run tests
pytest
```

## Architecture

**Spendly** is a Flask-based personal expense tracking web app with a Jinja2 + vanilla JS frontend and SQLite database.

### Stack
- **Backend**: Flask (Python), SQLite via `database/db.py`
- **Frontend**: Jinja2 templates, vanilla JS (`static/js/main.js`), custom CSS (`static/css/style.css`)
- **Auth**: Session-based (Werkzeug for password hashing)

### Key Files
- `app.py` — all Flask routes; routes for auth and expenses exist but are mostly stubbed
- `database/db.py` — SQLite connection and schema management (not yet implemented)
- `templates/base.html` — shared layout (navbar, footer); all other templates extend this
- `static/css/style.css` — 874-line design system with CSS variables for color, typography, and components

### Design System (CSS)
Variables defined at `:root` level:
- Colors: `--ink` (dark), `--paper` (light), `--accent` (#1a472a green), `--accent-2` (orange), `--danger` (red)
- Fonts: DM Serif Display (headings), DM Sans (body) via Google Fonts
- Responsive breakpoints: 900px and 600px
- Reusable classes: `.btn-primary`, `.btn-ghost`, `.form-input`, `.auth-card`

### Project State
The UI scaffolding is complete (landing, auth forms, terms, privacy). Core backend features are stubbed and pending implementation in this order (as indicated by comments in `app.py`):
1. SQLite schema + db helper functions (`database/db.py`)
2. User registration and login with sessions
3. Expense CRUD endpoints
4. Dashboard and analytics views
