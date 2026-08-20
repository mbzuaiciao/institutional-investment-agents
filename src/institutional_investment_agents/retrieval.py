"""Small deterministic lexical retriever with stable evidence provenance."""

from __future__ import annotations

import re
from collections import Counter

from institutional_investment_agents.schemas import EvidenceItem


def tokenize(text: str) -> Counter[str]:
    return Counter(re.findall(r"[a-z0-9]+", text.lower()))


class LocalRetriever:
    def __init__(self, documents: tuple[EvidenceItem, ...] | list[EvidenceItem]) -> None:
        ids = [item.id for item in documents]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence IDs must be unique")
        self.documents = tuple(documents)

    def search(
        self, query: str, *, issuer_id: str | None = None, limit: int = 4
    ) -> list[EvidenceItem]:
        query_tokens = tokenize(query)
        scored: list[tuple[float, EvidenceItem]] = []
        for document in self.documents:
            if issuer_id is not None and document.issuer_id not in {issuer_id, None}:
                continue
            document_tokens = tokenize(
                f"{document.title} {document.text} {' '.join(document.tags)}"
            )
            overlap = sum(
                min(count, document_tokens[token]) for token, count in query_tokens.items()
            )
            issuer_bonus = 2.0 if issuer_id is not None and document.issuer_id == issuer_id else 0.0
            scored.append((overlap + issuer_bonus, document))
        scored.sort(key=lambda pair: (-pair[0], pair[1].id))
        return [document for score, document in scored[:limit] if score > 0]
