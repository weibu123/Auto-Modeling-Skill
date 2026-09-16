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
- `--limit N`
- `--json` for machine-readable output

Use several structural terms together. Queries such as `时空 预测 分组验证 泄漏` are more useful than an isolated algorithm name.

## Audit a workspace

```bash
python3 scripts/auto_model.py audit <target-directory>
python3 scripts/auto_model.py audit <target-directory> --strict
```

The audit checks source material, per-question notes/code/results, paper files, unresolved placeholders, and whether a compiled PDF exists. It does not prove mathematical correctness. `--strict` returns a non-zero exit status when warnings remain, which is useful in CI or before final delivery.

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
- No command downloads data, installs packages, or sends content externally.
