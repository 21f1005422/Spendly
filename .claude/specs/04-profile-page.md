# Step 4 — Profile Page

> **Status: transcribed, with derived design.** The requirements, rules, and
> definition of done below come from supplied assignment text and are
> authoritative. Everything under **Decisions** is derived from the existing
> templates and CSS — the assignment names *what* the page shows, not which
> classes, tokens, or context keys carry it. Correct the derived half freely;
> the transcribed half is fixed.

## Goal

Replace the `/profile` placeholder (`app.py:75-77`) with a guarded route and a
real `templates/profile.html`, rendering **hardcoded** data through four
sections: user info card, summary stat row, transaction history table, and
category breakdown. The point is to settle the layout before Step 5 wires
queries in, so Step 5 is a swap of the context dict — not a rewrite of the
template.

**No database queries in this step.** No schema change. No change to
`database/db.py`, no change to registration, no change to the expense routes.

The one thing this step touches outside its own files is `base.html`: the
definition of done requires the navbar to show the signed-in state, which
`03-login-and-logout.md` had deferred to Step 5. See
[Decisions → the navbar](#the-navbar-conflict).

**Unmet dependency, stated up front.** The assignment lists Step 2
(registration) as a prerequisite. It is not done — `/register` is still the
GET-only placeholder at `app.py:26-28` and ignores its form. Nothing in Step 4
depends on creating accounts, so this is not blocking, but it means the only
way to reach `/profile` is signing in as the seeded demo user
(`demo@spendly.app` / `demo1234`, `database/db.py:86-90`).

## Evidence

Assignment rows are quoted requirements. Repo rows are where the derived design
comes from.

| Requirement | Source |
|---|---|
| GET `/profile`, logged-in only, redirect to `/login` when not authenticated | assignment — Routes |
| Guard reads `session.get("user_id")`, redirects with `url_for("login")` | assignment — Rules |
| Four sections: user card, summary stats, transaction table, category breakdown | assignment — Templates |
| User card shows avatar initials, name, email, member-since | assignment — Templates |
| Stat row shows total spent, transaction count, top category | assignment — Templates, DoD |
| Table rows carry date, description, category badge, amount; ≥ 3 rows | assignment — Templates, DoD |
| Category breakdown shows ≥ 3 categories as a list or progress-bar rows | assignment — Templates, DoD |
| All template data is hardcoded Python dicts/lists in `app.py` | assignment — Rules |
| No inline styles; no hex values in `profile.html`; CSS variables only | assignment — Rules, DoD |
| Category badges use a CSS class, not an inline colour | assignment — Rules |
| Navbar shows the signed-in state — username plus a logout link | assignment — DoD |
| `profile.html` extends `base.html` | assignment — Rules; `templates/base.html:29` |
| The session key the guard reads is `user_id`, an INTEGER | `app.py:46-47` |
| `/login` must be pointed back at `/profile` in this step | `app.py:48-50`, `tests/test_auth.py:47-48` |
| Stat-tile markup and styling already exist and should be reused | `templates/landing.html:38-54`, `static/css/landing.css:203-239` |
| Progress-bar rows already exist and should be reused | `templates/landing.html:56-75`, `static/css/landing.css:244-281` |
| Card idiom is white on `--paper`, 1px `--border`, `--radius-md` | `static/css/style.css:317`, `:405`, `:541` |
| Design tokens to use instead of literals | `static/css/style.css:5-30` |
| Page-specific CSS is linked from `{% block head %}` | `templates/landing.html:5-7`, `templates/base.html:11` |
| User fields available to show: username, email, created_at | `database/db.py:24-30`; `templates/privacy.html:23` |
| Expense fields available per row: amount, category, date, description | `database/db.py:32-40`; `templates/privacy.html:25` |
| Categories are exactly Food, Travel, Bills, Other | `database/db.py:21`, `database/db.py:36` |
| Currency is INR, displayed with a thousands separator | `templates/landing.html:41` |
| The navbar is currently hard-coded to the signed-out state | `templates/base.html:21-24` |
| Nav links that are not `.nav-cta` are hidden below 600px | `static/css/style.css:599` |

## Decisions

### The navbar conflict

`.claude/specs/03-login-and-logout.md` assigns the `{% if session.user_id %}`
branch in `base.html` to Step 5, and CLAUDE.md's step table agrees. **The
assignment's definition of done pulls it into Step 4** — "the navbar shows the
logged-in state (username + logout link)". The assignment wins; Step 4 edits
`base.html:21-24`.

That is not a violation of the repo's "never edit a template to match a route"
rule. That rule protects the *form-field interface* in `register.html` and
`login.html` — field names the routes must map to. `base.html`'s navbar is not
an interface to anything; it is hard-coded to one of two states and always had
to gain the branch.

**The username in the navbar comes from `session["username"]`, set in
`/login`.** `base.html` renders on every page and has no context of its own, so
the only globals available to it are `session` and `request`. The alternatives
are worse: a `context_processor` that looks the user up would put a DB query in
a step whose rules forbid them, and passing the name from `/profile` alone
would leave the navbar nameless on every other page.

Cost, stated plainly: this adds one line to `/login` — a Step 3 route — and
puts a *copy* of the username in the session cookie. The copy goes stale if a
later step lets a user rename themselves; whatever route does that must rewrite
`session["username"]` too. `session.clear()` on logout (`app.py:71`) already
discards it, so nothing leaks across users.

**The logout link needs `.nav-cta`.** `static/css/style.css:599` hides
`.nav-links a:not(.nav-cta)` below 600px, so a logout link added as a plain
anchor is invisible on a phone — the one page where a user most wants it. Give
it `.nav-cta`, or add a rule to the Navbar section of `style.css`. This was
already flagged in `03-login-and-logout.md`.

### The category colours are trapped in `landing.css`

The obvious move — copy the `.preview-bar-row` / `.preview-fill` markup from
`templates/landing.html:56-75` — **renders transparent bars on `/profile`**.
`.fill-food`, `.fill-travel`, and `.fill-bills` resolve `--hero-food`,
`--hero-travel`, and `--hero-bills` (`static/css/landing.css:279-281`), and
those tokens are defined in `landing.css:9-19`, which only `landing.html` loads
(`landing.html:5-7`). On any other page they are undefined.

**Decision: promote category colours into `:root` in `style.css`** as
`--cat-food`, `--cat-travel`, `--cat-bills`, `--cat-other`, plus `--cat-track`
for the empty bar, using the same values `landing.css` already picked.

Cost: the same four colours are now defined twice, once as `--hero-*` in
`landing.css` and once as `--cat-*` in `style.css`, and they can drift.
Collapsing `landing.css` onto the new tokens is a three-line change but touches
a file this step has no business in; leave it, and note the debt.

**`Other` has no colour anywhere.** The schema has four categories
(`database/db.py:21`) and the landing mockup charts three
(`templates/landing.html:56-75`). `--cat-other` is genuinely new. Use
`--ink-muted` — a neutral grey reads correctly for a catch-all bucket and adds
no fifth hue to a palette that already carries `--accent`, `--accent-2`, and
`--danger`.

### Badges and bar widths versus "no inline styles"

Badges are easy and the assignment already specifies them: one class per
category, `.cat-food` / `.cat-travel` / `.cat-bills` / `.cat-other`, each
setting `background` and `color` from the tokens above.

Bar widths are not. `templates/landing.html:60` sets width with
`style="width: 72%"` — exactly what the rules forbid. **Decision: width step
classes** — `.pct-0`, `.pct-5`, … `.pct-100` in 5% increments, generated once
in `profile.css`, with the route rounding each percentage to the nearest step.

This works only because the data is hardcoded. **It does not survive Step 5**,
where percentages are computed from real sums and cannot be enumerated — that
step will need `style="--fill: {{ pct }}%"` on the fill element, which is an
inline style by the letter of the rule even though it carries data, not
design. Flagging rather than hiding it: either the rule means "no inline
*design*", in which case Step 5 is fine and Step 4 could have skipped the step
classes, or it is literal, in which case Step 5 needs a different mechanism.
This is worth resolving with whoever wrote the rule before Step 5 starts.

The 5% rounding also visibly lies for small categories: anything under 2.5% of
the total renders as a zero-width bar.

### Page CSS goes in a new `static/css/profile.css`

Linked from `{% block head %}`, following the `landing.html:5-7` model that
CLAUDE.md names as the convention. The alternative — a "Profile page" banner
section in `style.css` — would load the page's grid, table, and badge rules on
the landing and legal pages that never use them.

Cost: unlike `landing.css`, `profile.css` overrides nothing; it is all new
rules. It is a page stylesheet by convention, not by necessity.

### Hardcoded data must be shaped like the future query result

The highest-value constraint in this step. Each transaction dict uses **exactly
the column names `sqlite3.Row` will hand back** — `id`, `date`, `description`,
`category`, `amount` — with `date` as ISO `YYYY-MM-DD` text and `amount` as a
`REAL` number of rupees, matching `database/db.py:32-40`. Then Step 5 replaces
the literal list with a `SELECT` and the template does not change.

Cost: the fixtures are more verbose than the page strictly needs, and they must
be kept in sync with the schema by hand until Step 5 deletes them.

### Money is formatted in the template, not in Python

The route passes raw numbers; the template renders
`₹{{ "{:,.0f}".format(total) }}`, matching `₹18,240` at
`templates/landing.html:41`. Formatting in `app.py` would mean Step 5 has to
re-do it after swapping in real sums.

Cost: Python's `,` grouping is Western, so a lakh renders `₹1,82,400` in Indian
convention but `₹182,400` here. Acceptable for a teaching scaffold; a real INR
app needs a Jinja filter.

### The guard has no `next=` parameter

An unauthenticated visitor to `/profile` is redirected to `/login` and, after
signing in, lands on `/profile` anyway — because this step points the login
redirect there (`app.py:48-50`). A general `?next=` mechanism would need
open-redirect validation for a case that does not yet arise.

### "Budget left" is dropped from the stat row

The landing mockup's middle tile is `Budget left / ₹6,760 / 43% remaining`
(`templates/landing.html:44-48`). **There is no budget column in the schema**
(`database/db.py:24-40`) and no step in CLAUDE.md's table adds one, so nothing
in Step 5 could ever compute it. The assignment's trio — total spent,
transaction count, top category — is used instead, and all three are derivable
from `expenses` alone.

## Route contract — `app.py`

| Route | Method | Behaviour |
|---|---|---|
| `/profile` | GET | `session.get("user_id")` absent → `redirect(url_for("login"))`, 302. Present → render `profile.html` at 200 with the hardcoded context below. The session value is *checked but not used* this step; it is not looked up in the database. |
| `/login` | POST | Unchanged except the success redirect: `url_for("landing")` becomes `url_for("profile")` (`app.py:48-50`), and `session["username"] = user["username"]` is set alongside `session["user_id"]`. The `SELECT` at `app.py:37-39` grows a `username` column. |

### Template context

| Key | Type | Notes |
|---|---|---|
| `user` | dict | `username`, `email`, `initials`, `member_since` |
| `stats` | dict | `total_spent` (float), `transaction_count` (int), `top_category` (str) |
| `transactions` | list[dict] | `id`, `date` (ISO), `description`, `category`, `amount` — newest first |
| `breakdown` | list[dict] | `category`, `total` (float), `pct` (int, already rounded to a 5% step) |

`initials` is computed from the name in the route (`"Yash Agarwal"` → `"YA"`),
not in the template, so Step 5 changes one line rather than a Jinja expression.

`breakdown` covers all four categories including zero-total ones, so the
section always renders four rows and the layout does not jump when a category
is empty. Percentages are of the **total spent**, not of the largest category —
the four therefore sum to 100 and the section reads as a composition.

Use `database/db.py:86-107` as the source of the hardcoded values so the page
looks the same before and after Step 5 wires the seeded demo user in.

## Wiring

**`app.py`** — replace the placeholder at `app.py:75-77`; add `session` usage
(already imported, `app.py:3`); repoint the login redirect at `app.py:50`; add
`username` to the login `SELECT` and the session write at `app.py:37-47`.

**`templates/base.html`** — the navbar branch, replacing `base.html:21-24`:

```jinja
<div class="nav-links">
    {% if session.user_id %}
        <a href="{{ url_for('profile') }}">{{ session.username }}</a>
        <a href="{{ url_for('logout') }}" class="nav-cta">Log out</a>
    {% else %}
        <a href="{{ url_for('login') }}">Sign in</a>
        <a href="{{ url_for('register') }}" class="nav-cta">Get started</a>
    {% endif %}
</div>
```

This changes every page at once. Check the landing, login, register, terms, and
privacy pages after the edit, not just `/profile`.

**`templates/profile.html`** — new. Extends `base.html`, links `profile.css`
from `{% block head %}`, fills `{% block content %}` with the four sections.
Wrap the transaction table in `{% if transactions %}` with an empty-state
`{% else %}` branch **now**, even though the hardcoded list is never empty, so
Step 5 does not have to restructure the section for a brand-new user with no
expenses.

**`static/css/style.css`** — five new tokens in the `:root` block at
`style.css:5-30`; a logout-link rule in the Navbar section if `.nav-cta` is not
used. Nothing else.

**`static/css/profile.css`** — new. Organised into banner-comment sections
matching the house style: `/* --- Profile header --- */`,
`/* --- Summary stats --- */`, `/* --- Transaction table --- */`,
`/* --- Category breakdown --- */`, `/* --- Responsive --- */`.

## Known mismatch for Step 5

- **Every number on the page is a lie.** The stats, the table, and the
  breakdown are literals in `app.py` and do not reflect the signed-in user.
  Two different users see identical figures. This is intended and is the whole
  point of the step, but the page must not ship past Step 5 in this state.
- **`session["user_id"]` is checked and then ignored.** The guard proves a
  session exists; nothing scopes data to it. `terms.html:33` ("attempt to
  access another user's account or expense data") is not yet enforced by
  anything, because there is no data access to scope.
- **The width step classes do not survive.** Real percentages cannot be
  enumerated as classes — see [Decisions](#badges-and-bar-widths-versus-no-inline-styles).
  Resolve the "no inline styles" rule against `style="--fill: N%"` before
  Step 5 starts.
- **`--hero-*` and `--cat-*` now hold the same four colours in two files.**
  Whoever next edits `landing.css` should collapse it onto the `--cat-*`
  tokens.
- **`tests/test_auth.py:47-48` asserts the login redirect is `/`** and carries
  a comment saying to flip it to `/profile` when Step 4 lands. It must be
  flipped in this step or the suite fails.
- **Registration is still a placeholder** (`app.py:26-28`), so the signed-in
  navbar and the profile page can only be seen as the demo user until Step 2
  is done.

## Commands

```bash
source venv/bin/activate
python app.py                 # http://localhost:5001/login
```

Sign in as `demo@spendly.app` / `demo1234` — after this step, login lands on
`/profile` directly.

Verify without a browser:

```bash
pytest tests/test_auth.py -v          # the redirect assertion must be updated
pytest tests/test_profile.py -v       # new; does not exist yet
```

`tests/test_profile.py` should take the `client` and `demo` fixtures from
`tests/conftest.py` and cover the definition of done:

- `GET /profile` signed out → 302 to `/login`
- `GET /profile` with `session["user_id"]` set → 200
- the response body contains the user card's name and email
- the response body contains three stat values
- the response contains at least three transaction rows
- the response contains four category breakdown rows
- a signed-in `GET /` renders a logout link (the `base.html` branch)
- `profile.html` contains no `#` hex literal and no `style=` attribute

The last one is a grep, not a request — assert against the template file so it
stays true regardless of what the route passes:

```bash
grep -nE '#[0-9a-fA-F]{3,6}\b|style="' templates/profile.html    # must print nothing
```
