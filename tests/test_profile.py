"""Step 4 — the profile page.

Covers the definition of done in .claude/specs/04-profile-page.md. Everything
the page renders is hardcoded in app.py this step, so these assert the layout
and the guard, not the numbers. Step 5 replaces the fixtures with queries; the
structural assertions here should keep passing unchanged.
"""

import re

from markupsafe import escape

from app import PROFILE_BREAKDOWN, PROFILE_TRANSACTIONS, PROFILE_USER

TEMPLATE = "templates/profile.html"


def sign_in(client, demo):
    client.post("/login", data={"email": demo["email"], "password": demo["password"]})


# ------------------------------------------------------------------ #
# The guard                                                           #
# ------------------------------------------------------------------ #

def test_signed_out_visitor_is_redirected_to_login(client):
    response = client.get("/profile")

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_signed_in_visitor_gets_the_page(client, demo):
    sign_in(client, demo)

    assert client.get("/profile").status_code == 200


# ------------------------------------------------------------------ #
# The four sections                                                   #
# ------------------------------------------------------------------ #

def test_user_card_shows_name_and_email(client, demo):
    sign_in(client, demo)
    body = client.get("/profile").get_data(as_text=True)

    assert PROFILE_USER["username"] in body
    assert PROFILE_USER["email"] in body
    assert "Member since" in body


def test_three_summary_stats_are_rendered(client, demo):
    sign_in(client, demo)
    body = client.get("/profile").get_data(as_text=True)

    assert body.count('class="stat-tile"') == 3
    for label in ("Total spent", "Transactions", "Top category"):
        assert label in body


def test_transaction_table_lists_every_row(client, demo):
    sign_in(client, demo)
    body = client.get("/profile").get_data(as_text=True)

    assert "Transaction history" in body
    assert len(PROFILE_TRANSACTIONS) >= 3
    for txn in PROFILE_TRANSACTIONS:
        # Jinja autoescapes, so "Month's groceries" reaches the page as
        # "Month&#39;s groceries".
        assert str(escape(txn["description"])) in body


def test_breakdown_covers_all_four_categories(client, demo):
    sign_in(client, demo)
    body = client.get("/profile").get_data(as_text=True)

    assert "Category breakdown" in body
    assert body.count('class="breakdown-row"') == len(PROFILE_BREAKDOWN) == 4
    for row in PROFILE_BREAKDOWN:
        assert f'pct-{row["pct_step"]}' in body


def test_iso_dates_are_rendered_readably(client, demo):
    sign_in(client, demo)
    body = client.get("/profile").get_data(as_text=True)

    # The `day` filter turns 2026-08-22 into "22 Aug"; raw ISO must not leak.
    assert "22 Aug" in body
    assert "2026-08-22" not in body


# ------------------------------------------------------------------ #
# The navbar (base.html, so it applies to every page)                 #
# ------------------------------------------------------------------ #

def test_navbar_shows_signed_in_state(client, demo):
    sign_in(client, demo)
    body = client.get("/").get_data(as_text=True)

    assert "/logout" in body
    assert PROFILE_USER["username"] in body
    assert "Get started" not in body


def test_navbar_shows_signed_out_state(client):
    body = client.get("/").get_data(as_text=True)

    assert "Sign in" in body
    assert "Get started" in body
    assert "/logout" not in body


def test_logout_link_survives_the_mobile_nav_rule(client, demo):
    """style.css:599 hides .nav-links a:not(.nav-cta) below 600px."""
    sign_in(client, demo)
    body = client.get("/").get_data(as_text=True)

    assert re.search(r'href="/logout"[^>]*class="nav-cta"', body)


# ------------------------------------------------------------------ #
# The styling rules                                                   #
# ------------------------------------------------------------------ #

def test_template_uses_no_hex_colours_or_inline_styles():
    source = open(TEMPLATE).read()

    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", source)
    assert 'style="' not in source
