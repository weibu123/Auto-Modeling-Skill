# Command Reference

Use these commands for repeatable filesystem work. Run them from the Skill root or call the script by its absolute path.

## Initialize a workspace

```bash
python3 scripts/auto_model.py init <target-directory> --questions 4
```

The command creates missing directories and starter files. It refuses a non-empty target unless `--merge` is supplied. Merge mode never overwrites an existing file.

Options:

- `--questions N`: create `问题1` through `问题N`; valid range is 1–12.
- `--title TEXT`: put a competition title in `比赛状态.md` and the LaTeX title.
- `--merge`: add only missing files to an existing workspace.

After initialization, put the untouched prompt in `题目/` and untouched attachments in `数据/原始/`. Do not move derived files into those directories.

## Query the knowledge base

```bash
python3 scripts/auto_model.py query "<task, data, constraint, or risk keywords>" \
  --dataset all --limit 8
```

Options:

- `--dataset papers|subproblems|methods|all`
- `--topic A|B|C|D|E|F`
- `--year YYYY`
- `--limit N`
- `--json` for machine-readable output
- `--explain` to show matched fields and the record evidence level

Use several structural terms together. Queries such as `时空 预测 分组验证 泄漏` are more useful than an isolated algorithm name.

The ranker combines field-weighted exact matches with dependency-free BM25. Subproblem results surface reviewed constraints and metrics; method results surface the minimum baseline and forbidden conditions. `待补` means the field has not completed decision-field review. Run the reviewed retrieval evaluation after changing weights, tokenization, schemas, or data.

## Validate and evaluate the knowledge base

```bash
python3 scripts/auto_model.py decision-promote --check
python3 scripts/auto_model.py decision-promote
python3 scripts/auto_model.py kb-validate
python3 scripts/auto_model.py kb-validate --strict
python3 scripts/auto_model.py eval-retrieval
```

`decision-promote --check` validates every reviewed batch without writing. Without `--check`, the command deterministically merges decision fields into `subproblems.json` and `methods.json`, records batch provenance, and rejects unknown or conflicting identities. Run it after editing `references/data/decision_fields/`.

`kb-validate` checks Schema v2, identity uniqueness, cross-dataset links, metadata counts, and structured-field coverage. Empty metrics, constraints, and method baselines are reported as coverage warnings rather than silently invented.

`eval-retrieval` runs the reviewed cases in `evals/retrieval_cases.json` and reports Recall@k and mean reciprocal rank. Use `evals/modeling_cases.json` for isolated forward tests of modeling behavior.

## Audit a workspace

```bash
python3 scripts/auto_model.py audit <target-directory>
python3 scripts/auto_model.py audit <target-directory> --strict
```

The audit checks source material, per-question notes/code/results, the Markdown draft, core LaTeX sections, unresolved placeholders, selected writing red flags, and whether a compiled PDF exists. It does not prove mathematical correctness or citation truth. `--strict` returns a non-zero exit status when warnings remain, which is useful in CI or before final delivery.

## Check the local toolchain

```bash
python3 scripts/auto_model.py doctor
python3 scripts/auto_model.py doctor --strict
```

The check covers Python 3.10+, XeLaTeX, and the LaTeX classes/packages used by `assets/paper-template.tex`. Missing LaTeX support does not block workspace initialization, querying, or auditing. In strict mode any missing requirement returns a non-zero exit status.

## Safety behavior

- Initialization never modifies files already present.
- Auditing is read-only.
- Querying reads only the bundled JSON knowledge base.
- Validation and evaluation are read-only.
- No command downloads data, installs packages, or sends content externally.
