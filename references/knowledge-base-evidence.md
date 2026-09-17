# 知识库证据与蒸馏规范

本文件用于维护知识库，不是比赛解题时的必读材料。

## 两级证据

- `references/data/paper_index.json` 是发现层。它覆盖全部 Markdown 论文，标题、摘要、关键词和片段可能由规则自动抽取，只能用于检索候选论文。
- `papers.json`、`subproblems.json`、`methods.json` 是蒸馏层。只有人工核验过原文、模型、验证和局限后，才可写入。

索引命中不等于论文结论可靠。不得直接把索引摘要中的性能数字、最优性声明或因果判断当作建模依据。

## 晋级为蒸馏记录的最低要求

1. 核验年份、题号、论文标题和源文件。
2. 阅读摘要、问题分析、模型建立、求解、检验与结论；不能只读摘要。
3. 在 `papers.json` 记录完整流程、验证方式、论文自报结果、优势、风险和可追溯证据位置。
4. 在 `subproblems.json` 按子问题拆分输入、输出、模型、算法、约束、指标、检验和风险。
5. 只有能跨论文复用的方法才合并到 `methods.json`，并保留来源论文 ID。
6. 将“论文声称”“从原文直接读取”“维护者推断”明确区分；无法核验的字段留空，不补写成事实。

## 质量异常处理

- `cid_tokens`：字体映射损坏。先换转换器、OCR 或人工查看原 PDF，再蒸馏。
- `missing_title` / `missing_abstract`：不得据文件名猜测论文结论。可在 `paper_index_overrides.json` 中添加已核验标题，并写明来源。
- `replacement_characters`：检查关键公式、变量名和数值是否损坏。
- `short_document`：优先确认 PDF 是否完整、是否只有图片或是否转换中断。

人工修正只解决定位和检索，不会自动把记录升级为 `curated`。

## 批次工作流

```powershell
python scripts/build_paper_index.py
python scripts/prepare_full_distillation.py
python scripts/migrate_kb_schema_v2.py
python scripts/auto_model.py decision-promote --check
python scripts/auto_model.py decision-promote
python scripts/auto_model.py kb-validate
python scripts/auto_model.py eval-retrieval
python scripts/auto_model.py query "关键词" --dataset index --year 2016 --topic A
python -m unittest discover -s tests -v
```

每次深度蒸馏建议按“年份 × 题目”成批处理。完成后重新构建索引，使对应记录从 `indexed` 变为 `curated`，并检查总数与唯一性。

全量蒸馏开始前运行 `prepare_full_distillation.py`。它会把 338 篇源文与
`references/data/full_distillation_manifest.json` 一一对应，并在
`build/distillation_packets/` 生成带原文行号的紧凑证据包。证据包只用于减少复核时
重复载入全文的 token 和时间；它不会自动把论文晋级为 `deeply_curated`。

按批次继续时可限定范围：

```powershell
python scripts/prepare_full_distillation.py --batch 2016-C
python scripts/promote_curation_batch.py references/data/curation_batches/2016-C.json
python scripts/build_paper_index.py
python scripts/prepare_full_distillation.py --batch 2016-D
```

每完成一个批次，必须把论文记录、子问题记录和必要的方法来源一起晋级，重新生成
索引与 manifest，并运行校验和检索评测。manifest 中的
`ready_with_quality_flags` 表示转换稿需要额外核查；`needs_source_repair` 表示在修复
来源前不得深度晋级。

论文事实蒸馏与决策字段蒸馏分两步。先在 `curation_batches/` 固定论文事实，再在 `decision_fields/` 填写约束、指标、最低基线和方法禁用条件。后者必须声明 `evidence_basis`；维护者归纳不得写成论文原始结论。
