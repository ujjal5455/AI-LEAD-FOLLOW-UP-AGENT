# Learning notes

Plain-language explanations of the ideas behind this codebase, added milestone by
milestone. Each section points to the code where the idea lives.

---

## Milestone 1: foundation

### What happens when you log in

```text
1. You type email + password on /login               (frontend/components/auth/login-form.tsx)
2. Browser sends POST /api/auth/login to Next.js
3. Next.js forwards it to FastAPI                    (frontend/next.config.ts → rewrites)
4. FastAPI validates the JSON shape                  (backend/app/schemas/auth.py)
5. Looks up the user, checks the password hash       (backend/app/services/auth_service.py)
6. Creates a signed token, puts it in a cookie       (backend/app/api/routes/auth.py)
7. Browser stores the cookie and sends it back automatically on every later request
8. Dashboard page asks the backend "who is this?"    (frontend/lib/session.ts → /api/auth/me)
```

### Password hashing

We never store your password. We store a **hash**: the output of a one-way function
(Argon2). Logging in hashes what you typed and compares the results. If the database
leaked, attackers would get hashes, and Argon2 is deliberately slow to make guessing
expensive. → `backend/app/core/security.py`

### Tokens and cookies

After login the backend creates a **JWT**: a small piece of text saying "this is user
869d8df2…, valid until next week", plus a **signature** made with `JWT_SECRET`. Changing
even one character breaks the signature, so nobody can forge or edit a token without the
secret.

The token goes into an **httpOnly cookie**. The browser sends it automatically, but page
JavaScript can't read it, so if a malicious script ever got onto the page, it still
couldn't steal your login. `SameSite=Lax` stops other websites from triggering requests
that carry your cookie.

### Database relationships, with an example

```text
users            Asha (owner account)
  │ owns 1
businesses       ABC Interiors
  │ has many
leads            Rahul, Priya, Aman…
  │ each has many
conversations    Rahul's WhatsApp chat
  │ has many
messages         "Hi, I need a modular kitchen" …
```

A **foreign key** is a column that points at a row in another table, e.g.
`leads.business_id → businesses.id`. The database refuses a lead whose business doesn't
exist, and **ON DELETE CASCADE** means deleting a business deletes its leads too.

### Tenant isolation: two locks on the door

Each business (a **tenant**) must only ever see its own data.

1. **API lock:** endpoints get the business from your *session*, never from something you
   send (`CurrentBusiness` in `backend/app/api/deps.py`). You can't ask for another
   business's lead by changing an ID in the URL.
2. **Database lock:** conversations point at `(business_id, lead_id)` *together*
   (a composite foreign key). So even if application code had a bug, the database would
   refuse to attach Business B's conversation to Business A's lead.
   → `test_database_rejects_a_conversation_linking_two_businesses` proves it.

### Migrations

A **migration** is a versioned script that changes the database structure ("create table
leads", later "add column x"). `uv run alembic upgrade head` applies every migration that
hasn't run yet. Your laptop, the test database and Supabase all end up with *exactly* the
same structure, and history is kept in git. → `backend/alembic/versions/`

Workflow when a model changes:
```bash
uv run alembic revision --autogenerate -m "describe the change"   # writes a new migration
# read the generated file! autogenerate is a helper, not an oracle
uv run alembic upgrade head
```
(A test fails if a model changes without a matching migration.)

### Environment variables

Settings that differ per machine, or that are secret (database password, API keys), come
from **environment variables**, not code. Locally they're read from `backend/.env`; in the
cloud you set them in the hosting dashboard. The code validates them at startup
(`backend/app/core/config.py`), so a missing secret fails immediately and loudly.

### Rate limiting

After 10 failed logins for one email within 15 minutes, further attempts are refused
(HTTP 429) until the window passes. That makes password guessing impractically slow.
→ `backend/app/core/rate_limit.py`

### Request IDs

Every response carries an `X-Request-ID` header, and every log line for that request
includes the same ID. When something fails, the error shows the ID, and you can search the
logs for it to see exactly what happened. → `backend/app/core/middleware.py`
