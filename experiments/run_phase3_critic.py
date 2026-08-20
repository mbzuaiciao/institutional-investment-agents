"""Plan the paired critic-off/critic-on real-model replication."""

from __future__ import annotations

import sys

from institutional_investment_agents.phase3_runner import run_cli

if __name__ == "__main__":
    arguments = sys.argv[1:] or ["--preset", "smoke", "--dry-run"]
    raise SystemExit(run_cli("critic", arguments))
