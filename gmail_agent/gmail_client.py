from __future__ import annotations

import base64
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


READ_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
MODIFY_SCOPE = "https://www.googleapis.com/auth/gmail.modify"


@dataclass
class GmailClient:
    service: Any

    @staticmethod
    def from_token_file(token_path: str, scopes: list[str]) -> "GmailClient":
        creds = Credentials.from_authorized_user_file(token_path, scopes)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        return GmailClient(service=service)

    def list_unread(self, max_results: int = 10, query: Optional[str] = None) -> list[dict[str, Any]]:
        q = "is:unread"
        if query:
            q = f"{q} ({query})"
        results = (
            self.service.users()
            .messages()
            .list(userId="me", q=q, maxResults=max_results)
            .execute()
        )
        return results.get("messages", []) or []

    def get_message(self, msg_id: str) -> dict[str, Any]:
        return (
            self.service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )

    def send_email(self, to_addr: str, subject: str, body: str, in_reply_to: str | None = None) -> None:
        message = EmailMessage()
        message["To"] = to_addr
        message["Subject"] = subject
        if in_reply_to:
            message["In-Reply-To"] = in_reply_to
            message["References"] = in_reply_to
        message.set_content(body)

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        (
            self.service.users()
            .messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )

    def mark_as_read(self, msg_id: str) -> None:
        (
            self.service.users()
            .messages()
            .modify(userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]})
            .execute()
        )
