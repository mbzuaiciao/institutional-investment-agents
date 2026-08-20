"""Typed, deterministic financial and portfolio-risk tools."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SpreadInput(ToolInput):
    bond_yield: float = Field(ge=-0.05, le=1.0)
    benchmark_yield: float = Field(ge=-0.05, le=1.0)


class RatiosInput(ToolInput):
    debt: float = Field(gt=0)
    cash: float = Field(ge=0)
    ebitda: float = Field(gt=0)
    interest_expense: float = Field(gt=0)


class PercentileInput(ToolInput):
    value: float
    mean: float
    standard_deviation: float = Field(gt=0)


class ExpectedLossInput(ToolInput):
    default_probability: float = Field(ge=0, le=1)
    recovery_rate: float = Field(ge=0, le=1)
    horizon_years: float = Field(gt=0, le=30)


class PortfolioImpactInput(ToolInput):
    market_value: float = Field(gt=0)
    spread_duration: float = Field(ge=0)
    rate_duration: float = Field(ge=0)
    spread_change_bps: float
    rate_change_bps: float


def spread_bps(data: SpreadInput) -> float:
    return round((data.bond_yield - data.benchmark_yield) * 10_000, 4)


def credit_ratios(data: RatiosInput) -> dict[str, float]:
    return {
        "gross_leverage": round(data.debt / data.ebitda, 4),
        "net_leverage": round((data.debt - data.cash) / data.ebitda, 4),
        "interest_coverage": round(data.ebitda / data.interest_expense, 4),
    }


def spread_z_score(data: PercentileInput) -> dict[str, float]:
    z_score = (data.value - data.mean) / data.standard_deviation
    percentile = 0.5 * (1 + math.erf(z_score / math.sqrt(2)))
    return {"z_score": round(z_score, 4), "normal_percentile": round(percentile, 4)}


def expected_loss(data: ExpectedLossInput) -> float:
    cumulative_pd = 1 - (1 - data.default_probability) ** data.horizon_years
    return round(cumulative_pd * (1 - data.recovery_rate), 6)


def portfolio_impact(data: PortfolioImpactInput) -> dict[str, float]:
    spread_pnl = -data.market_value * data.spread_duration * data.spread_change_bps / 10_000
    rate_pnl = -data.market_value * data.rate_duration * data.rate_change_bps / 10_000
    return {
        "spread_pnl": round(spread_pnl, 2),
        "rate_pnl": round(rate_pnl, 2),
        "total_pnl": round(spread_pnl + rate_pnl, 2),
        "dv01": round(data.market_value * data.rate_duration / 10_000, 2),
    }


ToolFunction = Callable[[Any], float | dict[str, float]]


class ToolRegistry:
    """Contract registry validates inputs before executing financial arithmetic."""

    def __init__(self) -> None:
        self._tools: dict[str, tuple[type[ToolInput], ToolFunction, str]] = {
            "spread_bps": (SpreadInput, spread_bps, "bps"),
            "credit_ratios": (RatiosInput, credit_ratios, "ratio"),
            "spread_z_score": (PercentileInput, spread_z_score, "standard deviations"),
            "expected_loss": (ExpectedLossInput, expected_loss, "fraction of par"),
            "portfolio_impact": (PortfolioImpactInput, portfolio_impact, "currency"),
        }

    def execute(self, name: str, arguments: dict[str, Any]) -> tuple[float | dict[str, float], str]:
        if name not in self._tools:
            raise KeyError(f"unknown tool: {name}")
        input_model, function, units = self._tools[name]
        validated = input_model.model_validate(arguments)
        return function(validated), units

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))
