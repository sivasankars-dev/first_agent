from __future__ import annotations

import base64
from typing import Any, Optional


def _decode_base64url(data: str) -> str:
    raw = base64.urlsafe_b64decode(data.encode("utf-8"))
    try:
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return raw.decode(errors="replace")


def get_header(headers: list[dict[str, str]], name: str) -> Optional[str]:
    name_lower = name.lower()
    for h in headers:
        if h.get("name", "").lower() == name_lower:
            return h.get("value")
    return None


def extract_best_text(message: dict[str, Any]) -> str:
    payload = message.get("payload") or {}
    if not payload:
        return ""

    def walk(part: dict[str, Any]) -> list[tuple[str, str]]:
        mime = (part.get("mimeType") or "").lower()
        body = part.get("body") or {}
        data = body.get("data")
        out: list[tuple[str, str]] = []
        if data:
            out.append((mime, _decode_base64url(data)))
        for child in part.get("parts") or []:
            out.extend(walk(child))
        return out

    parts = walk(payload)
    for preferred in ("text/plain", "text/html"):
        for mime, text in parts:
            if mime == preferred and text.strip():
                return text.strip()
    for _, text in parts:
        if text.strip():
            return text.strip()
    snippet = message.get("snippet") or ""
    return snippet.strip()


def extract_user_question(text: str) -> str:
    """
    Best-effort extraction of the *new* user question from an email body.
    - Removes quoted replies (lines starting with '>').
    - Stops at common reply/forward markers (e.g. "On ... wrote:", "From:", "-----Original Message-----").
    """
    if not text:
        return ""

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cleaned: list[str] = []
    stop_markers = (
        "-----original message-----",
        "---------- forwarded message ---------",
    )

    for raw in lines:
        line = raw.rstrip()
        low = line.strip().lower()

        if not low:
            cleaned.append("")
            continue

        if low.startswith(">"):
            continue

        if low.startswith("on ") and " wrote:" in low:
            break

        if low.startswith("from:") or low.startswith("sent:") or low.startswith("to:") or low.startswith("subject:"):
            break

        if any(m in low for m in stop_markers):
            break

        cleaned.append(line)

    out = "\n".join(cleaned).strip()
    # collapse excessive blank lines
    while "\n\n\n" in out:
        out = out.replace("\n\n\n", "\n\n")
    return out
