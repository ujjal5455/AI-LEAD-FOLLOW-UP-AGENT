# AI Lead Follow-Up Agent

Small businesses lose revenue because leads aren't answered quickly, qualified properly, or
followed up consistently. This product fixes that with an AI sales assistant that:

1. **Captures** every lead that messages the business (WhatsApp first, other channels later)
2. **Responds** within seconds, using only facts the business has configured
3. **Qualifies** the lead naturally: what they need, budget, location, timeline
4. **Scores** the lead transparently (you can see *why* a lead scored 87)
5. **Follows up** when a promising lead goes quiet, a limited number of times, in business hours
6. **Hands off** to the owner when a human is needed (hot lead, complaint, custom pricing…)

The first target customers are high-ticket, appointment-driven local businesses: interior
designers, renovation companies, clinics, coaching institutes, real estate.

> **Status: Milestone 1 of 8 complete**: project foundation, database schema, and secure
> login. See [the roadmap](#roadmap). Background: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md);
> concepts explained for learners: [docs/LEARNING_NOTES.md](docs/LEARNING_NOTES.md).

---

## Architecture

```text
 Browser (Next.js dashboard)
    │  calls /api/* on the same site · session in an httpOnly cookie
    ▼
 Next.js server ──forwards /api/*──►  FastAPI backend  ──►  PostgreSQL
                                      │
                                      ├─ auth + tenant isolation (every query scoped to one business)
                                      ├─ channel adapters (simulator now, WhatsApp later)
                                      ├─ AI lead agent (OpenAI), which only *proposes* actions
                                      ├─ tools layer: validates and executes those actions
                                      └─ follow-up worker (sends due follow-ups)
```

**The key rule:** the AI decides *what* should happen ("book an appointment"); ordinary,
tested backend code decides *whether it is allowed* and does it. The AI never writes to the
database directly.

## Tech stack

| Part | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic |
| Database | PostgreSQL (Supabase in the cloud, a local server for development) |
| Auth | Argon2 password hashing, signed JWT in an httpOnly cookie |
| AI (Milestone 3) | OpenAI Responses API with structured outputs and tool calling |
| Tooling | `uv` (Python packages), `npm`, `pytest`, `ruff`, `eslint` |

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py            # creates the FastAPI app
│   │   ├── api/               # HTTP layer: routes + shared dependencies (auth, tenant)
│   │   ├── core/              # settings, database, security, logging, middleware
│   │   ├── models/            # database tables (SQLAlchemy)
│   │   ├── schemas/           # request/response shapes (Pydantic)
│   │   └── services/          # business logic, independent of HTTP
│   ├── alembic/versions/      # database migrations (schema history)
│   ├── scripts/local_db.py    # run PostgreSQL locally without Docker
│   ├── tests/                 # pytest suite (runs against real PostgreSQL)
│   ├── .env.example           # backend configuration template
│   └── pyproject.toml         # Python dependencies
├── frontend/
│   ├── app/                   # pages (Next.js App Router)
│   │   ├── (auth)/            # /login, /register
│   │   └── (dashboard)/       # /dashboard (login required)
│   ├── components/            # UI building blocks
│   ├── lib/                   # session check (server) and API client (browser)
│   ├── types/                 # TypeScript types for API data
│   └── .env.example           # frontend configuration template
├── docs/                      # architecture decisions and learning notes
└── docker-compose.yml         # optional: PostgreSQL via Docker
```

Folders such as `agents/`, `tools/`, `channels/` and `workers/` will be added in the
milestones that need them.

## Environment variables

Each app has its own `.env` file because they are deployed separately.

**`backend/.env`** (copy from `backend/.env.example`)

| Variable | Purpose |
|---|---|
| `APP_ENV` | `development`, `test` or `production`. Production turns on secure cookies and hides API docs. |
| `DATABASE_URL` | PostgreSQL connection URL. |
| `JWT_SECRET` | Signs login tokens. **At least 32 random characters. Keep it secret.** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | How long a login lasts (default 7 days). |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | AI configuration (used from Milestone 3). |
| `WHATSAPP_*` | WhatsApp Cloud API credentials (used from Milestone 8). |

**`frontend/.env.local`** (optional, copy from `frontend/.env.example`)

| Variable | Purpose |
|---|---|
| `BACKEND_URL` | Where the FastAPI backend runs. Default `http://localhost:8000`. Server-side only. |

Never commit `.env` files; they're in `.gitignore`. Only the `.env.example` templates are committed.

## Local setup

**Prerequisites:** [Python 3.12+](https://www.python.org/), [uv](https://docs.astral.sh/uv/),
[Node.js 20+](https://nodejs.org/). Docker is *not* required.

### 1. Backend configuration

```bash
cd backend
uv sync                      # creates .venv and installs dependencies
cp .env.example .env         # on Windows PowerShell: Copy-Item .env.example .env
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the printed value after `JWT_SECRET=` in `backend/.env`.

### 2. Database

**Option A: local PostgreSQL, no Docker (recommended to start):**

```bash
cd backend
uv run python scripts/local_db.py start    # also: stop | status | psql
```

This runs a real PostgreSQL 16 bundled with the `pgserver` Python package, storing data in
`backend/.localdb/`. The default `DATABASE_URL` in `.env.example` already points at it.

**Option B: Docker:** `docker compose up -d` from the project root (same URL).

**Option C: Supabase:**
1. Create a project at [supabase.com](https://supabase.com).
2. Open **Connect**, copy the **Session pooler** connection string, and put it in
   `DATABASE_URL`. Use the pooler, not "Direct connection": direct connections need IPv6,
   which many home networks lack.

Then create the tables. Run this once, and again whenever a new migration is added:

```bash
cd backend
uv run alembic upgrade head
```

### 3. Run the backend

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

- Health check: <http://localhost:8000/api/health>
- Interactive API docs: <http://localhost:8000/docs>. You can try every endpoint from
  here. After calling `/api/auth/login`, the browser keeps the session cookie, so the other
  endpoints work too.

### 4. Run the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000>, create an account, and you'll land on the dashboard.

## Testing

```bash
cd backend
uv run pytest            # 42 tests, against a real temporary PostgreSQL
uv run ruff check .      # lint
uv run ruff format .     # auto-format

cd ../frontend
npm run lint
npm run build            # also type-checks
```

The backend tests start their **own temporary PostgreSQL** and delete it afterwards, so they
never touch your development data. To use a specific database instead, set
`TEST_DATABASE_URL`. Its name must contain `test`, because the tests wipe it.

The tests cover: registration and login, password hashing, session tokens (tampered,
forged, expired), rate limiting, **tenant isolation** (one business can never be linked to
another's data), database constraints, migrations (up, down, and in sync with the models),
and safe error responses.

## Mock conversation mode

*Arrives in Milestone 7.* A built-in simulator where you type as a customer and watch the
assistant reply, qualify, score and create follow-ups, with no WhatsApp account needed.
It's also how the product gets demoed to prospective clients.

## AI configuration

*Arrives in Milestone 3.* The model is set with `OPENAI_MODEL` (default `gpt-6-astra`). Before
that milestone, the model name and API usage will be checked against OpenAI's current
documentation. Business facts (services, prices, hours) live in the database, never in
prompts, so the AI can only repeat what the owner has configured.

## Deployment

*Detailed in Milestone 8.* The intended setup:

- **Database:** Supabase (run `uv run alembic upgrade head` against it).
- **Backend:** any Python host (Render, Railway, Fly.io…). Start command:
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set `APP_ENV=production` and all
  secrets as environment variables.
- **Frontend:** Vercel or similar, with `BACKEND_URL` pointing at the deployed backend.

## Roadmap

| # | Milestone | Status |
|---|---|---|
| 1 | Project structure, database, configuration, authentication | ✅ Done |
| 2 | Business profile, lead CRUD, conversation CRUD, demo business | Next |
| 3 | OpenAI integration, agent instructions, structured extraction, tool calling | |
| 4 | Lead qualification, scoring with explanations, human handoff | |
| 5 | Follow-up engine: scheduling, business hours, stop conditions | |
| 6 | Dashboard: overview, leads table, lead profile, conversation view | |
| 7 | Conversation simulator, webhook architecture | |
| 8 | Real WhatsApp integration, deployment, security hardening | |

**After the MVP:** Instagram, website chat, email, Google Calendar, CRM integrations,
multi-language, analytics, team accounts, subscription billing, white-label for agencies.
