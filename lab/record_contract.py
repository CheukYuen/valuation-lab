#!/usr/bin/env python3
"""关键数字记录契约校验器（第1课可选实验）。

    python3 lab/record_contract.py                          校验全部样本
    python3 lab/record_contract.py cases/00-records/a.json   校验一条记录

它实现 course/DAY-1.md 里已经写死的语义校验和 PIT 序关系，不新造词表：
每个 code 对应失败状态矩阵里的一行。

这个脚本是可选验证工具。第1课不运行它也能完成——纸面判断才是本课的正体，
脚本只负责让"我的判断可以被复算"这件事成立。

它不判断数字对不对，只判断这条记录是否说清了自己是什么。
一条通过全部校验的记录仍然可能基于错误的经营假设。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "cases" / "00-records"

# code -> (失败状态矩阵里的返回值, 严重性)。不要新增词表以外的 code。
STATES = {
    "consensus": ("单家外部预测；共识无法确认", "重大"),
    "pit": ("未来信息污染", "致命"),
    "bridge": ("内部假设，部分可用或无法确认", "重大"),
    "evidence": ("证据指针缺失", "重大"),
    "recompute": ("尚未程序复核", "重大"),
    "conflict": ("明确错误", "致命"),
    "semantics": ("语义不完整，无法确认", "重大"),
}

NATURES = {"fact", "guidance", "forecast", "assumption", "derived", "judgment"}
DATE_FIELDS = ("source_published_at", "adopted_at", "research_as_of")

# 证据指针要落到文件、页码、表格单元格或可复取记录，而不是只保存机构名或网站首页。
POINTER_MARKS = ("页", "表", "行", "单元格", "cell", "Sheet", "#", "::")


class Finding:
    """一条发现：说清是什么状态、哪个字段、为什么，以及还不能断言什么。"""

    def __init__(self, code, field, message):
        self.code = code
        self.field = field
        self.message = message
        self.state, self.severity = STATES[code]

    def __repr__(self):
        return f"Finding({self.code!r}, {self.field!r})"

    def line(self):
        return f"[{self.severity}] {self.code:<10} {self.field:<22} {self.message}\n{'':>13}→ 应返回：{self.state}"


def _missing(record, field):
    value = record.get(field)
    return value is None or (isinstance(value, str) and not value.strip())


def validate_record(record):
    """返回 list[Finding]。空列表表示语义完整，不表示数字正确。"""
    findings = []

    # 1. value 与 unit 同时存在；百分比、小数和金额不能靠字段名猜测。
    if _missing(record, "value") or _missing(record, "unit"):
        findings.append(Finding("semantics", "value/unit", "数值与单位必须同时存在，不能靠字段名推断量纲"))
    if not _missing(record, "unit") and _missing(record, "currency") and "%" not in str(record.get("unit", "")):
        findings.append(Finding("semantics", "currency", "金额类记录必须写明币种，人民币与港币不能靠上下文猜"))

    # 2. subject 必须落到发行人、证券或分部。
    if _missing(record, "subject"):
        findings.append(Finding("semantics", "subject", "缺少估值对象；发行人、证券和分部不能混用"))

    # 3. period_end 与 as_of 分开，财务期间不能冒充估值日。
    if _missing(record, "period_end"):
        findings.append(Finding("semantics", "period_end", "缺少报告期；财务期间不能由估值日代替"))
    if _missing(record, "research_as_of"):
        findings.append(Finding("semantics", "research_as_of", "缺少研究时点，PIT 序关系无法检查"))

    # 4. 信息性质必须在六类之内。
    nature = record.get("nature")
    if nature not in NATURES:
        findings.append(Finding("semantics", "nature", f"信息性质必须是六类之一 {sorted(NATURES)}，收到 {nature!r}"))

    # 5. PIT：source_published_at <= adopted_at <= research_as_of。
    dates = [record.get(field) for field in DATE_FIELDS]
    if all(isinstance(d, str) and d for d in dates):
        published, adopted, as_of = dates
        if published > as_of:
            findings.append(Finding("pit", "source_published_at", f"来源发布日 {published} 晚于研究时点 {as_of}"))
        elif adopted > as_of:
            findings.append(Finding("pit", "adopted_at", f"采用日 {adopted} 晚于研究时点 {as_of}"))
        elif published > adopted:
            findings.append(Finding("pit", "adopted_at", f"采用日 {adopted} 早于来源发布日 {published}"))
    elif nature != "judgment":
        findings.append(Finding("semantics", "/".join(DATE_FIELDS), "三个时间字段必须齐全且可比较"))

    # 6. 外部预测：单家来源不能命名为共识；汇总必须有样本、方法和截点。
    if nature == "forecast":
        consensus = record.get("consensus")
        if record.get("labelled_as_consensus") and not consensus:
            findings.append(Finding("consensus", "labelled_as_consensus", "被命名为共识，却没有样本、统计方法和截点"))
        elif isinstance(consensus, dict):
            gaps = [key for key in ("sample_size", "method", "cutoff") if _missing(consensus, key)]
            if gaps:
                findings.append(Finding("consensus", "consensus", f"汇总预测缺少 {gaps}，不能称为共识"))

    # 7. 发生换汇、年化、调整或汇总时，保留原值、变换规则和派生值。
    transform = record.get("transform")
    if isinstance(transform, dict):
        gaps = [key for key in ("rule", "from_value", "bridge") if _missing(transform, key)]
        if gaps:
            findings.append(Finding("bridge", "transform", f"发生了变换但缺少 {gaps}；调整后数字没有逐项桥"))

    # 8. 派生计算保存输入版本、公式或程序版本，以及独立重算结果。
    if nature == "derived":
        computation = record.get("computation")
        if not isinstance(computation, dict):
            findings.append(Finding("recompute", "computation", "派生值必须保存输入版本、公式和重算结果"))
        else:
            gaps = [key for key in ("inputs_version", "formula", "recomputed_by") if _missing(computation, key)]
            if gaps:
                findings.append(Finding("recompute", "computation", f"派生值缺少 {gaps}；引用不能代替复算"))
            elif str(computation.get("recomputed_by", "")).startswith("model:"):
                findings.append(Finding("recompute", "computation.recomputed_by",
                                        "另一个语言模型复述不是独立计算；需要确定性程序或可检查公式"))

    # 9. 证据指针要能定位到文件、页码、单元格或可复取记录。
    evidence = record.get("evidence_pointer")
    if _missing(record, "evidence_pointer"):
        findings.append(Finding("evidence", "evidence_pointer", "缺少证据指针；来源身份不能代替定位信息"))
    elif isinstance(evidence, str) and not any(mark in evidence for mark in POINTER_MARKS):
        findings.append(Finding("evidence", "evidence_pointer",
                                f"证据指针 {evidence!r} 定位不到页码、表格或可复取记录"))

    # 10. 记录值与原始证据直接冲突。
    quoted = record.get("source_value")
    if quoted is not None and record.get("value") is not None and quoted != record.get("value") and not transform:
        findings.append(Finding("conflict", "value", f"记录值 {record['value']} 与原文 {quoted} 冲突，且没有声明任何变换"))

    return findings


def report(path):
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    findings = validate_record(record)
    print(f"\n{path}")
    print(f"  {record.get('label', '(无标签)')}")
    if not findings:
        print("  语义完整：没有触发任何失败状态。")
        print("  注意：这只说明这条记录说清了自己是什么，不说明数字或经营假设正确。")
        return 0
    for finding in findings:
        print(f"  {finding.line()}")
    return len(findings)


def main(argv):
    paths = [Path(a) for a in argv[1:]] or sorted(SAMPLES.glob("*.json"))
    if not paths:
        print(f"没有找到样本：{SAMPLES}", file=sys.stderr)
        return 1
    total = sum(report(path) for path in paths)
    print(f"\n合计 {total} 条发现，来自 {len(paths)} 条记录。")
    print("发现数量不等于严重性排序；请按对本次结论的影响判断。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
