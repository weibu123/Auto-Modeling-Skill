# Paper Delivery Checklist

Use after the Markdown draft is approved and again after the final LaTeX compilation. Record unresolved items rather than silently treating them as passed.

## Structure and narrative

- [ ] Every question is restated as a mathematical task with a direct answer.
- [ ] The paper explains dependencies among questions and names inherited outputs.
- [ ] Every question closes the loop from analysis through validation and handoff.
- [ ] Assumptions are team choices rather than copied prompt conditions.
- [ ] Notation, units, indexes, and question numbering are consistent.

## Models and computation

- [ ] Important formulas have motivation before them and interpretation after them.
- [ ] Optimization models specify decision variables, objective, constraints, domains, and feasibility.
- [ ] Algorithms state initialization, update, constraint handling, and stopping rules.
- [ ] Parameters have a source, calibration method, or sensitivity analysis.
- [ ] Existing results were not silently replaced or recomputed.

## Results and evidence

- [ ] Each numerical claim traces to a result file, figure, table, or calculation.
- [ ] Baselines and main models use comparable data splits, metrics, and budgets.
- [ ] Each figure/table has units, scope, caption, text reference, and interpretation.
- [ ] Error, residual, feasibility, sensitivity, robustness, or failure-case analysis matches the claim type.
- [ ] The正文 directly answers the prompt rather than merely pointing to figures.

## Writing quality

- [ ] The abstract was written last and every abstract number appears in the正文.
- [ ] Abstract sentences vary by question and do not repeat one template.
- [ ] The main text avoids filenames, function-call narration, debugging history, and work-log language.
- [ ] Stock phrases and unsupported adjectives have been removed.
- [ ] Strengths are verified; limitations identify scope and likely bias.

## References and appendices

- [ ] Every cited source was verified and every bibliography item is cited.
- [ ] Citation style is consistent with the competition requirements.
- [ ] Appendices are referenced from the正文 and agree with equations, code, and results.
- [ ] Core code is executable and stripped of irrelevant debugging fragments.

## Delivery

- [ ] `论文/论文草稿.md` reflects the final narrative.
- [ ] `论文/论文.tex` compiles twice without errors.
- [ ] Cross-references, bibliography, figures, and tables resolve correctly.
- [ ] `论文/论文.pdf` exists and was visually inspected.
- [ ] `python3 scripts/auto_model.py audit <workspace> --strict` passes or remaining deviations are documented.
