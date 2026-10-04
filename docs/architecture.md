# Architecture

Product: **Personalized AI Mentor**
Packaged evidence profile: **Alexandr Wang public-source case study**

## Design objective

The system separates substantive supervision from persona presentation. Public evidence informs a compressed behavioral model; the policy selector activates only the smallest useful subset; optional retrieval restores source nuance when a consequential judgment needs it.

## Runtime sequence

1. Classify the session and supervision relevance.
2. Read only the learner state needed for the decision.
3. Select applicable behavioral policies under user constraints.
4. Apply the semantic RAG gate.
5. If useful, retrieve up to four source chunks and reject weak matches.
6. Make the substantive decision.
7. Apply the communication-style layer without changing facts, priorities, or confidence.
8. Update state only when the conversation establishes a justified fact or plan.

## Layer boundaries

| Layer | Responsibility | Must not do |
|---|---|---|
| Learner state | Goals, projects, skills, constraints, execution facts | Encode persona judgments as user facts |
| Session router | Determine interaction type, relevance, and depth | Route by keywords alone |
| Behavioral model | Store evidence-derived supervisory rules | Impersonate Wang or override user constraints |
| Policy selector | Activate the minimum useful rules | Treat every rule as always active |
| Selective RAG | Add source nuance and traceability | Retrieve on every message or force weak evidence |
| Style model | Shape order, directness, and conversational delivery | Change the substantive decision |
| State updater | Record supported changes | Infer completion, mastery, or deadlines from ambiguity |

## Retrieval implementation

The corpus is small, so the project uses a deterministic local BM25-style sparse index rather than a hosted vector database. The index preserves source and chunk IDs, statement types, evidence levels, source status, URLs, and source hashes. Ranking boosts direct statements and discounts caveated or publisher-only records.

The LLM decides whether retrieval is warranted and generates a focused conceptual query. The deterministic retriever produces candidates; the LLM still evaluates applicability after retrieval. A zero-result response is valid.

## Safety and epistemic boundaries

- The product is Personalized AI Mentor; Wang is the cited subject of one evidence-profile case study, not the product identity.
- The evidence profile is not an identity simulation, endorsement, voice replica, or representation of Wang.
- Public founder rhetoric is not automatically safe personal productivity advice.
- Learner-defined health and workload constraints outrank persona intensity.
- Evidence gaps remain explicit rather than being filled with invented philosophy.
- Organizational source material is labeled as analogy when applied to individual study decisions.
