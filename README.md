# Auto Modeling Skill

面向“华为杯”中国研究生数学建模竞赛的可安装 Agent Skill。它把赛题拆解、数据审计、模型选择、代码实现、验证设计和 LaTeX 论文交付串成一条可复现工作流，并内置 44 篇优秀论文的结构化知识库。

项目不是“一键生成答案”的黑箱。脚本负责确定性工作，Agent 负责需要判断的工作：

- `init`：创建标准参赛目录、建模笔记和论文骨架；
- `query`：检索 44 篇论文、164 条子问题和 66 条方法记录；
- `audit`：检查材料完整性、占位符、结果来源和论文交付状态；
- `doctor`：检查 Python、XeLaTeX 和中文论文模板所需宏包；
- `$auto-modeling-skill`：在题目与附件基础上完成问题拆解、建模、实现、验证和写作协作。

## 安装

### Codex

```bash
git clone https://github.com/weibu123/Auto-Modeling-Skill.git ~/.codex/skills/auto-modeling-skill
```

重新打开 Codex 后，可显式调用：

```text
使用 $auto-modeling-skill 分析这道华为杯赛题。先审计题目和附件，再给出问题图、基线、主模型链和验证矩阵。
```

也可把仓库复制到当前项目的 `.codex/skills/auto-modeling-skill/`，作为项目级 Skill 使用。

## 可运行命令

在仓库根目录执行：

```bash
# 1. 创建一套含 4 个子问题的参赛工作区
python3 scripts/auto_model.py init ./contest-2026 --questions 4

# 2. 从优秀论文知识库检索可迁移方案与风险
python3 scripts/auto_model.py query "多目标优化 疲劳 功率分配" --dataset all --limit 8

# 3. 检查参赛材料和论文交付是否完整
python3 scripts/auto_model.py audit ./contest-2026

# 4. 检查本机能否编译中文 LaTeX 模板
python3 scripts/auto_model.py doctor
```

完整参数：

```bash
python3 scripts/auto_model.py --help
python3 scripts/auto_model.py init --help
python3 scripts/auto_model.py query --help
python3 scripts/auto_model.py audit --help
python3 scripts/auto_model.py doctor --help
```

命令本身仅依赖 Python 3.10+ 标准库。生成中文论文 PDF 还需要 XeLaTeX 及 `ctex` 等宏包；先运行 `doctor` 可以看到缺失项。

## 标准工作区

`init` 默认生成：

```text
contest-2026/
├── 题目/                 # 原始题目，只读保留
├── 数据/
│   ├── 原始/             # 原始附件，只读保留
│   └── 处理/             # 可复现的中间数据
├── 问题1/ ... 问题N/
│   ├── 建模笔记.md
│   ├── 代码/
│   └── 结果/
├── 论文/
│   ├── 论文.tex
│   ├── figures/
│   └── tables/
├── 参考资料/
└── 比赛状态.md
```

## 知识库边界

知识库中的历史结果均为原论文作者自报，不能替代当前赛题上的复现、验证或证明。检索时优先匹配任务结构、数据形式、约束和验证方式，不按算法名称机械套用。仓库不包含原始论文 PDF。

## 项目结构

```text
auto-modeling-skill/
├── SKILL.md
├── agents/openai.yaml
├── assets/                     # 初始化工作区时复制的模板
├── references/                 # 工作流、模型路由、验证与写作规范
│   └── data/                   # 44 篇论文结构化知识库
├── scripts/                    # init / query / audit 命令
└── tests/                      # 标准库 smoke tests
```

## 验证

```bash
python3 -m unittest discover -s tests -v
```

## 设计说明

本项目吸收了 [cumcm-paper-hand-skill](https://github.com/Mr-Potato-123/cumcm-paper-hand-skill) 在“可安装目录、参赛工作区、LaTeX 模板、交付检查闭环”方面的产品化思路；具体指令、脚本、模板与知识库均在本项目中独立实现。前者侧重论文写作，本项目定位为研究生数学建模竞赛的全流程工作台。

## License

MIT
