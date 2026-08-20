"""Mechanical checks for claim support, provenance, and contradictions."""

from __future__ import annotations

from institutional_investment_agents.retrieval import tokenize
from institutional_investment_agents.schemas import ClaimType, ResearchState, VerificationResult


def _evidence_entails_terms(claim_text: str, evidence_text: str) -> bool:
    claim_tokens = set(tokenize(claim_text)) - {
        "the",
        "a",
        "an",
        "is",
        "was",
        "of",
        "and",
        "to",
        "with",
        "at",
        "for",
        "its",
    }
    evidence_tokens = set(tokenize(evidence_text))
    if not claim_tokens:
        return False
    return len(claim_tokens & evidence_tokens) / len(claim_tokens) >= 0.25


def verify_state(state: ResearchState) -> VerificationResult:
    unsupported: list[str] = []
    missing_ids: set[str] = set()
    valid_citations = 0
    total_citations = 0
    claims_with_valid_support = 0

    for claim in state.claims.values():
        claim_supported = False
        for evidence_id in claim.evidence_ids:
            total_citations += 1
            evidence = state.evidence.get(evidence_id)
            if evidence is None:
                missing_ids.add(evidence_id)
            elif _evidence_entails_terms(claim.text, evidence.text):
                valid_citations += 1
                claim_supported = True
        for result_id in claim.tool_result_ids:
            if result_id in state.tool_results:
                claim_supported = True
            else:
                missing_ids.add(result_id)
        if claim.claim_type in {ClaimType.INFERRED, ClaimType.JUDGMENT} and claim.evidence_ids:
            claim_supported = True
        if claim_supported:
            claims_with_valid_support += 1
        else:
            unsupported.append(claim.id)

    claim_count = len(state.claims)
    evidence_used = {item for claim in state.claims.values() for item in claim.evidence_ids}
    evidence_coverage = len(evidence_used) / len(state.evidence) if state.evidence else 0.0
    support_rate = claims_with_valid_support / claim_count if claim_count else 0.0
    citation_validity = valid_citations / total_citations if total_citations else 1.0
    notes: list[str] = []
    if unsupported:
        notes.append(
            "Unsupported claims require evidence, a traced calculation, or lower confidence."
        )
    if state.contradictions:
        notes.append("Contradictions remain visible and unresolved.")
    return VerificationResult(
        valid=not unsupported and not missing_ids and not state.contradictions,
        claim_support_rate=round(support_rate, 4),
        citation_validity=round(citation_validity, 4),
        evidence_coverage=round(evidence_coverage, 4),
        unsupported_claim_ids=tuple(unsupported),
        missing_evidence_ids=tuple(sorted(missing_ids)),
        unresolved_contradictions=len(state.contradictions),
        notes=tuple(notes),
    )
