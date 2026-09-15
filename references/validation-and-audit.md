# Validation and Audit

Use this reference before accepting a result or reviewing a draft.

## Split integrity

- Identify the true independent unit: patient, machine, file, device, site, region, time block, or simulation seed.
- Keep all observations from one unit in one split when deployment will encounter unseen units.
- Fit imputation, scaling, encoding, feature selection, oversampling, PCA, and calibration only on training data.
- For time series, train on the past and test on the future. Report error by horizon.
- For spatial data, use blocked or leave-region-out validation in addition to random splits.
- Do not tune on the unlabeled competition test distribution unless the rules and method explicitly allow transductive use.

## Metric integrity

- Define the unit and aggregation of every metric.
- For imbalance, include per-class recall/precision, macro-F1 or PR-AUC; accuracy alone is insufficient.
- For regression, combine scale-dependent error with relative or normalized error and inspect residuals.
- For ranking/evaluation, report rank stability under normalization and weight perturbations.
- For optimization, report feasibility, objective components, baseline gap, runtime, and variability across seeds.
- For simulation, verify conservation, limiting cases, distributional assumptions, and Monte Carlo uncertainty.

## Minimum comparison matrix

| Test | Question answered |
| --- | --- |
| Naive or classical baseline | Is the task genuinely learned or optimized? |
| Strong same-family baseline | Is the proposed change better than a competent alternative? |
| Ablation | Which component produces the gain? |
| Sensitivity | Does a reasonable parameter choice change the conclusion? |
| Robustness perturbation | Does noise, missingness, delay, or distribution shift break the result? |
| Error cases | Where and why does the method fail? |
| Runtime/resource report | Can the method finish under competition and deployment constraints? |

## Claim audit

Flag a sentence when it:

- says “significant” without a statistical or practically meaningful comparison;
- says “optimal” without exact proof, a bound, or a clearly scoped heuristic meaning;
- says “robust” without perturbation or repeated-run evidence;
- generalizes beyond the sampled population, time, region, or operating range;
- converts correlation, attention, feature importance, or a fitted rule into causality;
- reports only the best random seed or favorable case;
- copies a historical paper's metric without reproducing it on current data.

## Final consistency checks

Verify notation, units, row counts, sample splits, table/figure numbers, significant digits, parameter values, and conclusions against code outputs. The abstract and conclusion may summarize only results that appear in the body and have an identifiable calculation artifact.
