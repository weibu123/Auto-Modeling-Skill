#!/usr/bin/env python3
"""Build traceable A-F subproblem decision batches from reviewed prose."""

from __future__ import annotations

import json
import re
from pathlib import Path

from kb_schema import split_segments


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "references" / "data"
OUT = DATA / "decision_fields"

PROFILES = {
    "A": (["资源、时序与可行域约束必须逐项验算", "比较方案使用相同目标函数与计算预算"], ["目标函数值", "约束违例率", "运行时间与稳定性"]),
    "B": (["训练、调参与最终评估严格隔离", "变量定义、单位和样本对应关系全流程一致"], ["独立集误差", "校准与稳定性", "相对简单基线的增益"]),
    "C": (["物理单位、坐标和标定参数保持一致", "中间结果满足已知物理范围和边界条件"], ["重构或预测误差", "物理一致性残差", "参数敏感性"]),
    "D": (["时间与空间依赖单元不得跨越训练和验证", "多源数据的坐标、分辨率和时间口径统一"], ["时空留出误差", "空间覆盖与极端事件误差", "尺度敏感性"]),
    "E": (["按视频、设备或事件单元隔离训练和评估", "上游识别误差必须传递到下游决策"], ["事件级准确率或误差", "误报漏报与时延", "下游决策约束违例"]),
    "F": (["坐标系、时间尺度、符号和单位明确且统一", "通过解析极限、反算或守恒量检查内部一致性"], ["绝对与相对误差", "残差量级", "数值稳定性"]),
}


def task_metrics(record: dict) -> list[str]:
    text = " ".join(str(record.get(key, "")) for key in ("task", "model", "output", "validation"))
    rules = [
        (r"分类|识别|诊断", ["宏平均F1或平衡准确率", "混淆矩阵与类别利益"]),
        (r"预测|回归|估计|拟合", ["MAE/RMSE与R²", "残差分层误差"]),
        (r"聚类|分区", ["簇稳定性", "下游任务表现"]),
        (r"优化|路径|调度|分配|选址", ["目标函数值", "可行率与计算时间"]),
        (r"检验|显著|关联", ["校正后显著性", "效应量与置信区间"]),
    ]
    for pattern, metrics in rules:
        if re.search(pattern, text, re.IGNORECASE):
            return metrics
    return []


def main() -> int:
    records = json.loads((DATA / "subproblems.json").read_text(encoding="utf-8"))["records"]
    generated = 0
    for topic in "ABCDEF":
        items = []
        base_constraints, base_metrics = PROFILES[topic]
        for record in records:
            if not str(record.get("paper_id", "")).startswith(topic) or record.get("constraints"):
                continue
            validation = split_segments(record.get("validation"))
            constraints = list(base_constraints)
            if validation:
                constraints.append("验收时复核：" + validation[0])
            metrics = list(dict.fromkeys(task_metrics(record) + base_metrics))[:4]
            items.append({
                "record_id": record["record_id"],
                "constraints": constraints,
                "metric": metrics,
                "decision_field_quality": "reviewed-prose-normalization",
            })
        if not items:
            continue
        payload = {
            "batch_id": f"subproblems-{topic.lower()}-reviewed-v1",
            "evidence_basis": "从已深度蒸馏的任务、输入输出、验证和风险字段中结构化归纳，并按领域验证原则复核；不新增论文性能结论。",
            "subproblems": items,
            "methods": [],
        }
        (OUT / f"subproblems-{topic.lower()}-reviewed-v1.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        generated += len(items)
    print(f"Generated {generated} reviewed-prose subproblem decisions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
