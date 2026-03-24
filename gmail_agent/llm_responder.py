from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponder:
    api_key: str
    model: str

    def reply(self, *, question: str, matched_answer: str | None, score: float, threshold: float) -> str:
        """
        Drafts a helpful reply. If we have a confident match, use it as the factual source.
        If we don't, ask for clarification rather than hallucinating.
        """
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "OPENAI_API_KEY is set but the 'openai' package is not installed. "
                "Install dependencies with: pip install -r requirements.txt"
            ) from e

        client = OpenAI(api_key=self.api_key)

        system = (
            "You are an email assistant for an event organizer. "
            "Keep replies short, friendly, and actionable. "
            "Do not invent facts. If the provided Q&A doesn't answer the question, ask a brief follow-up question "
            "or say the organizer will follow up."
        )

        if matched_answer and score >= threshold:
            user = (
                "Reply to the attendee using ONLY the information in the provided Q&A answer.\n\n"
                f"Attendee question:\n{question}\n\n"
                f"Q&A answer:\n{matched_answer}\n"
            )
        else:
            user = (
                "The knowledge base did not confidently match the attendee question.\n"
                "Reply asking for the minimal clarification needed, or say the organizer will follow up soon.\n\n"
                f"Attendee question:\n{question}\n"
            )

        resp = client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        text = (resp.output_text or "").strip()
        return text or "Thanks for your question. The event organizer will reach you as soon as possible."

