# Agent state and orchestration

Chat history is a transcript. Task state says what remains. Research state preserves evidence, claims, calculations, contradictions, assumptions, and open questions. Memory is a policy for retaining and retrieving information across steps or cases. Conflating these concepts makes a workflow difficult to resume, verify, or evaluate.

This project stores important research objects explicitly and logs each transition. Orchestration is deliberately ordinary Python: create a plan, route tasks, execute tools, add evidence before dependent claims, synthesize, challenge, verify, request approval, and emit the memo. The simplicity makes causal ablations possible.

