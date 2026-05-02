from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from database.db import get_db, init_db, seed_db, get_user_by_email, get_user_by_id, update_user, create_user

app = Flask(__name__)
app.secret_key = "dev-secret-change-in-prod"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form["name"].strip()
    email = request.form["email"].strip()
    password = request.form["password"]

    if not name:
        return render_template("register.html", error="Name is required.")

    if "@" not in email:
        return render_template("register.html", error="Please enter a valid email address.")

    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.")

    if get_user_by_email(email):
        return render_template("register.html", error="An account with that email already exists.")

    create_user(name, email, password)
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form["email"].strip()
    password = request.form["password"]

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.")

    session["user_id"] = user["id"]
    return redirect(url_for("profile"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])

    stats = {
        "total_spent": 324.45,
        "transaction_count": 8,
        "top_category": "Bills",
    }

    transactions = [
        {"date": "2026-04-10", "description": "Groceries",       "category": "Food",          "amount": 18.20},
        {"date": "2026-04-10", "description": "Miscellaneous",   "category": "Other",         "amount": 8.75},
        {"date": "2026-04-09", "description": "Clothing",        "category": "Shopping",      "amount": 65.00},
        {"date": "2026-04-07", "description": "Cinema tickets",  "category": "Entertainment", "amount": 25.00},
        {"date": "2026-04-05", "description": "Pharmacy",        "category": "Health",        "amount": 30.00},
        {"date": "2026-04-03", "description": "Electricity bill","category": "Bills",         "amount": 120.00},
        {"date": "2026-04-02", "description": "Monthly bus pass","category": "Transport",     "amount": 45.00},
        {"date": "2026-04-01", "description": "Lunch at cafe",   "category": "Food",          "amount": 12.50},
    ]

    categories = [
        {"name": "Bills",         "amount": 120.00, "pct": 37},
        {"name": "Shopping",      "amount": 65.00,  "pct": 20},
        {"name": "Transport",     "amount": 45.00,  "pct": 14},
        {"name": "Health",        "amount": 30.00,  "pct": 9},
        {"name": "Entertainment", "amount": 25.00,  "pct": 8},
        {"name": "Food",          "amount": 30.70,  "pct": 9},
        {"name": "Other",         "amount": 8.75,   "pct": 3},
    ]

    return render_template("profile.html", user=user, stats=stats,
                           transactions=transactions, categories=categories)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
