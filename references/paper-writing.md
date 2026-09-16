# Competition Paper Writing

Use this reference only after the problem map is stable and the available code, results, and figures have been inventoried. The paper is an evidence argument, not a chronological work log and not a catalogue of algorithms.

## 1. Evidence inventory before drafting

For every subquestion, build a compact evidence card:

| Field | Required content |
| --- | --- |
| Direct answer | The quantity, decision, ranking, mechanism, or conclusion requested by the prompt |
| Model choice | Why this model matches the data structure and constraints |
| Core mathematics | Variables, equation/objective, constraints, and parameter source |
| Solver | Algorithm, key settings, stopping rule, and reproducible entry command |
| Main result | Exact values and the result file that produced them |
| Validation | Baseline, residual/error, ablation, sensitivity, robustness, or feasibility evidence |
| Handoff | What this question contributes to the next question |

Do not begin a polished paper while a main result has no traceable file or a question has no direct answer. Mark missing evidence explicitly and resolve it before making numerical claims.

## 2. Build the narrative map

Before writing sections, state how the questions relate:

- Does the next question reuse a calibrated parameter, cleaned dataset, uncertainty estimate, or decision from the previous question?
- Is the later model an extension of the earlier model, or a genuinely different model? State the reason.
- Can a later result validate or challenge an earlier assumption?
- Which concepts are shared and should be introduced once rather than repeated?

Use one transition sentence at each handoff. The sentence must name the inherited quantity or changed condition, not merely say that the next question is considered.

## 3. Draft in two passes

1. Write `论文/论文草稿.md` from evidence cards. Resolve logic, section order, figure purpose, and unsupported claims here.
2. After review, transfer the stable draft into `论文/论文.tex`, add cross-references, compile twice, and run the delivery audit.

When an existing draft is present, revise it in place. Do not discard usable writing or silently replace established modeling choices.

## 4. Overall paper structure

Use this backbone unless the competition specifies another format:

1. abstract and keywords;
2. problem restatement;
3. problem analysis and cross-question dependencies;
4. assumptions;
5. notation;
6. data audit and preprocessing;
7. model construction, solution, and validation by subquestion;
8. sensitivity, robustness, and error analysis;
9. strengths, limitations, and transferability;
10. conclusion;
11. verified references;
12. appendices.

Each subquestion should close the loop:

> task and difficulty → data treatment → model and mathematics → algorithm → result → validation → interpretation → handoff

## 5. Section-specific technique

### Problem restatement

Compress the background and rewrite each question as an operational mathematical task. Identify the object, known information, required output, constraints, and relation to other questions. Do not copy long passages from the prompt.

### Problem analysis

For each question explain: what makes it difficult, what pattern or constraint matters, why the candidate model fits, how it will be solved, and how success will be tested. Avoid formulas here unless a definition is necessary.

### Assumptions

Include only decisions introduced by the team, not conditions already given by the prompt. For each assumption state the simplification or convention and its consequence. Prefer a short defensible set over a fixed quota. Every material assumption should reappear in the model or limitations.

### Notation

Use a three-line table with symbol, meaning, unit, and index range when relevant. List recurring symbols only. Keep notation consistent across questions.

### Data preprocessing

Do not write only “the data were preprocessed.” State:

1. the observed defect or incompatibility;
2. the chosen method;
3. key parameters or thresholds;
4. why those settings are appropriate;
5. what information is retained or removed;
6. how the effect is checked or visualized.

### Model construction

Present every important relationship in four moves:

1. explain why the relationship is needed;
2. give the equation, objective, or constraint;
3. define every term and unit;
4. state what the expression computes and how its output is used next.

Put decisive derivation steps in the main text and long algebra in an appendix. Optimization models must show decision variables, objective, constraints, domains, and feasibility meaning in a recognizable standard form.

### Algorithm

Describe mathematical operations rather than library calls. Pseudocode or a flowchart should show initialization, update rule, objective or fitness evaluation, constraint handling, and stopping rule. A diagram that only says “input → model → output” adds no evidence.

### Results and validation

Every figure and table needs a specific question to answer. A useful result paragraph follows:

> conclusion → visual or numeric evidence → explanation in model terms → limitation or downstream implication

Reference each figure/table in the text and discuss it. Captions should state what is compared, the sample or scenario, and the metric/unit. Use three-line tables for exact comparisons and highlight the best value only when all methods use the same split, metric, and budget.

The正文 must directly answer the prompt. “The result is shown in the figure” is not analysis. Discuss trend, scale, uncertainty, agreement with domain constraints, and failure cases.

### Subquestion summary

End each question with its direct answer, strongest evidence, and handoff. Do not repeat a list of all numbers or begin every summary with the same stock phrase.

## 6. Abstract: write it last

The abstract should report the task chain, decisive model idea, principal quantitative results, and the most relevant validation. Give different questions different rhetorical emphasis; do not repeat one fill-in-the-blank sentence with changed numbers. Remove generic claims such as “good performance” or “provides decision support” unless a concrete result makes them meaningful.

Every number in the abstract must appear in a result table, figure, or calculation artifact.

## 7. Academic style and anti-template rules

- Keep file paths, function calls, debugging, runtime diary, and data-writing operations out of the main text; put reproducibility details in an appendix or repository note.
- Do not show raw attachment filenames in prose when a semantic description is clearer.
- Avoid process-report language such as “mechanical checks passed” or “independent recalculation confirmed.” State the actual test and result.
- Limit stock transitions such as “it is worth noting,” “therefore,” or “in summary.” Vary sentence structure and make transitions carry information.
- Do not call a result optimal, significant, robust, or generalizable without the matching proof or test.
- Explain standard algorithms briefly; spend space on task-specific adaptation, constraints, parameters, and failure modes.

## 8. Strengths, limitations, and transferability

Strengths must name verified properties: lower held-out error, constraint satisfaction, stable rankings, or computational feasibility. Limitations must identify the affected scope and likely direction of bias. Proposed improvements should address those limitations. Transferability must name what remains invariant and what must be recalibrated in a new setting.

## 9. References and appendices

Verify every reference against a real source and include only works cited in the正文. Use references for model theory, algorithm origin, domain background, and justified comparisons—not decoration.

Appendices should contain long derivations, core executable code, supplemental tables, or sample data needed to verify the work. Every appendix item should be referenced from the正文, and its equations, code outputs, and numbers must agree with the main text.

Before delivery, read and apply [delivery-checklist.md](delivery-checklist.md), then run:

```bash
python3 scripts/auto_model.py audit <workspace> --strict
```
