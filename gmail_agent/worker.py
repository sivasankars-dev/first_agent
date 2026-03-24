from __future__ import annotations

import time
from email.utils import parseaddr

from gmail_agent.config import load_settings
from gmail_agent.gmail_client import GmailClient, MODIFY_SCOPE, READ_SCOPE, SEND_SCOPE
from gmail_agent.llm_responder import LLMResponder
from gmail_agent.message_parse import extract_best_text, extract_user_question, get_header
from gmail_agent.qna_store import QnAStore


def main():
    settings = load_settings()
    store = QnAStore.from_markdown(settings.qna_path)
    llm = (
        LLMResponder(api_key=settings.openai_api_key, model=settings.openai_model)
        if settings.openai_api_key
        else None
    )
    if settings.allowed_senders:
        print(f"Allowed senders: {', '.join(settings.allowed_senders)}")
    else:
        print("Allowed senders: (not set) -> replying to any unread sender")
    if llm:
        print(f"LLM replies: enabled (model={settings.openai_model})")
    else:
        print("LLM replies: disabled (set OPENAI_API_KEY to enable)")

    gmail = GmailClient.from_token_file(
        str(settings.token_path),
        scopes=[READ_SCOPE, SEND_SCOPE, MODIFY_SCOPE],
    )

    while True:
        query = None
        if settings.allowed_senders:
            query = " OR ".join([f"from:{a}" for a in settings.allowed_senders])
        messages = gmail.list_unread(max_results=10, query=query)
        for m in messages:
            msg_id = m["id"]
            full = gmail.get_message(msg_id)

            headers = (full.get("payload") or {}).get("headers") or []
            from_raw = get_header(headers, "From") or ""
            from_addr = parseaddr(from_raw)[1].strip().lower()
            subject = get_header(headers, "Subject") or "(no subject)"
            message_id = get_header(headers, "Message-Id")

            if settings.allowed_senders and (not from_addr or from_addr not in settings.allowed_senders):
                print(f"Skipping {msg_id} from {from_addr or from_raw} (not allowed)")
                continue

            body = extract_best_text(full)
            question = extract_user_question(body)
            answer, score = store.answer(question or body)

            if llm:
                reply = llm.reply(
                    question=(question or body).strip(),
                    matched_answer=answer,
                    score=score,
                    threshold=settings.match_threshold,
                )
            else:
                reply = answer
                if score < settings.match_threshold:
                    reply = "Thanks for your question. The event organizer will reach you as soon as possible."

            gmail.send_email(
                to_addr=from_addr,
                subject=f"{settings.reply_subject_prefix} {subject}",
                body=reply,
                in_reply_to=message_id,
            )
            gmail.mark_as_read(msg_id)
            print(f"Replied to {msg_id} (score={score:.3f})")

        time.sleep(settings.poll_seconds)


if __name__ == "__main__":
    main()
