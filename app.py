from datetime import date as date_type
from flask import Flask, abort, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from database.db import (
    get_db,
    init_db,
    seed_db,
    get_user_by_email,
    get_user_by_id,
    update_user,
    create_user,
    create_expense,
    get_expenses,
    get_expense_stats,
    get_expense_by_id,
    update_expense,
)

VALID_CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]

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
        return render_template(
            "register.html", error="Please enter a valid email address."
        )

    if len(password) < 8:
        return render_template(
            "register.html", error="Password must be at least 8 characters."
        )

    if get_user_by_email(email):
        return render_template(
            "register.html", error="An account with that email already exists."
        )

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


def _build_categories(transactions, total_spent):
    cat_totals = {}
    for txn in transactions:
        cat_totals[txn["category"]] = cat_totals.get(txn["category"], 0) + txn["amount"]
    categories = []
    for name, amount in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
        pct = round(amount / total_spent * 100) if total_spent else 0
        categories.append({"name": name, "amount": amount, "pct": pct})
    return categories


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    transactions = get_expenses(
        session["user_id"], start_date or None, end_date or None
    )
    stats = get_expense_stats(session["user_id"], start_date or None, end_date or None)
    categories = _build_categories(transactions, stats["total_spent"])

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        error = None
        if not name:
            error = "Name is required."
        elif new_password and new_password != confirm_password:
            error = "Passwords do not match."
        elif new_password and len(new_password) < 8:
            error = "Password must be at least 8 characters."

        if error:
            return render_template(
                "profile.html",
                user=user,
                stats=stats,
                transactions=transactions,
                categories=categories,
                start_date=start_date,
                end_date=end_date,
                error=error,
            )

        password_hash = generate_password_hash(new_password) if new_password else None
        update_user(session["user_id"], name, password_hash)
        return redirect(url_for("profile", start_date=start_date, end_date=end_date))

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        start_date=start_date,
        end_date=end_date,
    )


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("add_expense.html", categories=VALID_CATEGORIES)

    amount_raw = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    expense_date = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()

    error = None
    try:
        amount = float(amount_raw)
        if amount <= 0:
            error = "Amount must be greater than zero."
    except ValueError:
        error = "Amount must be a valid number."

    if not error and category not in VALID_CATEGORIES:
        error = "Please select a valid category."

    if not error and not expense_date:
        error = "Date is required."

    if not error:
        try:
            date_type.fromisoformat(expense_date)
        except ValueError:
            error = "Date must be a valid date (YYYY-MM-DD)."

    if error:
        return render_template(
            "add_expense.html",
            categories=VALID_CATEGORIES,
            error=error,
            form={
                "amount": amount_raw,
                "category": category,
                "date": expense_date,
                "description": description,
            },
        )

    create_expense(session["user_id"], amount, category, expense_date, description)
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    expense = get_expense_by_id(id)
    if expense is None:
        abort(404)
    if expense["user_id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template(
            "edit_expense.html", categories=VALID_CATEGORIES, expense=expense
        )

    amount_raw = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    expense_date = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()

    error = None
    try:
        amount = float(amount_raw)
        if amount <= 0:
            error = "Amount must be greater than zero."
    except ValueError:
        error = "Amount must be a valid number."

    if not error and category not in VALID_CATEGORIES:
        error = "Please select a valid category."

    if not error and not expense_date:
        error = "Date is required."

    if not error:
        try:
            date_type.fromisoformat(expense_date)
        except ValueError:
            error = "Date must be a valid date (YYYY-MM-DD)."

    if error:
        return render_template(
            "edit_expense.html",
            categories=VALID_CATEGORIES,
            expense=expense,
            error=error,
            form={
                "amount": amount_raw,
                "category": category,
                "date": expense_date,
                "description": description,
            },
        )

    update_expense(id, amount, category, expense_date, description)
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
