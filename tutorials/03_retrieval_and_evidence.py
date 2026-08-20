"""Tutorial 03: retrieval returns evidence objects, not automatically true claims."""

from institutional_investment_agents.dataset import generate_universe
from institutional_investment_agents.retrieval import LocalRetriever


def main() -> None:
    retriever = LocalRetriever(generate_universe().documents)
    for item in retriever.search("Northstar debt EBITDA spread", issuer_id="NRT"):
        print(f"{item.id} | {item.source} | {item.locator}\n  {item.text}")


if __name__ == "__main__":
    main()
