# Problem Routing

Use the table to shortlist models after the data audit. Query the knowledge base for comparable subproblems and risks before selecting the final chain.

| Problem signal | Credible first model | Upgrade only when | Required checks | Common failure |
| --- | --- | --- | --- | --- |
| DAG, precedence, capacity, address or scheduling | topological/critical-path greedy; exact small-instance ILP | baseline leaves a measurable gap or scale blocks exact solution | feasibility, small-case optimum, runtime, convergence | heuristic returns infeasible or incomparable solutions |
| Rolling allocation or control with uncertain measurements | deterministic rolling optimization or MPC | delay/noise materially changes decisions | closed-loop simulation, constraint violations, sensitivity | optimizing a biased proxy creates unsafe actions |
| Continuous and discrete multiobjective optimization | scalarized baseline plus Pareto method | stakeholders cannot justify one weight vector | Pareto front, dominance, weight sensitivity, repeated seeds | calling one weighted point the global optimum |
| Tabular nonlinear prediction | linear/generalized linear model and tree ensemble | residuals show nonlinear or interaction structure | grouped split, calibration, feature leakage, error slices | random rows from the same entity appear in both sets |
| Multivariate time series | persistence/ARIMA and regularized lag model | long nonlinear dependencies improve held-out future periods | chronological split, rolling evaluation, horizon-specific error | random split leaks the future |
| Physics equation with missing factors | calibrated governing equation | residuals vary systematically with unmodeled conditions | units, limiting cases, residual plots, parameter stability | black-box correction violates physical monotonicity |
| Image segmentation and geometry reconstruction | interpretable enhancement/threshold baseline | labels and sample size support a trained segmenter | subject-level split, IoU/F1, parameter fit, scale consistency | pixel accuracy hides poor small-object segmentation |
| Multi-source spatial field | coordinate harmonization plus IDW/Kriging baseline | source biases or dynamics require assimilation | leave-location-out validation, resolution sensitivity | spatial random split inflates accuracy |
| Geospatial trend and vulnerability | nonparametric trend, spatial statistics, transparent index | nonlinear interactions improve unseen-region prediction | spatial blocks, autocorrelation, weight sensitivity, scenario uncertainty | treating correlated pixels as independent samples |
| Domain adaptation or unlabeled target data | source-only baseline plus feature-distance audit | a real domain shift is demonstrated | target-blind tuning, grouped split, class-conditional alignment | marginal alignment mixes classes |
| Video traffic extraction and real-time decisions | detector/tracker audit plus traffic-flow baseline | prediction adds actionable lead time | event-level split, counting error, threshold hysteresis, counterfactual assumptions | upstream detection error disappears from reported policy metrics |
| Composite evaluation or ranking | equal weight and transparent normalized score | expert or entropy weights change decisions meaningfully | direction, normalization, rank stability, external comparison | arbitrary weights dominate the answer |
| Orbital state, precision timing, photon simulation | two-body/geometry baseline and conservation checks | navigation precision requires time-scale and relativistic corrections | coordinate/time convention, units, component magnitudes, template fit | sign or reference-frame mismatch overwhelms small corrections |

## Choosing between close candidates

Rank candidates by:

1. compatibility with the actual data structure and deployment split;
2. ability to satisfy hard constraints;
3. interpretability of parameters and failure modes;
4. validation evidence available within competition time;
5. implementation and compute cost;
6. novelty only after the first five criteria.

When two models are close, prefer the one that enables a stronger falsifiable comparison. Keep the other as a fallback or ablation.
