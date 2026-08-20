import pytest
from pydantic import ValidationError

from institutional_investment_agents.tools import ToolRegistry


def test_spread_calculation() -> None:
    value, units = ToolRegistry().execute(
        "spread_bps", {"bond_yield": 0.0575, "benchmark_yield": 0.041}
    )
    assert value == 165.0
    assert units == "bps"


def test_credit_ratios() -> None:
    value, _ = ToolRegistry().execute(
        "credit_ratios", {"debt": 8.0, "cash": 2.0, "ebitda": 2.0, "interest_expense": 0.5}
    )
    assert value == {"gross_leverage": 4.0, "net_leverage": 3.0, "interest_coverage": 4.0}


def test_spread_z_score() -> None:
    value, _ = ToolRegistry().execute(
        "spread_z_score", {"value": 150, "mean": 100, "standard_deviation": 25}
    )
    assert isinstance(value, dict)
    assert value["z_score"] == 2.0
    assert value["normal_percentile"] > 0.97


def test_expected_loss() -> None:
    value, _ = ToolRegistry().execute(
        "expected_loss", {"default_probability": 0.02, "recovery_rate": 0.4, "horizon_years": 5}
    )
    assert isinstance(value, float)
    assert 0.057 < value < 0.058


def test_portfolio_impact_signs_and_dv01() -> None:
    value, _ = ToolRegistry().execute(
        "portfolio_impact",
        {
            "market_value": 10_000_000,
            "spread_duration": 4,
            "rate_duration": 3.5,
            "spread_change_bps": 100,
            "rate_change_bps": -25,
        },
    )
    assert isinstance(value, dict)
    assert value["spread_pnl"] == -400_000
    assert value["rate_pnl"] == 87_500
    assert value["dv01"] == 3_500


def test_input_validation() -> None:
    with pytest.raises(ValidationError):
        ToolRegistry().execute(
            "credit_ratios", {"debt": 8, "cash": 1, "ebitda": 0, "interest_expense": 1}
        )


def test_unknown_tool_fails() -> None:
    with pytest.raises(KeyError):
        ToolRegistry().execute("magic", {})
