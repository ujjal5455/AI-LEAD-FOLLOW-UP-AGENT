# Architecture & decisions

This file records **what** we're building and **why** each major decision was made, so
future changes can be judged against the original reasoning.

## MVP definition

The MVP is done when all of these work locally, with no real WhatsApp credentials:

1. Create a business → 2. configure its services and rules → 3. simulate a customer
message → 4. AI responds → 5. asks useful qualification questions → 6. extracts lead data
→ 7. saves the lead → 8. scores it → 9. stores the conversation → 10. schedules a
follow-up → 11. cancels it when the customer replies → 12. hot lead triggers an owner
notification → 13. human handoff stops AI replies → 14. dashboard shows the lead →
15. all of it without WhatsApp.

Out of scope for the MVP: billing, team accounts, calendar sync, multi-language tuning,
advanced analytics.

## System overview

```text
 Browser (Next.js)
    │  same-origin /api/*  (httpOnly session cookie)
    ▼
 Next.js server ──rewrite /api/*──►  FastAPI
                                      │
   Channel adapters ──► unified inbound message
   (Simulator · WhatsApp later)        │
                                      ▼
                  Message pipeline: dedupe → find/create lead → store message
                                      │  (stops if opted out / human handoff)
                                      ▼
                  Lead agent (OpenAI Responses API) → proposes tool calls
                                      ▼
                  Tools layer: validate → execute (update_lead, create_followup,
                                handoff_to_human, book_appointment, mark_opted_out…)
                                      ▼
                  Deterministic rules: scoring, status transitions, stop conditions
                                      ▼
                  Follow-up worker (polls due follow-ups; Postgres is the queue)
                                      ▼
                                 PostgreSQL
```

## Decisions

| Decision | Why |
|---|---|
| **AI proposes, backend decides.** The model returns tool calls; server code validates and executes them. | Deterministic, testable, safe. The AI can't book an unavailable slot or edit another tenant's data. |
| **Business facts live in the database**, not in prompts or code. | The AI repeats configured facts instead of inventing them; each business edits its own. |
| **Own auth (Argon2 + JWT in httpOnly cookie)** rather than Supabase Auth. | One place enforces both "who are you" and "which business's data can you see". Works identically locally and in the cloud. |
| **Next.js proxies `/api/*` to FastAPI.** | Browser only talks to one origin: cookies are first-party, no CORS configuration, backend URL is never exposed. |
| **UUID primary keys.** | IDs can't be guessed or enumerated (`/leads/1`, `/leads/2`…). |
| **Composite foreign keys `(business_id, lead_id)`.** | The database itself guarantees a conversation, follow-up or appointment belongs to the same business as its lead. A second line of defence behind the API's tenant scoping. |
| **Enums stored as text + CHECK constraints**, not native PG enums. | Easy to evolve with a migration; the database still rejects invalid values. |
| **Row Level Security enabled with no policies.** | Supabase exposes `public` tables via its REST API; this blocks that route. The backend connects as table owner, which RLS doesn't restrict. |
| **Postgres as the job queue** for follow-ups (`SELECT … FOR UPDATE SKIP LOCKED`). | No Redis/Celery to run or pay for until volume demands it. |
| **One business per owner** (unique `owner_id`) for now. | Simplest correct tenancy. Team accounts / agencies later via a memberships table. |
| **In-memory login rate limiter.** | Enough for one backend instance. Move to Postgres/Redis if we scale horizontally. |
| **Real PostgreSQL in tests** (temporary server via `pgserver`). | SQLite behaves differently (time zones, constraints); tests must match production. |

## Database schema (Milestone 1)

```text
users ─1:1─ businesses ─1:N─ leads ─┬─1:N─ conversations ─1:N─ messages
                                    ├─1:N─ followups
                                    └─1:N─ appointments
```

| Table | Purpose / notable columns |
|---|---|
| `users` | Login accounts. `email` unique and lowercase; `password_hash` (Argon2). |
| `businesses` | Tenants. `owner_id` (unique), `timezone`, and JSON config: `business_hours`, `services`, `service_area`, `pricing_information`; `ai_instructions`. |
| `leads` | `status`, `score` (0–100) + `score_breakdown` (the *why*), qualification fields (`service_interest`, `budget`, `location`, `urgency`, `timeline`, `requirements`, `availability`, `purchase_intent`), `summary`. Phone unique per business. |
| `conversations` | One thread per lead per channel. `status`: `active` / `human_handoff` / `closed`. |
| `messages` | `sender_type` (customer / ai / human / system), `content`, `metadata`, `external_id` (provider message ID, unique per business, so duplicate webhooks can't create duplicate replies). |
| `followups` | `scheduled_at`, `status`, `attempt_number`, `cancel_reason`. **At most one pending follow-up per lead** (partial unique index). |
| `appointments` | `scheduled_at`, `duration_minutes`, `status`, `notes`. |

Planned additions: `agent_events` (AI calls, tool calls, token usage, for observability
and cost tracking; Milestone 3), `notifications` (owner alerts; Milestone 4).

### Deviations from the original spec

- `messages.message` is named `content`, and `messages` also carries `business_id` so every
  tenant table can be filtered directly.
- Separate `backend/.env.example` and `frontend/.env.example` (deployed separately).
- `NEXT_PUBLIC_API_URL` → server-only `BACKEND_URL` (`NEXT_PUBLIC_*` values are visible
  to every browser; with the proxy the browser doesn't need the backend URL at all).
- `pyproject.toml` (managed by `uv`) instead of `requirements.txt`.

## Milestones

1. **Foundation**: structure, FastAPI, Next.js, database + migrations, config, auth ✅
2. Business profile, lead CRUD, conversation CRUD, demo data (ABC Interiors)
3. OpenAI integration: layered prompts, structured extraction, tool calling, event log
4. Qualification rules, transparent scoring, status rules, human handoff, notifications
5. Follow-up engine: delays, business hours, timezone, max attempts, stop conditions
6. Dashboard: overview metrics, leads table, lead profile, conversation view, settings
7. Simulator (mock channel) + webhook architecture with idempotency
8. WhatsApp Cloud API, deployment, security hardening

## Security checklist (living)

- [x] Secrets only from environment; `.env` git-ignored; startup fails on weak `JWT_SECRET`
- [x] Argon2 password hashing; constant-time-ish login for unknown emails
- [x] httpOnly + SameSite=Lax session cookie; `Secure` in production
- [x] Login and sign-up rate limiting
- [x] Tenant scoping via `CurrentBusiness` dependency + composite FKs in the database
- [x] Input validation on every request (Pydantic); length limits on all text
- [x] Safe 500 responses (no internals) with a request ID for support
- [x] Request IDs in logs; no request bodies or emails logged
- [x] RLS enabled (blocks Supabase's auto-generated REST API)
- [ ] Prompt-injection defences & AI action validation (M3–M4)
- [ ] Webhook signature verification (M7–M8)
- [ ] Idempotent message processing (schema ready: `messages.external_id`; logic in M7)
- [ ] Production hardening review (M8)
