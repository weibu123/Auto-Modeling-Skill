---
name: auto-modeling-skill
description: "Use for Huawei Cup / China Graduate Mathematical Contest in Modeling work: initialize a competition workspace, interpret the problem, audit attachments, retrieve analogues from the indexed 338-paper corpus and deeply curated knowledge base, select and implement models, design validation, draft a traceable LaTeX paper, or audit final delivery. Do not use for routine mathematics exercises or unrelated academic writing."
---

# Auto Modeling Skill

Build a defensible, reproducible competition solution from the actual problem and attachments. Historical papers are analogues, not templates to copy and not evidence that a method will work on the current data.

## Choose the operating mode

- **Workspace setup:** initialize the competition directory and explain where raw inputs, code, results, and paper artifacts belong.
- **Rapid triage:** classify each subquestion, expose the hardest dependency, and propose a baseline plus one justified upgrade.
- **Full solution design:** produce the problem map, data audit, model chain, computation plan, validation plan, and required figures/tables.
- **Implementation support:** turn an agreed model into modular code, tests, intermediate outputs, and reproducible runs.
- **Paper drafting:** write only from established formulas and computed results; keep every numerical claim traceable to an artifact.
- **Review and repair:** audit leakage, assumptions, metrics, consistency, unsupported claims, compilation, and delivery completeness.

If the problem statement or required attachment is missing, request it before committing to a model. A provisional taxonomy is allowed only when clearly labelled provisional.

## Start with deterministic tools

Read [commands.md](references/commands.md) before initializing or auditing a workspace.

```bash
python3 scripts/auto_model.py init ./contest --questions 4
python3 scripts/auto_model.py query "时间序列 空间泄漏" --dataset subproblems --topic D --limit 6
python3 scripts/auto_model.py query "无人机 调度" --dataset index --year 2016 --topic A --limit 6
python3 scripts/auto_model.py decision-promote --check
python3 scripts/auto_model.py audit ./contest
python3 scripts/auto_model.py doctor
```

Resolve command paths relative to this Skill directory. Do not assume the user's current directory contains the scripts.

## Core reasoning workflow

1. Convert the prompt into a **problem map** with one row per subquestion: target, inputs, outputs, constraints, metric, evidence, and dependency on earlier questions.
2. Audit the attachments before choosing an advanced model. Check units, identifiers, time/space/group structure, missingness, outliers, label construction, imbalance, and possible distribution shift.
3. Establish the simplest credible baseline for each subquestion. Add complexity only when a named residual pattern, constraint, uncertainty, or validation failure justifies it.
4. Make the questions form one chain. Reuse calibrated parameters, cleaned data, uncertainty estimates, and intermediate outputs rather than building disconnected models.
5. Specify computation in executable terms: variables, objective, constraints, algorithm, stopping rule, initialization, complexity, seeds, and saved artifacts.
6. Design validation before interpreting results. Use deployment-appropriate splits and include baselines, ablations, sensitivity, robustness, and error cases.
7. Separate current-data facts, assumptions/model choices, and historical-paper results.
8. Before delivery, run the project audit and reconcile every paper claim with code or result files.

Read [competition-workflow.md](references/competition-workflow.md) for full solution design, [problem-routing.md](references/problem-routing.md) for model selection, and [validation-and-audit.md](references/validation-and-audit.md) for evaluation or review. For drafting or structural revision, read [paper-writing.md](references/paper-writing.md) completely; before final delivery, apply [delivery-checklist.md](references/delivery-checklist.md).

## Use the curated knowledge base

The local knowledge base has two evidence levels: a 338-paper discovery index and a deeply curated layer containing 55 paper records, 213 subproblem records, and 86 method records. Query it when an analogue materially improves model selection or risk checking:

```bash
python3 scripts/auto_model.py query "多目标优化 疲劳 功率分配" --dataset all --limit 8
python3 scripts/auto_model.py query "脉冲星 相对论时延 光子仿真" --topic F --limit 6
python3 scripts/auto_model.py query "遗传位点 假设检验" --dataset index --year 2016 --topic B --limit 6
```

Use `references/data/paper_index.json` to discover candidates by year, topic, title, abstract, and keywords. Records marked `indexed` are discovery leads only: inspect their source Markdown before reusing a method or claim. Records marked `curated` cross-reference `papers.json`, `subproblems.json`, and `methods.json` and contain deeper task, validation, and risk extraction. Prefer task similarity, data structure, constraints, and validation design over algorithm-name matching. Never quote a historical paper's reported performance as an expected current result.

Before recommending an advanced method, retrieve its method record and check applicability, required data, minimum baseline, forbidden conditions, alternatives, and common misuse. If a result shows `待补`, treat that decision field as unresolved and derive it from the current problem rather than assuming the method is safe. For a selected analogue, also retrieve the closest subproblem record and compare its constraints and metric with the current question.

When maintaining the knowledge base or promoting indexed papers, read [knowledge-base-evidence.md](references/knowledge-base-evidence.md) and [knowledge-base-schema.md](references/knowledge-base-schema.md). Store reviewed decision fields in a traceable batch, run `decision-promote --check`, apply it, and then validate the result. When changing retrieval or Skill instructions, read [evaluation.md](references/evaluation.md) and rerun the relevant evaluation instead of relying on structural tests alone.

## Model-selection rules

- Prefer **physics/statistics plus data-driven correction** when a governing relationship exists but is incomplete.
- Prefer **structured optimization** when variables and constraints are explicit; use heuristics only after defining feasibility and a baseline.
- Split grouped, temporal, spatial, device, subject, or file data by the true deployment unit.
- For multiobjective tasks, show the Pareto trade-off or justify scalarization weights.
- For deep learning on small data, require a classical baseline, leakage-safe split, regularization or transfer learning, and stability across seeds.
- For composite scores, report indicator direction, normalization, weight source, and weight sensitivity.
- For chained models, quantify error propagation from upstream estimates to downstream decisions.
- Every preprocessing step and model component must address a named failure mode.

## Paper and delivery rules

- Treat `题目/` and `数据/原始/` as immutable source material.
- Reuse existing code and results unless the user asks to replace them; do not silently rerun or redesign completed work.
- Write numerical claims only after computation and link them to a result table, figure, or log.
- Draft the narrative in `论文/论文草稿.md` before polishing `论文/论文.tex`; write the abstract after the result sections stabilize.
- Make every subquestion close the loop from task and model choice through result, validation, interpretation, and handoff.
- Verify every citation against a real source.
- Compile LaTeX twice when cross-references are used, and report unresolved warnings or missing fonts/packages honestly.
- Never invent attachment contents, numerical results, citations, successful validation, or competition awards.

## Default output contract

Unless the user requests a narrower deliverable, provide:

1. subquestion problem map;
2. coherent baseline-to-main-model chain;
3. mathematical definitions for variables, objectives, constraints, and assumptions;
4. data-processing and implementation plan;
5. validation matrix tied to each main claim;
6. required figures, tables, and intermediate files;
7. risks, fallback methods, and unresolved decisions;
8. project artifact paths and current audit status when files are being created.
