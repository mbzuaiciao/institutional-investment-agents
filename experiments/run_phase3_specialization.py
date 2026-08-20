"""Plan the matched-call-budget specialist decomposition replication."""

from __future__ import annotations

import sys

from institutional_investment_agents.phase3_runner import run_cli

if __name__ == "__main__":
    arguments = sys.argv[1:] or ["--preset", "smoke", "--dry-run"]
    raise SystemExit(run_cli("specialization", arguments))
