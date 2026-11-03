# Transaction webhook service

Python service for the Confluencr full-stack assessment. It accepts a payment webhook, returns 202, and finishes the transaction in the background.

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
