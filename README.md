# Huawei Cup Mathematical Modeling Skill

面向“华为杯”中国研究生数学建模竞赛的 Codex Skill，用于赛题拆解、数据审计、模型选择、验证设计、实现规划、论文写作与终稿检查。

## 主要能力

- 将多问赛题整理为目标、输入、输出、约束、指标和依赖关系明确的问题图。
- 根据数据结构选择可复现基线，并在有证据时升级为物理—数据混合、优化、时空、深度学习或多目标方法。
- 检查时间、空间、个体、设备和文件级数据泄漏。
- 为预测、优化、评价、重构、仿真和实时决策设计验证矩阵。
- 从整理后的优秀论文知识库检索相似任务、可复用方法链和常见风险。

## 知识库

当前版本包含：

- 44 篇华为杯优秀论文的论文级结构化记录；
- 164 条子问题记录；
- 66 条方法记录。


## 安装

将仓库克隆到 Codex Skills 目录：

```bash
git clone <repository-url> ~/.codex/skills/Auto-Modeling-Skill
```


## 使用

显式调用示例：

```text
使用 Auto-Modeling-Skill 分析这道华为杯赛题，先完成问题拆解和数据审计，再比较候选模型并给出验证方案。
```

查询本地知识库：

```bash
python3 scripts/query_kb.py --query "多目标优化 疲劳 功率分配" --dataset all --limit 8
python3 scripts/query_kb.py --query "空间泄漏 脆弱性" --dataset subproblems --topic D --limit 6
```

## 目录结构

```text
Auto-Modeling-modeling/
├── SKILL.md
├── agents/openai.yaml
├── scripts/query_kb.py
└── references/
    ├── competition-workflow.md
    ├── problem-routing.md
    ├── validation-and-audit.md
    ├── paper-writing.md
    └── data/
        ├── papers.json
        ├── subproblems.json
        └── methods.json
```

## 验证

```bash
python3 scripts/query_kb.py --query "脉冲星 相对论时延 光子仿真" --topic F
```

Skill 的结构可使用 Codex `skill-creator` 提供的 `quick_validate.py` 检查。
