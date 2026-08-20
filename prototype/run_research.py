"""Command-line entry point for the Agentic Fixed-Income Research Workbench."""

import argparse
import json
from pathlib import Path

from institutional_investment_agents.workflow import ResearchWorkbench, WorkflowConfig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issuer", nargs="?", default="NRT", help="synthetic issuer ID")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run = ResearchWorkbench(WorkflowConfig(seed=args.seed)).run(args.issuer.upper())
    payload = {
        "memo": run.memo.model_dump(mode="json"),
        "metrics": run.metrics,
        "audit": [event.model_dump(mode="json") for event in run.state.audit],
    }
    rendered = json.dumps(payload, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n")
        print(f"wrote {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
