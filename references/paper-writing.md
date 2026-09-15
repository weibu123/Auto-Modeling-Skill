# Competition Paper Writing

Use after the model and results are stable. Do not draft numerical claims before computation.

## Abstract

Write one compact paragraph per problem chain, not a catalogue of algorithm names. For each question state the task, decisive model idea, validation, and principal numeric result. End with the overall practical conclusion. Avoid background that does not distinguish the solution.

## Problem analysis

Explain the mathematical structure and dependencies among questions. State why each output is needed downstream. A flowchart should show data and parameter flow, not repeat section titles.

## Assumptions and notation

Keep only assumptions that simplify a real difficulty. State the consequence and where the assumption may fail. Give units and index ranges in the notation table; do not list symbols used only once.

## Model sections

For each subquestion use this order:

1. target and inputs;
2. preprocessing or feature construction;
3. variables, equations, objective, and constraints;
4. algorithm and reproducible settings;
5. result with a table or figure;
6. validation and interpretation;
7. limitation or handoff to the next question.

Do not place formulas without defining symbols. Do not explain standard algorithms at textbook length; spend space on adaptations, constraints, and why the method fits the data.

## Figures and tables

Prioritize: data-quality overview, key relationship/residual plot, baseline comparison, ablation, sensitivity/robustness, convergence or Pareto front, and final decision visualization. Every plot needs units, sample scope, and a caption that states what is compared.

Use consistent precision. Avoid screenshots of console output and tables that duplicate a figure without adding exact values.

## Strengths, limitations, and conclusion

Strengths should name verified properties such as lower held-out error, constraint satisfaction, or stability. Limitations should identify the affected scope and likely direction of bias. The conclusion should answer the questions in order and avoid new models or evidence.

## Final paper audit

- every abstract number appears in a result table or figure;
- every conclusion traces to current-data evidence;
- all baselines use the same split, metric, and compute budget where relevant;
- figures and tables are referenced before or near their appearance;
- variable names, units, and problem numbering are consistent;
- “optimal,” “significant,” “robust,” and “generalizable” are used only with supporting tests;
- no historical paper result is presented as the team's own result.
