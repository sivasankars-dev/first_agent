import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    token_path: Path
    credentials_path: Path
    qna_path: Path
    poll_seconds: int
    reply_subject_prefix: str
    allowed_senders: tuple[str, ...]
    match_threshold: float
    openai_api_key: str | None
    openai_model: str


def load_settings() -> Settings:
    # Best-effort local .env support for `python -m gmail_agent.worker`.
    # In Docker, environment variables are typically injected by `docker compose`.
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()
    except Exception:
        pass

    token_path = Path(os.environ.get("GMAIL_TOKEN_PATH", "token.json"))
    credentials_path = Path(os.environ.get("GMAIL_CREDENTIALS_PATH", "credentials.json"))
    qna_path = Path(os.environ.get("QNA_PATH", "data/event_qna.md"))
    poll_seconds = int(os.environ.get("POLL_SECONDS", "10"))
    reply_subject_prefix = os.environ.get("REPLY_SUBJECT_PREFIX", "Re:")
    match_threshold = float(os.environ.get("MATCH_THRESHOLD", "0.30"))
    openai_api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("openai_api_key")
    openai_model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    allowed_raw = os.environ.get("ALLOWED_SENDERS") or os.environ.get("ALLOWED_SENDER") or ""
    allowed_senders: list[str] = []
    if allowed_raw.strip():
        for part in allowed_raw.split(","):
            addr = part.strip().lower()
            if addr:
                allowed_senders.append(addr)

    return Settings(
        token_path=token_path,
        credentials_path=credentials_path,
        qna_path=qna_path,
        poll_seconds=poll_seconds,
        reply_subject_prefix=reply_subject_prefix,
        allowed_senders=tuple(dict.fromkeys(allowed_senders)),
        match_threshold=match_threshold,
        openai_api_key=openai_api_key.strip() if openai_api_key and openai_api_key.strip() else None,
        openai_model=openai_model,
    )
