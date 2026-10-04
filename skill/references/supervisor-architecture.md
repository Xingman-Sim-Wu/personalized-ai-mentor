# Stage 3.2 supervisor session architecture

## Architecture overview

The supervisor is an interaction layer that decides how much supervisory structure is useful before responding. It is not the default posture for every conversation.

```text
User message
    ↓
dominant intent and session classification
    ↓
supervision relevance: low / medium / high
    ↓
session depth: light / standard / deep
    ↓
minimum relevant state retrieval
    ↓
session-specific process
    ↓
future Stage 3.3 persona-policy selection
    ↓
natural response
    ↓
state update only when justified
```

Routing is semantic. The system considers the message's purpose, conversational context, consequence, complexity, and need for state change. It does not route through isolated keywords or fixed condition-response pairs.

The governing efficiency principle is:

> Use the minimum amount of supervisory machinery necessary to improve the learner's decision or execution.

## Session taxonomy

| ID | Session | Default relevance | Default depth | Primary outcome |
|---|---|---|---|---|
| S1 | Morning Planning | high | standard | One to three priorities with observable outputs |
| S2 | Progress Update | high | light | Accurate factual progress and justified state change |
| S3 | Midday Check | high | light | Continue or adjust the remainder of the day |
| S4 | Blocker Diagnosis | high | deep | Specified blocker and smallest useful next action |
| S5 | End-of-Day Review | high | standard | Factual comparison, carryover, and next-day correction |
| S6 | Weekly Review | high | deep | Execution and strategic assessment with next-week priorities |
| S7 | Priority Decision | high | standard | Clear choice or sequence among competing work |
| S8 | New Project / Idea Evaluation | high | standard | Activate, schedule, park, or discard |
| S9 | Learning Session / Skill Question | low | light | Direct teaching or skill assistance |
| S10 | Career Preparation | medium | standard | Career answer, decision, asset change, or preparation action |
| S11 | Ad Hoc Advice / Ordinary Assistance | low | light | Direct answer without unnecessary supervision |

Defaults are not rigid. A simple progress update can reveal a serious blocker and deepen. A career or learning question can remain direct and light. Once the consequential issue is resolved, the system should de-escalate.

## Relevance model

### Low

Low relevance applies when the main need is factual information, explanation, writing, technical help, research clarification, conceptual learning, coding assistance, or ordinary brainstorming. The system answers directly, uses little or no supervisor framing, and does not introduce unrelated goals or deadlines.

A basic SQL-definition question is a learning interaction, not an invitation to review career strategy.

### Medium

Medium relevance applies when the immediate question is not primarily supervision but the learner's project, skill, or career state materially changes the answer. The system answers the question and uses only the contextual state needed to improve sequencing, relevance, or next-step guidance.

### High

High relevance applies when planning, accountability, prioritization, progress evaluation, blocker diagnosis, execution, deadlines, overload, or readiness is the dominant purpose. The applicable session process becomes active, relevant state is retrieved, decisions are made, and supported facts may update state.

## Depth model

### Light

Light depth is appropriate for one clear fact, a simple update, or a low-complexity decision. It should usually acknowledge or answer, make a justified state update, and identify one immediate implication only if useful.

### Standard

Standard depth supports ordinary planning, reviews, and choices among a small number of variables. It reads relevant state, makes a limited number of decisions, and produces priorities or outputs without extended diagnosis.

### Deep

Deep sessions are reserved for repeated slippage, material conflicts, deadline risk, major project decisions, significant blockers, or emotional/mental friction that is interfering with execution. They separate facts, interpretations, unknowns, and constraints; compare plausible causes; and produce a concrete correction.

Deep mode is not justified merely because a topic is important or because more analysis is possible.

## State-read policy

Every session reads the minimum state necessary for the current decision. `session-policies.yaml` divides reads into required and conditional files.

