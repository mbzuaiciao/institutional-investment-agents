# Institutional workflow

## Research is a process

Institutional investment research is not simply a request followed by an answer. It is a controlled sequence of scoping, evidence gathering, calculation, comparison, challenge, and review. The workbench models that sequence for a synthetic five-year corporate-credit question: is an issuer’s credit risk attractive relative to its bond, peers, and macro environment, and under what conditions would the thesis fail?

## Workflow mapping

### 1. Research question formation

`ResearchQuestion` records the issuer, horizon, and analytical objective. Scoping the horizon and relative-value frame prevents the system from substituting a generic company summary for a credit conclusion.

### 2. Planning and task decomposition

The planner creates typed tasks for issuer fundamentals and capital structure, market pricing and peer relative value, macro/rates, and evidence/provenance. The plan makes missing coverage visible and assigns accountable roles. [Tutorial 02](../tutorials/02_structured_research.py) introduces this boundary.

### 3. Issuer fundamentals and capital structure

The credit role examines debt, cash, EBITDA, margin, free cash flow, leverage, interest coverage, earnings direction, and rating risk. These inputs address debt capacity and refinancing headroom. Real analysts would also inspect debt legal entities, covenants, secured priority, maturity ladders, pensions, leases, and off-balance-sheet liabilities; those are outside the synthetic prototype.

### 4. Rates and macro context

The macro/rates role considers the five-year benchmark, recession probability, refinancing conditions, and sector sensitivity. This connects issuer risk to the environment in which debt must be serviced or refinanced. The implementation uses one synthetic macro document rather than a live curve, economic releases, or central-bank scenarios.

### 5. Market pricing and relative value

The relative-value role compares bond spread, CDS, rating context, and the issuer’s synthetic historical spread distribution. A deterministic z-score tool describes spread position. This is intentionally simpler than full bond cash-flow pricing, option-adjusted spread, curve fitting, liquidity adjustment, or a live peer matrix.

### 6. Scenarios and downside analysis

The thesis contains bull, base, and bear scenarios with probabilities, spread moves, rate moves, and default probabilities. Risks have severity and observable triggers. Invalidation conditions—such as EBITDA decline or leverage thresholds—turn the conclusion into a falsifiable hypothesis instead of a static opinion.

### 7. Thesis formation

The synthesizer combines structured claims into a conditional “research conclusion.” It distinguishes attractiveness from issuer quality: compensation must be assessed relative to risk. The output is not an executable recommendation or order instruction.

### 8. Challenge and review

The critic asks whether cheap spread could be cheap for a good reason, whether refinancing and earnings assumptions are fragile, and whether known risks are missing. It records a structured challenge rather than silently rewriting the memo. [Tutorial 08](../tutorials/08_critic_agent.py) shows the resulting object.

### 9. Evidence checking

The verifier checks that factual claims cite evidence, calculated claims cite tool outputs, pointers exist, and contradictions remain visible. It cannot validate live truth or replace analyst judgment. Its function resembles a first-line quality-control check.

### 10. Portfolio impact

The portfolio tool estimates first-order spread and rate P&L and DV01 for a hypothetical position. This extends research beyond standalone issuer commentary, but it is not a portfolio risk engine: it omits nonlinearities, liquidity, correlation, hedges, concentration limits, and mandate constraints.

### 11. Approval

The workflow emits an explicit approve/revise/reject decision with rationale and conditions. The default reviewer is a deterministic policy so experiments remain reproducible. In a real institution, named analysts, portfolio managers, risk officers, or committees would own decisions under formal entitlements and escalation rules.

## Realism and deliberate simplification

The realistic elements are the separation of fundamentals, pricing, macro, downside, evidence, challenge, portfolio sensitivity, and approval; the connection between price and risk; and the preservation of lineage. The simplifications are synthetic data, a small issuer universe, static documents, first-order calculations, deterministic policy, and simulated review.

Those choices make the first phase executable and experimentally controlled. They do not make it production-ready. The relevant gaps are detailed in [limitations](limitations.md), with a staged path forward in [future work](future_work.md).
