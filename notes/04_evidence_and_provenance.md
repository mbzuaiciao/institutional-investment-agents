# Evidence and provenance

Retrieval finds candidate text. Evidence is a source object with identity, locator, issuer scope, date, and content. A citation points to that evidence. A claim asserts something and declares whether it is factual, calculated, inferred, or judgmental. These are distinct layers.

Factual claims require evidence IDs; calculated claims require tool-result IDs. State transitions reject pointers to objects not already present. The verifier checks existence and a conservative lexical-support heuristic. That heuristic is useful for catching missing or obviously unrelated citations, but it is not semantic entailment and can produce both false passes and false failures. Production verification should combine deterministic checks, source-aware rules, and carefully evaluated model judgments.

