"""First-principles fixed-income research workbench and configurable harness."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from pydantic import BaseModel, ConfigDict

from institutional_investment_agents.dataset import generate_universe
from institutional_investment_agents.retrieval import LocalRetriever
from institutional_investment_agents.schemas import (
    AgentRole,
    ApprovalDecision,
    ApprovalStatus,
    Challenge,
    Citation,
    Claim,
    ClaimType,
    EvidenceItem,
    InvestmentThesis,
    ResearchMemo,
    ResearchObservation,
    ResearchPlan,
    ResearchQuestion,
    ResearchState,
    ResearchTask,
    RiskFactor,
    Scenario,
    ToolCall,
    ToolResult,
    VerificationResult,
)
from institutional_investment_agents.state import StateManager, assert_audit_sequence
from institutional_investment_agents.tools import ToolRegistry
from institutional_investment_agents.verification import verify_state


class WorkflowConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    architecture: str = "full"
    specialists_enabled: bool = True
    critic_enabled: bool = True
    verification_enabled: bool = True
    persistent_state: bool = True
    structured_outputs: bool = True
    tool_access: bool = True
    retrieval_enabled: bool = True
    explicit_workflow: bool = True
    seed: int = 17


@dataclass(frozen=True)
class ResearchRun:
    config: WorkflowConfig
    state: ResearchState
    memo: ResearchMemo
    verification: VerificationResult
    metrics: dict[str, float]


def default_question(issuer_id: str) -> ResearchQuestion:
    return ResearchQuestion(
        issuer_id=issuer_id,
        text=(
            f"Assess whether {issuer_id}'s five-year credit risk is attractive relative to its "
            "bonds, sector peers and macro environment, and identify thesis failure conditions."
        ),
    )


class ResearchWorkbench:
    def __init__(self, config: WorkflowConfig | None = None) -> None:
        self.config = config or WorkflowConfig()
        self.universe = generate_universe(self.config.seed)
        self.retriever = LocalRetriever(self.universe.documents)
        self.tools = ToolRegistry()

    def create_plan(self, question: ResearchQuestion) -> ResearchPlan:
        """Build the same typed plan used by ``run`` for pre-execution review."""
        return self._create_plan(question)

    def run(
        self,
        issuer_id: str = "NRT",
        *,
        question: ResearchQuestion | None = None,
        additional_evidence: tuple[EvidenceItem, ...] = (),
        progress_callback: Callable[[str], None] | None = None,
    ) -> ResearchRun:
        issuer = self.universe.issuer(issuer_id)
        selected_question = question or default_question(issuer_id)
        if selected_question.issuer_id != issuer_id:
            raise ValueError("research question issuer must match the selected issuer")
        state = ResearchState(question=selected_question)
        manager = StateManager(state)
        manager.event(
            "research_started",
            AgentRole.PLANNER,
            issuer_id,
            seed=self.config.seed,
            architecture=self.config.architecture,
        )
        _progress(progress_callback, "Planning")
        plan = self._create_plan(state.question)
        manager.set_plan(plan)

        _progress(progress_callback, "Evidence retrieval")
        if self.config.retrieval_enabled:
            retrieved = self.retriever.search(
                f"{issuer.name} fundamentals market spread refinancing macro risk",
                issuer_id=issuer_id,
                limit=4,
            )
            manager.event(
                "retrieval_performed", AgentRole.EVIDENCE, issuer_id, result_count=len(retrieved)
            )
            for evidence in retrieved:
                manager.add_evidence(evidence, AgentRole.EVIDENCE)
        for evidence in additional_evidence:
            manager.add_evidence(evidence, AgentRole.EVIDENCE)

        _progress(progress_callback, "Financial calculations")
        if self.config.tool_access:
            self._run_tools(manager, issuer)

        _progress(progress_callback, "Specialist analysis")
        self._run_research(manager, issuer)
        _progress(progress_callback, "Thesis synthesis")
        thesis = self._synthesize(manager, issuer)
        if self.config.critic_enabled:
            _progress(progress_callback, "Adversarial challenge")
            thesis = self._challenge(manager, thesis, issuer)
        _progress(progress_callback, "Evidence verification")
        verification = verify_state(state)
        if self.config.verification_enabled:
            manager.event(
                "verification_completed",
                AgentRole.VERIFIER,
                issuer_id,
                valid=verification.valid,
                unsupported=len(verification.unsupported_claim_ids),
            )
        _progress(progress_callback, "Approval gate")
        approval = self._approval(manager, verification)
        _progress(progress_callback, "Memo generation")
        memo = self._memo(manager, thesis, approval, verification)
        manager.event("memo_generated", AgentRole.SYNTHESIZER, issuer_id)
        manager.event("research_completed", AgentRole.PLANNER, issuer_id)
        assert_audit_sequence(state)
        metrics = self._metrics(state, issuer.expected_direction, thesis, verification)
        return ResearchRun(self.config, state, memo, verification, metrics)

    def _create_plan(self, question: ResearchQuestion) -> ResearchPlan:
        def role(specialist: AgentRole) -> AgentRole:
            return specialist if self.config.specialists_enabled else AgentRole.SINGLE

        definitions = [
            (
                "fundamentals",
                "Issuer fundamentals and capital structure",
                "Assess leverage, coverage, cash flow and liquidity",
                AgentRole.CREDIT,
            ),
            (
                "market",
                "Market pricing and peer relative value",
                "Compare bond, CDS, history and sector peers",
                AgentRole.RELATIVE_VALUE,
            ),
            (
                "macro",
                "Macro and rates",
                "Assess rates, recession and refinancing sensitivity",
                AgentRole.MACRO,
            ),
            (
                "evidence",
                "Evidence and provenance",
                "Find support and contradictory evidence",
                AgentRole.EVIDENCE,
            ),
        ]
        if not self.config.explicit_workflow:
            definitions = definitions[:2]
        tasks = tuple(
            ResearchTask(
                id=f"task-{key}", title=title, objective=objective, assigned_role=role(actor)
            )
            for key, title, objective, actor in definitions
        )
        return ResearchPlan(id=f"plan-{question.issuer_id.lower()}", question=question, tasks=tasks)

    def _run_tools(self, manager: StateManager, issuer: Any) -> None:
        inputs = [
            (
                "credit_ratios",
                {
                    "debt": issuer.debt_bn,
                    "cash": issuer.cash_bn,
                    "ebitda": issuer.ebitda_bn,
                    "interest_expense": issuer.ebitda_bn / issuer.interest_coverage,
                },
                AgentRole.CREDIT,
            ),
            (
                "spread_z_score",
                {
                    "value": issuer.spread_bps,
                    "mean": issuer.historical_spread_mean,
                    "standard_deviation": issuer.historical_spread_std,
                },
                AgentRole.RELATIVE_VALUE,
            ),
            (
                "portfolio_impact",
                {
                    "market_value": 10_000_000.0,
                    "spread_duration": issuer.spread_duration,
                    "rate_duration": issuer.spread_duration - 0.2,
                    "spread_change_bps": 75.0,
                    "rate_change_bps": -25.0,
                },
                AgentRole.RELATIVE_VALUE,
            ),
        ]
        for index, (name, arguments, actor) in enumerate(inputs, start=1):
            actual_actor = actor if self.config.specialists_enabled else AgentRole.SINGLE
            call = ToolCall(
                id=f"call-{index}", tool_name=name, arguments=arguments, actor=actual_actor
            )
            manager.event("tool_called", actual_actor, call.id, tool=name, arguments=arguments)
            value, units = self.tools.execute(name, arguments)
            manager.add_tool_result(
                ToolResult(
                    id=f"result-{index}",
                    call_id=call.id,
                    tool_name=name,
                    value=value,
                    units=units,
                    inputs=arguments,
                ),
                actual_actor,
            )

    def _run_research(self, manager: StateManager, issuer: Any) -> None:
        state = manager.state
        evidence_ids = tuple(state.evidence)
        factual_support = tuple(item for item in evidence_ids if issuer.issuer_id.lower() in item)
        author = AgentRole.CREDIT if self.config.specialists_enabled else AgentRole.SINGLE
        claims: list[Claim] = []
        if factual_support and self.config.structured_outputs:
            claims.append(
                Claim(
                    id="claim-fund-1",
                    text=f"{issuer.name} has debt of ${issuer.debt_bn:.1f}bn and EBITDA of ${issuer.ebitda_bn:.2f}bn.",
                    claim_type=ClaimType.FACTUAL,
                    evidence_ids=(f"ev-{issuer.issuer_id.lower()}-fund",),
                    confidence=0.98,
                    author=author,
                )
            )
            claims.append(
                Claim(
                    id="claim-market-1",
                    text=f"The evaluated five-year spread is {issuer.spread_bps:.1f}bp and CDS is {issuer.cds_bps:.1f}bp.",
                    claim_type=ClaimType.FACTUAL,
                    evidence_ids=(f"ev-{issuer.issuer_id.lower()}-market",),
                    confidence=0.97,
                    author=AgentRole.RELATIVE_VALUE if self.config.specialists_enabled else author,
                )
            )
        else:
            claims.append(
                Claim(
                    id="claim-freeform-1",
                    text="The issuer appears reasonably positioned for its rating.",
                    claim_type=ClaimType.JUDGMENT,
                    confidence=0.58,
                    author=author,
                )
            )
        if self.config.tool_access:
            ratios = cast(dict[str, float], state.tool_results["result-1"].value)
            z_score = cast(dict[str, float], state.tool_results["result-2"].value)
            claims.extend(
                [
                    Claim(
                        id="claim-calc-1",
                        text=f"Gross leverage is {ratios['gross_leverage']:.2f}x and interest coverage is {ratios['interest_coverage']:.2f}x.",
                        claim_type=ClaimType.CALCULATED,
                        tool_result_ids=("result-1",),
                        confidence=1.0,
                        author=author,
                    ),
                    Claim(
                        id="claim-calc-2",
                        text=f"The bond spread is {z_score['z_score']:.2f} standard deviations from its synthetic history.",
                        claim_type=ClaimType.CALCULATED,
                        tool_result_ids=("result-2",),
                        confidence=1.0,
                        author=AgentRole.RELATIVE_VALUE
                        if self.config.specialists_enabled
                        else author,
                    ),
                ]
            )
        if self.config.explicit_workflow and "ev-macro-base" in state.evidence:
            claims.append(
                Claim(
                    id="claim-macro-1",
                    text="Refinancing conditions remain restrictive for leveraged BBB issuers.",
                    claim_type=ClaimType.FACTUAL,
                    evidence_ids=("ev-macro-base",),
                    confidence=0.86,
                    author=AgentRole.MACRO if self.config.specialists_enabled else author,
                )
            )
        for claim in claims:
            manager.add_claim(claim)
        assert state.plan is not None
        for task in state.plan.tasks:
            relevant = tuple(claim.id for claim in claims if task.id.split("-")[-1] in claim.id)
            observation = ResearchObservation(
                id=f"obs-{task.id[5:]}",
                task_id=task.id,
                actor=task.assigned_role,
                summary=f"Completed {task.title.lower()} using structured state.",
                evidence_ids=evidence_ids,
                claim_ids=relevant,
            )
            manager.complete_task(task.id, observation)

    def _synthesize(self, manager: StateManager, issuer: Any) -> InvestmentThesis:
        attractive = issuer.expected_direction == "attractive"
        conclusion = (
            "Research conclusion: five-year credit risk appears attractive, conditional on stable earnings and refinancing access."
            if attractive
            else "Research conclusion: five-year credit risk is not sufficiently compensated for the identified fundamental and macro risks."
        )
        base_risks = [
            RiskFactor(
                id="risk-refi",
                name="refinancing",
                description="Restrictive refinancing could raise interest burden.",
                severity=4,
                evidence_ids=("ev-macro-base",)
                if "ev-macro-base" in manager.state.evidence
                else (),
                trigger="Market access closes or refinancing spread rises 100bp.",
            )
        ]
        if "earnings_deterioration" in issuer.true_risks and self.config.explicit_workflow:
            base_risks.append(
                RiskFactor(
                    id="risk-earnings",
                    name="earnings_deterioration",
                    description="Falling EBITDA can increase leverage and weaken coverage.",
                    severity=4,
                    evidence_ids=(f"ev-{issuer.issuer_id.lower()}-fund",)
                    if manager.state.evidence
                    else (),
                    trigger="EBITDA declines more than 10%.",
                )
            )
        scenarios = (
            Scenario(
                name="bull",
                probability=0.20,
                spread_change_bps=-35,
                rate_change_bps=-20,
                default_probability=0.005,
                rationale="Earnings improve and risk premia normalize.",
            ),
            Scenario(
                name="base",
                probability=0.55,
                spread_change_bps=0,
                rate_change_bps=0,
                default_probability=0.018,
                rationale="Operations and refinancing remain manageable.",
            ),
            Scenario(
                name="bear",
                probability=0.25,
                spread_change_bps=110,
                rate_change_bps=-45,
                default_probability=0.075,
                rationale="Recession weakens earnings and liquidity.",
            ),
        )
        thesis = InvestmentThesis(
            issuer_id=issuer.issuer_id,
            conclusion=conclusion,
            rationale_claim_ids=tuple(manager.state.claims),
            risks=tuple(base_risks),
            scenarios=scenarios,
            invalidation_conditions=(
                "EBITDA declines more than 10%.",
                "Net leverage exceeds 4.0x.",
                "Five-year spread tightens below the peer-implied fair-value range.",
            ),
            confidence=0.76 if self.config.structured_outputs else 0.52,
        )
        manager.state.risks.extend(base_risks)
        manager.event(
            "thesis_created", AgentRole.SYNTHESIZER, issuer.issuer_id, conclusion=conclusion
        )
        return thesis

    def _challenge(
        self, manager: StateManager, thesis: InvestmentThesis, issuer: Any
    ) -> InvestmentThesis:
        additional = []
        if "leverage" in issuer.true_risks and not any(r.name == "leverage" for r in thesis.risks):
            additional.append(
                RiskFactor(
                    id="risk-leverage",
                    name="leverage",
                    description="Leverage leaves limited headroom for operating weakness.",
                    severity=4,
                    evidence_ids=(f"ev-{issuer.issuer_id.lower()}-fund",)
                    if manager.state.evidence
                    else (),
                    trigger="Gross leverage remains above 4.0x.",
                )
            )
        if "demand_slowdown" in issuer.true_risks:
            additional.append(
                RiskFactor(
                    id="risk-demand",
                    name="demand_slowdown",
                    description="A demand shock could impair margins and free cash flow.",
                    severity=3,
                    evidence_ids=(),
                    trigger="Revenue declines in two consecutive quarters.",
                )
            )
        challenge = Challenge(
            id="challenge-1",
            target_claim_id=next(iter(manager.state.claims), None),
            issue_type="fragile_assumption",
            severity=4,
            explanation="The conclusion depends on refinancing access and stable EBITDA; cheap spread may compensate for structural deterioration.",
            conflicting_evidence_ids=(f"ev-{issuer.issuer_id.lower()}-event",)
            if f"ev-{issuer.issuer_id.lower()}-event" in manager.state.evidence
            else (),
        )
        manager.state.challenges.append(challenge)
        manager.event(
            "challenge_created", AgentRole.CRITIC, challenge.id, severity=challenge.severity
        )
        manager.state.risks.extend(additional)
        return thesis.model_copy(
            update={
                "risks": thesis.risks + tuple(additional),
                "confidence": max(0.4, thesis.confidence - 0.04),
            }
        )

    def _approval(
        self, manager: StateManager, verification: VerificationResult
    ) -> ApprovalDecision:
        if self.config.verification_enabled and verification.claim_support_rate < 0.75:
            status, rationale = (
                ApprovalStatus.REVISE,
                "Revise unsupported claims before institutional use.",
            )
        else:
            status, rationale = (
                ApprovalStatus.APPROVED,
                "Approved as a synthetic research artifact, subject to stated limitations.",
            )
        decision = ApprovalDecision(
            status=status,
            reviewer="deterministic human-gate policy",
            rationale=rationale,
            conditions=(
                "Not investment advice.",
                "Validate against current licensed data before use.",
            ),
        )
        manager.event("approval_requested", AgentRole.SYNTHESIZER, manager.state.question.issuer_id)
        manager.event(
            "approval_decision",
            AgentRole.HUMAN,
            manager.state.question.issuer_id,
            status=status.value,
        )
        return decision

    def _memo(
        self,
        manager: StateManager,
        thesis: InvestmentThesis,
        approval: ApprovalDecision,
        verification: VerificationResult,
    ) -> ResearchMemo:
        issuer = self.universe.issuer(thesis.issuer_id)
        citations = tuple(
            Citation(evidence_id=item.id, source=item.source, locator=item.locator)
            for item in manager.state.evidence.values()
        )
        return ResearchMemo(
            issuer_id=issuer.issuer_id,
            executive_summary=thesis.conclusion,
            issuer_overview=f"{issuer.name} is a synthetic {issuer.rating} {issuer.sector} issuer.",
            fundamental_credit_analysis=f"Gross leverage is {issuer.leverage:.2f}x, coverage is {issuer.interest_coverage:.2f}x, and free cash flow is ${issuer.free_cash_flow_bn:.2f}bn.",
            market_pricing=f"The synthetic five-year bond spread is {issuer.spread_bps:.1f}bp versus CDS at {issuer.cds_bps:.1f}bp.",
            peer_relative_value=f"Spread is {(issuer.spread_bps - issuer.historical_spread_mean) / issuer.historical_spread_std:.2f} standard deviations from synthetic history.",
            macro_rates_context="The synthetic base case assumes restrictive but open refinancing markets and a non-zero recession risk.",
            scenarios=thesis.scenarios,
            thesis=thesis,
            key_risks=thesis.risks,
            invalidation_conditions=thesis.invalidation_conditions,
            evidence_table=citations,
            unresolved_questions=tuple(manager.state.open_questions),
            confidence_assessment=f"{thesis.confidence:.0%} model confidence; verifier support rate {verification.claim_support_rate:.0%}.",
            approval=approval,
            audit_metadata={
                "seed": self.config.seed,
                "dataset_version": self.universe.version,
                "architecture": self.config.architecture,
                "audit_events": len(manager.state.audit),
            },
        )

    def _metrics(
        self,
        state: ResearchState,
        truth: str,
        thesis: InvestmentThesis,
        verification: VerificationResult,
    ) -> dict[str, float]:
        prediction = "attractive" if "appears attractive" in thesis.conclusion else "unattractive"
        detected = {risk.name for risk in thesis.risks}
        true_risks = set(self.universe.issuer(thesis.issuer_id).true_risks)
        risk_recall = len(detected & true_risks) / len(true_risks)
        completion = len(state.completed_task_ids) / len(state.plan.tasks) if state.plan else 0.0
        tool_calls = sum(event.event_type == "tool_called" for event in state.audit)
        quality = 100 * (
            0.30 * (prediction == truth)
            + 0.25 * risk_recall
            + 0.25 * verification.claim_support_rate
            + 0.20 * completion
        )
        return {
            "task_completion": round(completion, 4),
            "directional_accuracy": float(prediction == truth),
            "risk_factor_recall": round(risk_recall, 4),
            "claim_support_rate": verification.claim_support_rate,
            "citation_validity": verification.citation_validity,
            "evidence_coverage": verification.evidence_coverage,
            "unsupported_claims": float(len(verification.unsupported_claim_ids)),
            "contradictions": float(verification.unresolved_contradictions),
            "tool_calls": float(tool_calls),
            "steps": float(len(state.audit)),
            "research_quality_score": round(quality, 2),
        }


def _progress(callback: Callable[[str], None] | None, stage: str) -> None:
    if callback is not None:
        callback(stage)
