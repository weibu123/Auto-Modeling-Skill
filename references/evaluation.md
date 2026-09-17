# Skill Evaluation

Read this file when changing instructions, retrieval, schemas, or modeling behavior. Structural validation alone does not show that the Skill makes better decisions.

## Retrieval evaluation

`evals/retrieval_cases.json` contains reviewed queries and acceptable top-k records. Run:

```powershell
python scripts/auto_model.py eval-retrieval
```

The report includes Recall@k and mean reciprocal rank. When a new paper or ranking change lowers either metric, inspect failed cases before adjusting weights. Do not rewrite expected records merely to make a regression pass; change them only after a human review shows that the expectation was incomplete.

## Modeling forward tests

`evals/modeling_cases.json` contains realistic prompts with required and forbidden behaviors. Evaluate them in an isolated competition workspace. Do not provide the expected behaviors to the tested agent.

Score each required behavior and the absence of each forbidden behavior on the declared 0–2 scale. Compare:

1. the agent without this Skill;
2. the current released Skill;
3. the proposed revision.

Keep the model and reasoning effort fixed while comparing Skill revisions. Record failures by category: problem decomposition, data leakage, baseline choice, validation, model-chain coherence, traceability, and unsupported claims.

## Iteration rule

Make one coherent change at a time, rerun relevant tests, and retain a change only when it improves the targeted behavior without causing material regressions elsewhere. Prefer a narrow correction supported by a failed case over adding general instructions.
