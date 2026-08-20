"""Tutorial 01: the smallest agent loop is policy + environment + transition + trace."""

from dataclasses import dataclass, field

from institutional_investment_agents.model import DeterministicResearchModel


@dataclass
class LoopState:
    observations: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
    terminated: bool = False


def run_loop() -> LoopState:
    model = DeterministicResearchModel()
    state = LoopState()
    state.trace.append("action: inspect synthetic issuer")
    observation = "Debt is $9.3bn and EBITDA is $2.35bn."
    state.observations.append(observation)
    state.trace.append(f"observation: {observation}")
    state.trace.append(model.generate("Assess leverage", context=tuple(state.observations)))
    state.terminated = True
    state.trace.append("termination: sufficient for minimal demonstration")
    return state


if __name__ == "__main__":
    print("\n".join(run_loop().trace))
