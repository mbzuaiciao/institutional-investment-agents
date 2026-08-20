"""Deterministic, financially coherent synthetic credit-research universe."""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from institutional_investment_agents.schemas import EvidenceItem

DATASET_VERSION = "synthetic-credit-v1"


@dataclass(frozen=True)
class IssuerRecord:
    issuer_id: str
    name: str
    sector: str
    rating: str
    revenue_bn: float
    debt_bn: float
    cash_bn: float
    ebitda_bn: float
    ebitda_margin: float
    free_cash_flow_bn: float
    leverage: float
    interest_coverage: float
    earnings_trend: float
    bond_maturity_years: float
    bond_yield: float
    benchmark_yield: float
    spread_bps: float
    cds_bps: float
    spread_duration: float
    historical_spread_mean: float
    historical_spread_std: float
    expected_direction: str
    true_risks: tuple[str, ...]


@dataclass(frozen=True)
class SyntheticUniverse:
    version: str
    seed: int
    issuers: tuple[IssuerRecord, ...]
    documents: tuple[EvidenceItem, ...]
    macro: dict[str, float]

    def issuer(self, issuer_id: str) -> IssuerRecord:
        for item in self.issuers:
            if item.issuer_id == issuer_id:
                return item
        raise KeyError(f"unknown issuer: {issuer_id}")


BASE_ISSUERS = (
    ("NRT", "Northstar Telecom", "telecom", "BBB-", 12.4, 9.3, 1.1, 2.35, 0.19, 0.62, -0.04),
    ("ALP", "Alpine Utilities", "utilities", "BBB+", 8.1, 6.0, 0.8, 2.10, 0.26, 0.34, 0.03),
    ("CRH", "Cedar Retail Holdings", "retail", "BB+", 15.3, 7.4, 0.6, 1.72, 0.11, 0.18, -0.08),
    ("MTR", "MetroRail Leasing", "industrials", "BBB", 6.8, 5.1, 0.9, 1.61, 0.24, 0.41, 0.01),
    ("VTX", "Vertex Software", "technology", "A-", 10.2, 2.2, 2.9, 3.06, 0.30, 1.12, 0.09),
    ("HRB", "Harbor Energy", "energy", "BBB-", 18.0, 8.6, 1.7, 4.12, 0.23, 1.03, -0.02),
    ("SLV", "Silverline Healthcare", "healthcare", "BBB", 9.4, 5.0, 1.2, 2.02, 0.21, 0.57, 0.05),
    ("PNC", "Pine Consumer Products", "consumer", "BBB+", 11.1, 4.3, 0.7, 2.31, 0.21, 0.71, 0.02),
    ("GRD", "GridWorks Infrastructure", "utilities", "A-", 7.7, 5.5, 1.0, 2.48, 0.32, 0.48, 0.04),
    ("BAY", "Bayview REIT", "real_estate", "BBB-", 5.9, 5.7, 0.5, 1.55, 0.26, 0.25, -0.05),
)

RATING_BASE_SPREAD = {"A-": 82.0, "BBB+": 105.0, "BBB": 128.0, "BBB-": 158.0, "BB+": 215.0}


def generate_universe(seed: int = 17) -> SyntheticUniverse:
    """Generate the same coherent universe for a given seed, without network data."""
    rng = random.Random(seed)
    benchmark = 0.041 + rng.uniform(-0.0015, 0.0015)
    issuers: list[IssuerRecord] = []
    documents: list[EvidenceItem] = []
    for index, row in enumerate(BASE_ISSUERS, start=1):
        issuer_id, name, sector, rating, revenue, debt, cash, ebitda, margin, fcf, trend = row
        leverage = debt / ebitda
        interest_cost = debt * (benchmark + RATING_BASE_SPREAD[rating] / 10_000)
        coverage = ebitda / interest_cost
        stress = max(0.0, leverage - 3.0) * 18 + max(0.0, -trend) * 180
        spread = RATING_BASE_SPREAD[rating] + stress + rng.uniform(-12, 12)
        cds = spread + rng.uniform(-10, 14)
        hist_mean = RATING_BASE_SPREAD[rating] + (8 if sector in {"retail", "real_estate"} else 0)
        hist_std = 26 + rng.uniform(-4, 5)
        direction = (
            "attractive"
            if spread > hist_mean + 0.30 * hist_std and coverage > 3.0
            else "unattractive"
        )
        risks = ["refinancing"]
        if leverage > 3.2:
            risks.append("leverage")
        if trend < 0:
            risks.append("earnings_deterioration")
        if sector in {"real_estate", "utilities"}:
            risks.append("rates_sensitivity")
        if sector in {"retail", "consumer"}:
            risks.append("demand_slowdown")
        issuer = IssuerRecord(
            issuer_id=issuer_id,
            name=name,
            sector=sector,
            rating=rating,
            revenue_bn=revenue,
            debt_bn=debt,
            cash_bn=cash,
            ebitda_bn=ebitda,
            ebitda_margin=margin,
            free_cash_flow_bn=fcf,
            leverage=round(leverage, 3),
            interest_coverage=round(coverage, 3),
            earnings_trend=trend,
            bond_maturity_years=round(4.4 + rng.uniform(0, 1.2), 2),
            bond_yield=round(benchmark + spread / 10_000, 5),
            benchmark_yield=round(benchmark, 5),
            spread_bps=round(spread, 1),
            cds_bps=round(cds, 1),
            spread_duration=round(4.0 + rng.uniform(0.1, 0.8), 2),
            historical_spread_mean=round(hist_mean, 1),
            historical_spread_std=round(hist_std, 1),
            expected_direction=direction,
            true_risks=tuple(risks),
        )
        issuers.append(issuer)
        documents.extend(_issuer_documents(issuer, index))
    macro = {
        "policy_rate": round(benchmark + 0.009, 4),
        "five_year_rate": round(benchmark, 4),
        "unemployment": 0.044,
        "base_default_rate": 0.019,
        "recession_probability": 0.27,
    }
    documents.extend(_macro_documents(macro))
    return SyntheticUniverse(DATASET_VERSION, seed, tuple(issuers), tuple(documents), macro)


