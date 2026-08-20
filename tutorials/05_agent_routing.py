"""Tutorial 05: explicit routing is measurable and replaceable."""

from institutional_investment_agents.routing import route_task


def main() -> None:
    tasks = ("Issuer fundamentals", "Macro and rates", "Peer relative value", "Evidence provenance")
    for task in tasks:
        print(f"{task} -> {route_task(task, task)}")
    print("Naive routing ->", route_task("Macro and rates", "Assess curve", naive=True))


if __name__ == "__main__":
    main()
