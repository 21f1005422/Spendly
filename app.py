import os
import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config["DATABASE"] = os.path.join(BASE_DIR, "expense_tracker.db")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")

db.init_app(app)


# ------------------------------------------------------------------ #
# Step 4 fixtures — hardcoded, deleted in Step 5                      #
# ------------------------------------------------------------------ #
# The profile page is built against literals so the layout can be settled
# before any query exists. Every key matches a column database/db.py returns,
# so Step 5 swaps these for SELECTs without touching profile.html. The values
# mirror the seed data in database/db.py, so the page looks the same once it
# is wired up.

PROFILE_USER = {
    "username": "Yash Agarwal",
    "email": "demo@spendly.app",
    "initials": "YA",
    "member_since": "August 2026",
}

PROFILE_STATS = {
    "total_spent": 12624.50,
    "transaction_count": 12,
    "top_category": "Travel",
}

# Newest first, the order Step 5's ORDER BY date DESC will produce.
PROFILE_TRANSACTIONS = [
    {"id": 7,  "date": "2026-08-22", "category": "Travel", "amount": 180.00,  "description": "Auto to the station"},
    {"id": 6,  "date": "2026-08-18", "category": "Other",  "amount": 560.75,  "description": "Birthday gift"},
    {"id": 5,  "date": "2026-08-15", "category": "Bills",  "amount": 1299.00, "description": "Broadband renewal"},
    {"id": 4,  "date": "2026-08-11", "category": "Food",   "amount": 240.00,  "description": "Lunch with the team"},
    {"id": 3,  "date": "2026-08-07", "category": "Travel", "amount": 899.00,  "description": "Monthly metro pass"},
    {"id": 2,  "date": "2026-08-04", "category": "Food",   "amount": 320.50,  "description": "Groceries - vegetables and milk"},
    {"id": 1,  "date": "2026-08-02", "category": "Bills",  "amount": 1450.00, "description": "Electricity bill"},
    {"id": 12, "date": "2026-07-26", "category": "Food",   "amount": 275.25,  "description": "Coffee and snacks"},
    {"id": 11, "date": "2026-07-20", "category": "Other",  "amount": 450.00,  "description": "Stationery and printing"},
    {"id": 10, "date": "2026-07-14", "category": "Travel", "amount": 3400.00, "description": "Weekend trip - train tickets"},
    {"id": 9,  "date": "2026-07-09", "category": "Food",   "amount": 2100.00, "description": "Month's groceries"},
    {"id": 8,  "date": "2026-07-03", "category": "Bills",  "amount": 1450.00, "description": "Electricity bill"},
]

# `pct` is the true share of total_spent, shown as the label. `pct_step` is
# that value rounded to a 5% step, which selects the bar's width class — the
# spec forbids inline styles, so widths have to be enumerable. The two differ
# by up to 2.5%, and the steps sum to 105 rather than 100.
PROFILE_BREAKDOWN = [
    {"category": "Travel", "total": 4479.00, "pct": 35, "pct_step": 35},
    {"category": "Bills",  "total": 4199.00, "pct": 33, "pct_step": 35},
    {"category": "Food",   "total": 2935.75, "pct": 23, "pct_step": 25},
    {"category": "Other",  "total": 1010.75, "pct": 8,  "pct_step": 10},
]

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


@app.template_filter("day")
def day(iso):
    """'2026-08-22' -> '22 Aug'.

    A filter rather than a context key, so it works unchanged on the ISO TEXT
    dates real rows carry (database/db.py:37).
    """
    _, month, dom = iso.split("-")
    return f"{int(dom)} {MONTHS[int(month) - 1]}"


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # First failure wins, so the message names the first thing wrong.
        if not username or not email or not password:
            error = "All fields are required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        else:
            error = None

        if error is None:
            conn = db.get_db()
            try:
                conn.execute(
                    "INSERT INTO users (username, email, password_hash)"
                    " VALUES (?, ?, ?)",
                    (username, email, generate_password_hash(password)),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                # users.email is COLLATE NOCASE UNIQUE.
                error = "An account with that email already exists."
            else:
                return redirect(url_for("login"))

        return render_template("register.html", error=error)

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = db.get_db().execute(
            "SELECT id, username, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()

        # One message for both failures, so it can't be used to probe which
        # emails are registered.
        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.")

        session.clear()
        session["user_id"] = user["id"]
        # A copy of the name, so base.html's navbar can greet the user on every
        # page without a query. A route that lets a user rename themselves has
        # to rewrite this too, or the navbar goes stale.
        session["username"] = user["username"]
        return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if session.get("user_id") is None:
        return redirect(url_for("login"))

    # The session id is checked but not used: nothing is scoped to the user
    # until Step 5 replaces these fixtures with queries.
    return render_template(
        "profile.html",
        user=PROFILE_USER,
        stats=PROFILE_STATS,
        transactions=PROFILE_TRANSACTIONS,
        breakdown=PROFILE_BREAKDOWN,
    )


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

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
