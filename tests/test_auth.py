"""Step 3 — login, logout, and the session.

Covers the route contract in `.claude/specs/03-login-and-logout.md`. These are
regression tests as much as anything: Steps 4-9 all build on `session["user_id"]`,
so a change that quietly breaks sign-in should fail here rather than in a
feature three steps later.
"""

import re

AUTH_ERROR = re.compile(r'<div class="auth-error">\s*(.*?)\s*</div>', re.S)


def auth_error(response):
    """Return the text inside the template's error div, or None if absent."""
    match = AUTH_ERROR.search(response.get_data(as_text=True))
    return match.group(1) if match else None


# ------------------------------------------------------------------ #
# GET /login                                                          #
# ------------------------------------------------------------------ #

def test_login_page_renders_the_form(client):
    response = client.get("/login")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'name="email"' in body
    assert 'name="password"' in body


def test_login_page_shows_no_error_before_submitting(client):
    assert auth_error(client.get("/login")) is None


# ------------------------------------------------------------------ #
# POST /login — success                                               #
# ------------------------------------------------------------------ #

def test_valid_credentials_start_a_session(client, demo):
    response = client.post(
        "/login", data={"email": demo["email"], "password": demo["password"]}
    )

    assert response.status_code == 302
    # Temporary destination while /profile is a Step 4 placeholder. When Step 4
    # lands, this becomes "/profile" again — see app.py.
    assert response.headers["Location"] == "/"

    with client.session_transaction() as session:
        assert session["user_id"] == demo["id"]


def test_email_matching_is_case_insensitive(client, demo):
    """`WHERE email = ?` inherits NOCASE from the column (database/db.py:27).

    Nothing in the query says so, so this is the test that fails if the lookup
    is ever rewritten in a way that loses the column's collation.
    """
    response = client.post(
        "/login",
        data={"email": demo["email"].upper(), "password": demo["password"]},
    )

    assert response.status_code == 302

    with client.session_transaction() as session:
        assert session["user_id"] == demo["id"]


def test_login_replaces_any_pre_existing_session(client, demo):
    """session.clear() runs before user_id is set — session fixation defence."""
    with client.session_transaction() as session:
        session["stale"] = "should not survive"

    client.post(
        "/login", data={"email": demo["email"], "password": demo["password"]}
    )

    with client.session_transaction() as session:
        assert "stale" not in session
        assert session["user_id"] == demo["id"]


# ------------------------------------------------------------------ #
# POST /login — failure                                               #
# ------------------------------------------------------------------ #

def test_wrong_password_is_rejected(client, demo):
    response = client.post(
        "/login", data={"email": demo["email"], "password": "not-the-password"}
    )

    assert response.status_code == 200
    assert auth_error(response) is not None

    with client.session_transaction() as session:
        assert "user_id" not in session


def test_unknown_email_is_rejected(client):
    response = client.post(
        "/login", data={"email": "nobody@example.com", "password": "demo1234"}
    )

    assert response.status_code == 200
    assert auth_error(response) is not None

    with client.session_transaction() as session:
        assert "user_id" not in session


def test_both_failures_give_the_same_message(client, demo):
    """Otherwise /login tells an attacker which emails are registered."""
    wrong_password = client.post(
        "/login", data={"email": demo["email"], "password": "not-the-password"}
    )
    unknown_email = client.post(
        "/login", data={"email": "nobody@example.com", "password": "demo1234"}
    )

    assert auth_error(wrong_password) == auth_error(unknown_email)


# ------------------------------------------------------------------ #
# GET /logout                                                         #
# ------------------------------------------------------------------ #

def test_logout_clears_the_session(client, demo):
    client.post(
        "/login", data={"email": demo["email"], "password": demo["password"]}
    )

    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    with client.session_transaction() as session:
        assert "user_id" not in session


def test_logout_while_signed_out_is_a_no_op(client):
    """Visiting /logout with no session redirects; it does not raise."""
    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
