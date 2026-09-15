# Competition Workflow

Use this reference for an end-to-end solution design. Keep the work iterative: a usable baseline should exist before advanced optimization or model stacking.

## 1. Build the problem map

Create one row per subquestion.

| Field | Required interpretation |
| --- | --- |
| Mathematical task | estimation, prediction, classification, reconstruction, evaluation, optimization, control, or simulation |
| Target | exact quantity, class, decision, path, policy, or ranking to output |
| Inputs | files, fields, units, sampling structure, known constants |
| Constraints | physical, logical, resource, temporal, spatial, or competition requirements |
| Metric | what makes an answer good and how it will be measured |
| Dependency | outputs or calibrated quantities inherited from earlier questions |
| Evidence | calculation, plot, table, residual, comparison, or robustness test required |

Resolve ambiguous wording by writing an operational definition. If several definitions are plausible, compare them on interpretability, computability, and sensitivity rather than silently choosing one.

## 2. Audit the attachments

Produce a compact data dictionary and record:

- row/entity identity and whether repeated observations exist;
- time frequency, spatial resolution, group/device/source identifiers;
- units, coordinate systems, time zones, encodings, and category meanings;
- missing-value mechanism and outlier candidates;
- label provenance and any fields derived from the target;
- train/test distribution differences;
- impossible values, duplicate rows, and broken joins.

Preserve raw data. Put cleaning, transformations, and exclusions in reproducible steps with counts before and after each step.

## 3. Establish the baseline

The baseline is a diagnostic instrument, not filler. Choose one that is easy to reproduce and exposes what the advanced model must improve:

- prediction: mean/last value, linear or logistic regression, tree ensemble;
- classification: majority class plus a transparent classifier;
- optimization: greedy, equal allocation, shortest path, or exact small-instance solution;
- evaluation: equal weight plus one defensible weighting method;
- physical modeling: governing equation with the fewest corrections;
- simulation: analytically checkable limiting case.

Record the same metrics and constraints for baseline and main model.

## 4. Build the main model chain

For each added component, state:

1. the observed failure mode it addresses;
2. the mathematical change;
3. the new parameter or assumption;
4. the expected measurable effect;
5. the ablation that can verify the contribution.

Reuse outputs across questions. Typical coherent chains include:

- extraction or calibration → prediction → decision optimization → robustness;
- physical baseline → residual correction → uncertainty estimate → robust optimization;
- segmentation → instance parameterization → spatial reconstruction → active sampling;
- indicator construction → factor analysis → prediction → policy or resource allocation.

## 5. Implement reproducibly

Organize code by data preparation, model, evaluation, and figure generation. Save configurations, seeds, package versions, intermediate tables, and final artifacts. Add small tests for units, shape, feasibility, conservation, and metric calculations.

Before long runs, test a small slice end to end. For stochastic optimization, save the best feasible solution and convergence history at intervals.

## 6. Convert results into evidence

Each main claim needs a matching artifact:

| Claim | Minimum evidence |
| --- | --- |
| Model predicts well | held-out metric, baseline, residual/error distribution |
| Component is useful | ablation under the same split and budget |
| Solution is optimal or better | feasibility check, baseline gap, convergence or exact small-case comparison |
| Result is robust | parameter/data perturbation and stability interval |
| Mechanism is plausible | sign, magnitude, limiting case, or independent physical/statistical check |
| Policy improves outcomes | counterfactual or simulation assumptions plus multiple outcome metrics |

End with a claim-to-evidence table before drafting the abstract and conclusion.
