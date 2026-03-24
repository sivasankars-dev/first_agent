from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class QnA:
    question: str
    answer: str


class QnAStore:
    def __init__(self, items):
        self._items = items
        self._vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        corpus = [f"{i.question}\n{i.answer}" for i in items]
        self._matrix = self._vectorizer.fit_transform(corpus) if items else None

    @staticmethod
    def from_markdown(path: Path) -> "QnAStore":
        text = path.read_text(encoding="utf-8")
        items: list[QnA] = []

        q: str | None = None
        a_lines: list[str] = []

        for line in text.splitlines():
            m_q = re.match(r"^\s*Q\s*[:\-]\s*(.+)\s*$", line, re.IGNORECASE)
            m_a = re.match(r"^\s*A\s*[:\-]\s*(.*)\s*$", line, re.IGNORECASE)
            if m_q:
                if q and a_lines:
                    items.append(QnA(question=q.strip(), answer="\n".join(a_lines).strip()))
                q = m_q.group(1)
                a_lines = []
                continue
            if m_a:
                a_lines.append(m_a.group(1))
                continue
            if q and a_lines is not None:
                if line.strip() == "" and a_lines:
                    a_lines.append("")
                elif a_lines:
                    a_lines.append(line)

        if q and a_lines:
            items.append(QnA(question=q.strip(), answer="\n".join(a_lines).strip()))

        return QnAStore(items)

    def answer(self, user_question: str) -> tuple[str, float]:
        if not self._items or self._matrix is None:
            return ("I don't have the event Q&A loaded yet.", 0.0)
        vec = self._vectorizer.transform([user_question])
        sims = cosine_similarity(vec, self._matrix)[0]
        best_idx = int(sims.argmax())
        score = float(sims[best_idx])
        best = self._items[best_idx]
        return (best.answer, score)
