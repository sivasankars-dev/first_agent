# gmail-agent (v1)

Goal: an event organizer maintains a single Event Q&A document; when attendees email questions, the agent replies using the best matching Q&A entry.

## Architecture (v1)

- **Q&A knowledge base**: `data/event_qna.md`
  - Simple `Q:` / `A:` markdown format.
  - Loaded into an in-memory TF‑IDF index (no external vector DB).
- **Gmail poller/worker**: `gmail_agent/worker.py`
  - Polls `is:unread` messages on a fixed interval.
  - Extracts best-effort body text.
  - Retrieves best matching Q&A answer and replies.
  - Marks the message as read to avoid double replies.
- **Gmail API client**: `gmail_agent/gmail_client.py`
  - Uses OAuth token from `token.json` (mounted as a secret in Docker).
  - Uses `gmail.modify` so it can remove `UNREAD`.

## Local run

1) Create OAuth token (interactive, on your host machine):

```bash
python gmail_auth.py
```

If you previously created `token.json` without `gmail.modify`, delete it and re-run auth:

```bash
rm -f token.json secrets/token.json
python gmail_auth.py
```

2) Ensure you have a Q&A file:

- Edit `data/event_qna.md`

3) Run the worker:

```bash
pip install -r requirements.txt
python -m gmail_agent.worker
```

## Docker run

1) Put your OAuth files in `./secrets/` (not committed):

- `secrets/token.json`
- `secrets/credentials.json`

If you see a 403 “insufficient authentication scopes”, regenerate `token.json` on your host using `python gmail_auth.py` (it must include `gmail.modify`).

2) Start:

```bash
docker compose up --build
```

Notes:
- `docker compose` reads config from `.env` (this repo includes a non-secret `.env` for convenience). Don’t put secrets in `.env`; keep them as mounted files in `./secrets/`.

## Configuration

Environment variables (see `gmail_agent/config.py`):

- `GMAIL_TOKEN_PATH` (default: `token.json`)
- `GMAIL_CREDENTIALS_PATH` (default: `credentials.json`)
- `QNA_PATH` (default: `data/event_qna.md`)
- `POLL_SECONDS` (default: `10`)
- `REPLY_SUBJECT_PREFIX` (default: `Re:`)
- `ALLOWED_SENDERS` (default: unset; if set, only replies to these sender emails, comma-separated)
- `ALLOWED_SENDER` (legacy alias for a single sender)
- `MATCH_THRESHOLD` (default: `0.30`; raise to reduce irrelevant matches)
- `OPENAI_API_KEY` (optional; if set, drafts replies using OpenAI)
- `OPENAI_MODEL` (default: `gpt-4.1-mini`)

## Next upgrades (v2+)

- Replace TF‑IDF with embeddings + a real vector store.
- Add a small admin UI/API endpoint for uploading the Q&A doc.
- Thread-safe de-duplication (e.g., store replied `Message-Id` in SQLite).
- Better email parsing (strip quoted replies/signatures).
# first_agent
