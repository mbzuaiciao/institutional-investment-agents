"""Tutorial 04: deterministic tools own arithmetic and preserve validated inputs."""

from institutional_investment_agents.tools import ToolRegistry


def main() -> None:
    tools = ToolRegistry()
    value, units = tools.execute(
        "credit_ratios", {"debt": 9.3, "cash": 1.1, "ebitda": 2.35, "interest_expense": 0.50}
    )
    print(value, units)
    impact, units = tools.execute(
        "portfolio_impact",
        {
            "market_value": 10_000_000,
            "spread_duration": 4.4,
            "rate_duration": 4.2,
            "spread_change_bps": 75,
            "rate_change_bps": -25,
        },
    )
    print(impact, units)


if __name__ == "__main__":
    main()