def _issuer_documents(issuer: IssuerRecord, index: int) -> list[EvidenceItem]:
    trend_word = "declined" if issuer.earnings_trend < 0 else "grew"
    fundamentals = EvidenceItem(
        id=f"ev-{issuer.issuer_id.lower()}-fund",
        source="synthetic issuer filing",
        title=f"{issuer.name} annual credit summary",
        text=(
            f"{issuer.name} reported revenue of ${issuer.revenue_bn:.1f}bn, EBITDA of "
            f"${issuer.ebitda_bn:.2f}bn, debt of ${issuer.debt_bn:.1f}bn and cash of "
            f"${issuer.cash_bn:.1f}bn. EBITDA {trend_word} {abs(issuer.earnings_trend):.0%} year on year. "
            f"Free cash flow was ${issuer.free_cash_flow_bn:.2f}bn."
        ),
        locator=f"filing-{index}:credit-metrics",
        issuer_id=issuer.issuer_id,
        published_date="2026-03-31",
        tags=("fundamentals", "liquidity", "earnings"),
    )
    market = EvidenceItem(
        id=f"ev-{issuer.issuer_id.lower()}-market",
        source="synthetic evaluated pricing",
        title=f"{issuer.name} five-year market snapshot",
        text=(
            f"The five-year bond yielded {issuer.bond_yield:.3%} against a benchmark yield of "
            f"{issuer.benchmark_yield:.3%}, an evaluated spread of {issuer.spread_bps:.1f}bp. "
            f"Five-year CDS was {issuer.cds_bps:.1f}bp and rating was {issuer.rating}."
        ),
        locator=f"pricing-{index}:5y",
        issuer_id=issuer.issuer_id,
        published_date="2026-06-30",
        tags=("market", "spread", "cds", "rating"),
    )
    event_text = (
        "Management announced debt-funded capital spending while demand softened."
        if issuer.earnings_trend < 0
        else "Management reiterated leverage discipline and plans to fund capital spending internally."
    )
    event = EvidenceItem(
        id=f"ev-{issuer.issuer_id.lower()}-event",
        source="synthetic newswire",
        title=f"{issuer.name} corporate update",
        text=event_text,
        locator=f"news-{index}:1",
        issuer_id=issuer.issuer_id,
        published_date="2026-07-15",
        tags=("event", "risk", "capital_allocation"),
    )
    return [fundamentals, market, event]


def _macro_documents(macro: dict[str, float]) -> list[EvidenceItem]:
    return [
        EvidenceItem(
            id="ev-macro-base",
            source="synthetic macro committee",
            title="Base macro scenario",
            text=(
                f"The five-year rate is {macro['five_year_rate']:.2%}; recession probability is "
                f"{macro['recession_probability']:.0%}. Refinancing conditions remain restrictive, "
                "especially for leveraged BBB and high-yield issuers."
            ),
            locator="macro-2026q2:base",
            published_date="2026-06-30",
            tags=("macro", "rates", "refinancing"),
        )
    ]


def export_universe(path: Path, seed: int = 17) -> None:
    universe = generate_universe(seed)
    payload = {
        "version": universe.version,
        "seed": universe.seed,
        "macro": universe.macro,
        "issuers": [asdict(item) for item in universe.issuers],
        "documents": [item.model_dump(mode="json") for item in universe.documents],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
