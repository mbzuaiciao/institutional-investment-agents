"""Parameterized hard credit-research episodes and explicit evidence freshness logic."""

from __future__ import annotations

import random
from datetime import date

from institutional_investment_agents.phase2_schemas import (
    EvidenceFreshness,
    HardEpisodeFamily,
    HardResearchEpisode,
    VersionedEvidence,
)


def evidence_freshness(
    evidence: VersionedEvidence,
    *,
    as_of_date: str,
    corpus: tuple[VersionedEvidence, ...],
) -> EvidenceFreshness:
    """Classify evidence using explicit validity and supersession metadata."""
    if any(item.supersedes_id == evidence.id for item in corpus):
        return EvidenceFreshness.SUPERSEDED
    if evidence.valid_until and date.fromisoformat(evidence.valid_until) < date.fromisoformat(
        as_of_date
    ):
        return EvidenceFreshness.STALE
    return EvidenceFreshness.CURRENT


def current_evidence(episode: HardResearchEpisode) -> tuple[VersionedEvidence, ...]:
    return tuple(
        item
        for item in episode.evidence
        if evidence_freshness(item, as_of_date=episode.as_of_date, corpus=episode.evidence)
        == EvidenceFreshness.CURRENT
    )


def generate_hard_episode(
    family: HardEpisodeFamily | str,
    *,
    seed: int = 17,
) -> HardResearchEpisode:
    selected = HardEpisodeFamily(family)
    rng = random.Random(f"{selected.value}:{seed}")
    suffix = f"{seed}-{rng.randrange(1000, 9999)}"
    issuer_id = f"P2-{selected.value[:3].upper()}"
    as_of_date = "2026-09-30"
    common_metadata: dict[str, str | int | float | bool] = {
        "issuer_id": issuer_id,
        "as_of_date": as_of_date,
    }
    if selected == HardEpisodeFamily.CONTRADICTORY_EVIDENCE:
        evidence = (
            _evidence(
                suffix, 1, "issuer filing", "Leverage improved from 4.1x to 3.5x.", ("leverage",)
            ),
            _evidence(
                suffix,
                2,
                "cash flow statement",
                "Free cash flow deteriorated to negative $0.3bn.",
                ("cash_flow",),
            ),
            _evidence(
                suffix,
                3,
                "market tape",
                "CDS widened 45bp while the cash bond spread was stable.",
                ("market_divergence",),
            ),
            _evidence(
                suffix,
                4,
                "management guidance",
                "Management expects margins to recover next year.",
                ("guidance",),
            ),
        )
        return HardResearchEpisode(
            id=f"episode-contradiction-{suffix}",
            family=selected,
            evidence=evidence,
            required_risks=("cash_flow", "market_divergence", "guidance_uncertainty"),
            expected_direction="unattractive",
            has_contradiction=True,
            complexity=4,
            metadata={**common_metadata, "signal_count": 4},
            issuer_id=issuer_id,
            as_of_date=as_of_date,
        )
    if selected == HardEpisodeFamily.MISLEADING_CHEAPNESS:
        evidence = (
            _evidence(
                suffix,
                1,
                "pricing",
                "The issuer trades 70bp wider than sector peers.",
                ("cheapness",),
            ),
            _evidence(
                suffix,
                2,
                "debt footnote",
                "A structural subordination change moves collateral away from bondholders.",
                ("structural_subordination",),
            ),
            _evidence(
                suffix,
                3,
                "rating note",
                "The rating outlook is negative due to weak covenant protection.",
                ("downgrade",),
            ),
        )
        return HardResearchEpisode(
            id=f"episode-cheapness-{suffix}",
            family=selected,
            evidence=evidence,
            required_risks=("structural_subordination", "downgrade", "weak_covenants"),
            expected_direction="unattractive",
            complexity=4,
            metadata={**common_metadata, "peer_discount_bps": 70.0},
            issuer_id=issuer_id,
            as_of_date=as_of_date,
        )
    if selected == HardEpisodeFamily.TOOL_NECESSITY:
        evidence = (
            _evidence(
                suffix,
                1,
                "bond terms",
                "Market value is $12m and spread duration is 4.6.",
                ("position",),
            ),
            _evidence(
                suffix,
                2,
                "stress scenario",
                "Spread widens 125bp and rates fall 35bp.",
                ("stress",),
            ),
            _evidence(
                suffix,
                3,
                "risk policy",
                "A scenario loss above $500,000 requires escalation.",
                ("limit",),
            ),
        )
        return HardResearchEpisode(
            id=f"episode-tool-{suffix}",
            family=selected,
            evidence=evidence,
            required_risks=("scenario_loss", "limit_breach"),
            expected_direction="unattractive",
            requires_tool=True,
            complexity=3,
            metadata={**common_metadata, "expected_loss": 621000.0},
            issuer_id=issuer_id,
            as_of_date=as_of_date,
        )
    if selected == HardEpisodeFamily.RETRIEVAL_DISTRACTORS:
        evidence = (
            _evidence(
                suffix,
                1,
                "current filing",
                "Issuer debt rose 18% after an acquisition.",
                ("acquisition_leverage",),
            ),
            _evidence(
                suffix,
                2,
                "unrelated issuer filing",
                "A similarly named issuer reduced debt 18%.",
                (),
                relevant=False,
            ),
            _evidence(
                suffix,
                3,
                "old sector article",
                "Sector leverage was stable five years ago.",
                (),
                relevant=False,
                valid_until="2022-12-31",
            ),
            _evidence(
                suffix,
                4,
                "current pricing",
                "The acquisition bond widened 55bp.",
                ("spread_widening",),
            ),
        )
        return HardResearchEpisode(
            id=f"episode-distractors-{suffix}",
            family=selected,
            evidence=evidence,
            required_risks=("acquisition_leverage", "spread_widening"),
            expected_direction="unattractive",
            complexity=4,
            metadata={**common_metadata, "distractor_count": 2},
            issuer_id=issuer_id,
            as_of_date=as_of_date,
        )
    if selected == HardEpisodeFamily.STALE_EVIDENCE:
        old = _evidence(
            suffix,
            1,
            "2025 filing",
            "Liquidity was strong and leverage was 2.8x.",
            ("strong_liquidity",),
            valid_until="2026-03-31",
        )
        evidence = (
            old,
            _evidence(
                suffix,
                2,
                "2026 filing",
                "Liquidity declined and leverage rose to 4.2x.",
                ("liquidity", "leverage"),
                version=2,
                supersedes_id=old.id,
            ),
            _evidence(
                suffix,
                3,
                "current pricing",
                "Five-year spread widened 90bp after the update.",
                ("spread_widening",),
            ),
        )
        return HardResearchEpisode(
            id=f"episode-stale-{suffix}",
            family=selected,
            evidence=evidence,
            required_risks=("liquidity", "leverage", "spread_widening"),
            expected_direction="unattractive",
            has_contradiction=True,
            complexity=4,
            metadata={**common_metadata, "stale_items": 1},
            issuer_id=issuer_id,
            as_of_date=as_of_date,
        )
    if selected == HardEpisodeFamily.MISSING_DATA:
        evidence = (
            _evidence(
                suffix, 1, "filing", "Debt is $6.2bn; the filing omits segment EBITDA.", ("debt",)
            ),
            _evidence(suffix, 2, "pricing", "The five-year spread is 185bp.", ("spread",)),
        )
        return HardResearchEpisode(
            id=f"episode-missing-{suffix}",
            family=selected,
            evidence=evidence,
            required_risks=("unknown_leverage", "data_gap"),
            expected_direction="unknown",
            missing_fields=("ebitda", "interest_expense"),
            complexity=3,
            metadata=common_metadata,
            issuer_id=issuer_id,
            as_of_date=as_of_date,
        )
    if selected == HardEpisodeFamily.SCENARIO_SENSITIVITY:
        evidence = (
            _evidence(
                suffix,
                1,
                "base case",
                "At unchanged rates the bond offers modest excess spread.",
                ("base_value",),
            ),
            _evidence(
                suffix,
                2,
                "stress",
                "A 100bp spread widening produces a loss larger than two years of carry.",
                ("downside_asymmetry",),
            ),
            _evidence(
                suffix,
                3,
                "rates case",
                "A 75bp rates rise weakens refinancing coverage below 2x.",
                ("rates_sensitivity",),
            ),
        )
        return HardResearchEpisode(
            id=f"episode-scenario-{suffix}",
            family=selected,
            evidence=evidence,
            required_risks=("downside_asymmetry", "rates_sensitivity"),
            expected_direction="unattractive",
            requires_tool=True,
            complexity=4,
            metadata={**common_metadata, "conclusion_reverses": True},
            issuer_id=issuer_id,
            as_of_date=as_of_date,
        )
    if selected == HardEpisodeFamily.FALSE_CORRELATION:
        evidence = (
            _evidence(
                suffix,
                1,
                "market series",
                "Issuer CDS and oil prices moved together for six weeks.",
                ("co_movement",),
            ),
            _evidence(
                suffix,
                2,
                "business mix",
                "Only 2% of issuer revenue is directly linked to oil.",
                ("limited_exposure",),
            ),
            _evidence(
                suffix,
                3,
                "macro note",
                "A common risk-off shock explains both series.",
                ("common_factor",),
            ),
        )
        return HardResearchEpisode(
            id=f"episode-correlation-{suffix}",
            family=selected,
            evidence=evidence,
            required_risks=("false_causality", "common_factor"),
            expected_direction="unknown",
            has_contradiction=True,
            complexity=4,
            metadata=common_metadata,
            issuer_id=issuer_id,
            as_of_date=as_of_date,
        )
    evidence = (
        _evidence(suffix, 1, "filing", "EBITDA is $1.8bn and debt is $7.2bn.", ("leverage_input",)),
        _evidence(
            suffix,
            2,
            "maturity table",
            "Half of debt matures within three years.",
            ("maturity_wall",),
        ),
        _evidence(
            suffix,
            3,
            "macro scenario",
            "Refinancing spreads rise 150bp in recession.",
            ("refinancing_stress",),
        ),
        _evidence(
            suffix,
            4,
            "peer pricing",
            "Peers with lower leverage trade 40bp tighter.",
            ("peer_value",),
        ),
    )
    return HardResearchEpisode(
        id=f"episode-multihop-{suffix}",
        family=selected,
        evidence=evidence,
        required_risks=("leverage", "maturity_wall", "refinancing_stress", "peer_value"),
        expected_direction="unattractive",
        requires_tool=True,
        complexity=5,
        metadata={**common_metadata, "required_hops": 4},
        issuer_id=issuer_id,
        as_of_date=as_of_date,
    )


