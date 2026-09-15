---
name: huawei-cup-modeling
description: "Use for Huawei Cup / China Graduate Mathematical Contest in Modeling work: interpret a problem, decompose subquestions, audit attachments, select and combine models, design validation, plan computation, draft or review a competition paper, or retrieve analogues from the curated 44-paper Huawei Cup knowledge base. Do not use for routine mathematics exercises or unrelated academic writing."
---

# Huawei Cup Mathematical Modeling

Build a defensible solution chain from the actual problem and data. Historical papers are analogues, not templates to copy and not evidence that a method will work on the current data.

## Select the working mode

Identify the user's current phase before producing detail:

- **Rapid triage:** classify each subquestion, expose the hardest dependency, and propose a baseline plus one justified upgrade.
- **Full solution design:** produce the problem map, data audit, model chain, computation plan, validation plan, and expected figures/tables.
- **Implementation support:** turn an agreed model into modular code, tests, intermediate outputs, and reproducible runs.
- **Paper drafting:** write only from established formulas and computed results; keep every claim traceable to a table, figure, or calculation.
- **Review and repair:** audit logic, data leakage, assumptions, metrics, consistency, and unsupported claims before suggesting edits.

If the problem statement or required attachment is missing, request it before committing to a model. A preliminary taxonomy may be offered, but label it provisional.

## Core workflow

1. Convert the prompt into a **problem map** with one row per subquestion: decision/prediction target, inputs, outputs, constraints, evaluation metric, and dependency on earlier questions.
2. Audit the data before choosing an advanced model. Check units, identifiers, time/space/group structure, missingness, outliers, label construction, imbalance, and whether the test set has a distribution shift.
3. For each subquestion, establish the simplest credible baseline. Add complexity only when a specific residual pattern, constraint, uncertainty, or validation failure justifies it.
4. Make the questions form one chain. Reuse calibrated parameters, cleaned data, uncertainty estimates, and intermediate outputs instead of rebuilding disconnected models.
5. Specify computation in executable terms: variables, objective, constraints, algorithm, stopping rule, initialization, complexity, random seeds, and required artifacts.
6. Design validation before interpreting results. Use data-appropriate splits and compare against baselines, ablations, sensitivity, robustness, and error cases.
7. Separate three kinds of statements: derived facts from the current data, assumptions/model choices, and results reported by historical papers.

Read [competition-workflow.md](references/competition-workflow.md) when producing a full solution plan. Read [problem-routing.md](references/problem-routing.md) when selecting models. Read [validation-and-audit.md](references/validation-and-audit.md) for evaluation or review. Read [paper-writing.md](references/paper-writing.md) only for writing or structural revision.

## Use the curated knowledge base

The local knowledge base contains 44 papers, 164 subproblem records, and 66 method records. Query it when a historical analogue would materially improve model selection or risk checking:

```bash
python3 scripts/query_kb.py --query "多目标优化 疲劳 功率分配" --dataset all --limit 8
python3 scripts/query_kb.py --query "时间序列 空间泄漏" --dataset subproblems --topic D --limit 6
```

Use returned paper IDs to cross-reference `references/data/papers.json`, `subproblems.json`, and `methods.json`. Prefer task similarity, data structure, constraints, and validation design over matching an algorithm name. Do not quote a paper's reported performance as an expected current result.

## Model-selection rules

- Prefer **physics/statistics plus data-driven correction** when a governing relationship is available but incomplete.
- Prefer **structured optimization** when the decision variables and constraints are explicit; use heuristics only after defining feasibility and a baseline.
- For time, space, subject, device, or file grouped data, split by the true deployment unit. Random row splits are usually invalid.
- For multiobjective tasks, show the Pareto trade-off or justify scalarization weights; do not present one weighted answer as uniquely optimal.
- For deep learning on small data, require a classical baseline, leakage-safe split, regularization or transfer learning, and stability across seeds.
- For composite scores, report indicator direction, normalization, weight source, and sensitivity to weights.
- For chained models, quantify error propagation. An accurate upstream model does not guarantee a valid downstream optimum.
- Avoid algorithm stacking for decoration. Every preprocessing step and model component must solve a named failure mode.

## Output contract

Unless the user asks for a narrower answer, deliver:

1. A subquestion problem map.
2. A coherent baseline-to-main-model chain.
3. Mathematical definitions for variables, objectives, constraints, and key assumptions.
4. A data-processing and implementation plan.
5. A validation matrix tied to each claim.
6. A list of required figures, tables, and intermediate files.
7. Main risks, fallback methods, and unresolved choices.

Never invent attachment contents, numerical results, citations, or successful validation. When computation has not been run, describe outputs as planned rather than obtained.
