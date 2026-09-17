# Knowledge Base Schema v2

Read this file when maintaining, validating, or extending the curated knowledge base. It is not required for ordinary competition solving.

## Design goals

Schema v2 separates reviewed prose from structured retrieval fields. Structured fields may repeat reviewed prose at a coarser granularity, but they must not introduce unverified facts. Unknown constraints, metrics, baselines, or artifacts remain empty rather than being guessed.

Every curated record has:

- `record_version: 2`;
- `evidence_level: deeply_curated`;
- stable identity and cross-references;
- original reviewed prose fields;
- structured lists used by retrieval, validation, and coverage reporting.

## Paper records

Paper records retain title, data, pipeline, validation, result, strength, risk, evidence, and source file. Schema v2 additionally requires:

- `year` and `topic` for filtering;
- `variant_label` to distinguish solutions to the same problem;
- `problem_archetypes` and `data_structure`;
- `models` and `validation_design`;
- `failure_modes` and `evidence_locations`.

## Subproblem records

Subproblem records add explicit fields for:

- `objective`;
- `constraints`;
- `metric`;
- `split_unit`;
- `assumptions`;
- `failure_modes`;
- `upstream_dependencies` and `downstream_outputs`;
- `implementation_artifacts`.

Empty lists are valid and represent a known curation gap. They should be filled only after checking the source Markdown or current competition artifacts.

## Method records

Method records add:

- `must_check`;
- `minimum_baseline`;
- `forbidden_when`;
- `recommended_alternatives`;
- `computational_complexity`;
- `common_misuse`.

These decision fields are more useful than collecting additional algorithm names. Fill them from multiple reviewed papers or established modeling principles, not from a single reported result.

## Decision-field batches

Store reviewed constraints, metrics, baselines, and method guardrails in `references/data/decision_fields/<batch-id>.json`. Keep these files separate from the paper curation batches because they contain maintainer synthesis as well as facts reorganized from papers.

Each batch must state its `evidence_basis`. Subproblem entries must provide non-empty `constraints` and `metric`; method entries must provide a `minimum_baseline`, `forbidden_when`, `recommended_alternatives`, and `common_misuse`. The promotion command rejects unknown identities, duplicate overrides, empty lists, and unsupported fields. Applied records carry `decision_field_sources` so a reviewer can find the responsible batch.

## Maintenance commands

```powershell
python scripts/migrate_kb_schema_v2.py
python scripts/auto_model.py decision-promote --check
python scripts/auto_model.py decision-promote
python scripts/auto_model.py kb-validate
python scripts/auto_model.py eval-retrieval
```

The migration and decision promotion are idempotent. The validator checks field types, identities, paper links, method sources, index links, metadata counts, and structured-field coverage.
