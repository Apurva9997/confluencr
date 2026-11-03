# Transaction webhook service

Python service for the Confluencr full-stack assessment. It accepts a payment webhook, returns 202, and finishes the transaction in the background.

Public API: http://13.202.16.144:8000

Swagger UI: http://13.202.16.144:8000/docs

## Why this stack

FastAPI returns the 202 before the background task runs, so the 30-second wait never sits in the request. Piccolo is the table and the migration command (`piccolo migrations forwards app`), so a reviewer can create the schema from the repo without a second tool. Postgres is Supabase, in `ap-south-1`. The deployed box is IPv4-only, so it uses the session pooler rather than the IPv6 direct host. One shared connection pool stays under that pooler's 15-client cap, which is what keeps a burst of webhooks from being dropped.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set DATABASE_URL, then create the table
piccolo migrations forwards app
uvicorn app.main:app --reload
```

Swagger UI is at http://127.0.0.1:8000/docs. The raw spec is at http://127.0.0.1:8000/openapi.json.

## Deploy

The service runs as its own Docker Compose project, `confluencr`, on the existing host. It does not join the other stacks. Put the env file at `/etc/confluencr.env` (mode 600), then:

```bash
docker compose up -d --build
```

## Test

```bash
pytest
```

`PROCESS_DELAY_SECONDS` is 30 in `.env.example`. Tests set it to 0 so the suite does not wait.