def generate_hard_suite(seed: int = 17) -> tuple[HardResearchEpisode, ...]:
    return tuple(generate_hard_episode(family, seed=seed) for family in HardEpisodeFamily)


def generate_longitudinal_sequence(seed: int = 17) -> tuple[HardResearchEpisode, ...]:
    """Five dated episodes where prior state can help but may also anchor the model."""
    labels = (
        (
            "initial",
            "2026-01-31",
            "Initial leverage is 3.2x and liquidity is adequate.",
            "attractive",
        ),
        (
            "earnings",
            "2026-04-30",
            "EBITDA falls 12%, breaching the thesis trigger.",
            "unattractive",
        ),
        (
            "rating",
            "2026-06-30",
            "The issuer is downgraded to BBB- with negative outlook.",
            "unattractive",
        ),
        (
            "rates",
            "2026-08-31",
            "A rates shock raises projected refinancing cost by 120bp.",
            "unattractive",
        ),
        (
            "guidance",
            "2026-10-31",
            "New guidance improves cash flow but does not restore prior leverage.",
            "unattractive",
        ),
    )
    sequence: list[HardResearchEpisode] = []
    previous_id: str | None = None
    for index, (label, as_of, text, direction) in enumerate(labels, start=1):
        evidence = VersionedEvidence(
            id=f"long-{seed}-v{index}",
            version=index,
            source=f"synthetic {label} update",
            text=text,
            published_date=as_of,
            valid_until=None if index == len(labels) else labels[index][1],
            supersedes_id=previous_id,
            supports=(label, "thesis_update"),
        )
        sequence.append(
            HardResearchEpisode(
                id=f"longitudinal-{seed}-{index}",
                family=HardEpisodeFamily.STALE_EVIDENCE,
                issuer_id="P2-LONG",
                as_of_date=as_of,
                evidence=(evidence,),
                required_risks=(label,),
                expected_direction=direction,
                has_contradiction=index in {2, 5},
                complexity=min(5, index + 1),
                metadata={"episode_number": index, "event": label},
            )
        )
        previous_id = evidence.id
    return tuple(sequence)


def _evidence(
    suffix: str,
    index: int,
    source: str,
    text: str,
    supports: tuple[str, ...],
    *,
    relevant: bool = True,
    valid_until: str | None = None,
    version: int = 1,
    supersedes_id: str | None = None,
) -> VersionedEvidence:
    return VersionedEvidence(
        id=f"p2-ev-{suffix}-{index}",
        version=version,
        source=source,
        text=text,
        published_date="2026-06-30" if version == 1 else "2026-09-15",
        valid_until=valid_until,
        supersedes_id=supersedes_id,
        relevant=relevant,
        supports=supports,
    )