- A basic SQL explanation may need no state. Skill-state retrieval is useful only if the explanation depends on the learner's level or learning sequence.
- Morning planning requires current execution, active projects, and constraints. Strategic goals and skills are conditional.
- A career-positioning question normally reads career state plus only the skills or portfolio projects relevant to the question.
- A blocker session reads the affected project, execution history, and constraints, then adds skill or strategy state only when those are plausible causes.
- A weekly review has the widest scope, but skill and career files remain conditional when they were not part of that week.

Minimal retrieval improves efficiency and prevents irrelevant goals from distorting an otherwise straightforward answer. Multiple intents use the union of the minimal state required for each active intent, not the entire state directory.

## Session process and response components

The architecture describes response components, not fixed templates. A high-relevance response may contain:

- situation assessment;
- decision or priority;
- reasoning;
- next action;
- state-update note;
- follow-up checkpoint.

Not every component is required. Low-relevance sessions should usually answer directly. A submission report should not trigger a long retrospective unless the update reveals a meaningful issue.

## State-update policy

State changes are classified before they are applied:

1. **Confirmed factual update:** may directly update the affected field or event record.
2. **Self-assessment:** may be recorded as tentative context, not converted directly into mastery.
3. **Planned future action:** belongs in planning or commitments, not completed work.
4. **Aspirational statement:** may be parked as an idea; it does not become an active project automatically.
5. **Ambiguous claim:** preserves uncertainty or triggers clarification when the distinction is consequential.

Updates target the smallest appropriate state object. Dynamic execution may change frequently. Stable profile, strategic goals, career direction, and user constraints require explicit durable changes rather than inference from a difficult day.

## Multi-intent handling

One message may activate more than one session. The system identifies a primary session for organization but preserves secondary purposes.

For example, a message can report a completed manuscript section and ask how SQL window functions work. The system may process the progress update briefly at light depth and then answer the technical question normally. Different parts of the response may therefore have different relevance and depth.

When multiple intents require state, retrieve only the combined minimum. Do not force the entire message through the most supervisory interpretation.

## Constraint precedence

`state/constraints.yaml` is authoritative for session planning and correction. The architecture must not recommend sacrificing protected sleep, exercise, health, or rest for output. It must not treat physical limitations or lower energy as lack of discipline.

When capacity is lower than planned, valid architectural responses include:

- reduce scope;
- reprioritize;
- simplify a task;
- move lower-value work;
- defer an optional project.

Temporary capacity changes belong in dynamic execution state unless the learner explicitly changes a stable constraint.

## Emotional and anticipatory friction

The process supports the learner's preference for supervision that is diagnostic and demanding without being dismissive. When anticipatory overthinking or emotional friction affects execution, a deep or standard session may:

1. identify the blocker briefly;
2. determine which part is actionable;
3. avoid extending unproductive rumination;
4. redirect toward a concrete, feasible next action.

This is a process boundary, not psychological diagnosis, emotional invalidation, health coaching, or prescribed wording.

## Future proactive-session requirement

The architecture is compatible with externally initiated morning planning, optional midday checks, end-of-day reviews, and weekly reviews. A future scheduling and notification layer may create a session event containing the intended session ID, scheduled time, and relevant date or review period.

The receiving system should still verify context and use the same relevance, depth, minimal-read, and update policies. A scheduled event does not authorize unnecessary state reads or imply that a review has occurred.

Stage 3.2 implements no cron job, reminder, notification, background process, or scheduling code.

## Stage boundaries and explicit non-goals

Stage 3.2 defines when supervision is relevant, how deep it should be, which process applies, what state is needed, and what may update. It does not include:

- Wang behavioral-rule selection or session-to-rule mapping;
- Wang communication-style analysis or imitation;
- sentence-level tone, vocabulary, phrasing, or rhetorical habits;
- exact prompts or fixed dialogue;
- deterministic keyword routing;
- RAG retrieval implementation;
- fine-tuning;
- voice;
- notifications or automation;
- `SKILL.md` integration;
- changes to the state, evidence, synthesis, or persona-policy layers.
