"""Deterministic specialist routing policies."""

from __future__ import annotations

from institutional_investment_agents.schemas import AgentRole, ResearchTask

ROUTING_RULES = {
    "fundamental": AgentRole.CREDIT,
    "capital": AgentRole.CREDIT,
    "macro": AgentRole.MACRO,
    "rates": AgentRole.MACRO,
    "peer": AgentRole.RELATIVE_VALUE,
    "relative": AgentRole.RELATIVE_VALUE,
    "evidence": AgentRole.EVIDENCE,
    "provenance": AgentRole.EVIDENCE,
}


def route_task(title: str, objective: str, *, naive: bool = False) -> AgentRole:
    if naive:
        return AgentRole.SINGLE
    text = f"{title} {objective}".lower()
    for keyword, role in ROUTING_RULES.items():
        if keyword in text:
            return role
    return AgentRole.CREDIT


def routing_accuracy(tasks: tuple[ResearchTask, ...]) -> float:
    if not tasks:
        return 1.0
    correct = sum(route_task(task.title, task.objective) == task.assigned_role for task in tasks)
    return correct / len(tasks)
