"""Tutorial 13: inject realistic model failures with a reproducible seed."""

from institutional_investment_agents.phase2_schemas import ModelOperation, ModelRequest
from institutional_investment_agents.stochastic_model import StochasticSyntheticModel


def main() -> None:
    model = StochasticSyntheticModel("weak", seed=7)
    for operation in ModelOperation:
        response = model.execute(
            ModelRequest(
                operation=operation, episode_id="tutorial-13", instruction="Perform the operation."
            )
        )
        failures = [item.failure_type.value for item in response.failures]
        print(f"{operation.value}: {failures or ['no injected failure']}")


if __name__ == "__main__":
    main()
