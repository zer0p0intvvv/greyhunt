#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段 5 / 分析文档 (report)

输入：analyze.py 产出的 analysis.json
输出：面向处置和复盘的 Markdown 分析文档。

用法：
  python build_report.py analysis.json -o analysis_report.md
"""
import argparse
import json
from datetime import datetime


def md_escape(value):
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def table(headers, rows):
    if not rows:
        return "无数据\n"
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        out.append("| " + " | ".join(md_escape(v) for v in row) + " |")
    return "\n".join(out) + "\n"


def top_pairs(pairs, limit=10):
    return pairs[:limit] if pairs else []


def render_report(analysis):
    summary = analysis.get("summary", {})
    gangs = analysis.get("gangs", [])
    records = analysis.get("records", [])
    pipeline = summary.get("pipeline_stats", {})
    jargon = summary.get("jargon_collection", {})
    risk = summary.get("risk_distribution", {})
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    top_gangs = []
    for gang in gangs[:10]:
        top_gangs.append([
            gang.get("gang_id", ""),
            gang.get("max_risk", 0),
            gang.get("note_count", 0),
            "、".join(gang.get("authors") or []) or "未知",
            "、".join(f"{c[0]}×{c[1]}" for c in gang.get("top_categories", [])) or "未知",
            gang.get("total_demand", 0),
        ])

    top_notes = []
    for rec in sorted(records, key=lambda r: r.get("risk_score", 0), reverse=True)[:15]:
        cats = "、".join((rec.get("biz_categories") or {}).keys())
        tags = "、".join(rec.get("risk_tags") or [])
        top_notes.append([
            rec.get("risk_score", 0),
            rec.get("note_id", ""),
            (rec.get("author") or {}).get("nickname") or "未知",
            rec.get("title") or rec.get("desc_excerpt") or "",
            cats,
            tags,
        ])

    seed_rows = []
    for term in (jargon.get("terms") or [])[:30]:
        evidence = ""
        if term.get("evidence"):
            ev = term["evidence"][0]
            evidence = f"{ev.get('field', '')}: {ev.get('excerpt', '')}"
        seed_rows.append([
            term.get("term", ""),
            term.get("count", 0),
            term.get("type", ""),
            "、".join(term.get("platforms") or []),
            "、".join(term.get("categories") or []),
            evidence,
        ])

    lines = [
        "# 黑灰产情报分析报告",
        "",
        f"- 生成时间：{generated_at}",
        f"- 情报明细阈值：risk_score > {summary.get('min_record_risk', 50)}",
        f"- 团伙聚类阈值：max_risk > {summary.get('min_peak_risk', 60)}",
        f"- 最终情报：{summary.get('total_records', 0)} 条",
        f"- 团伙簇：{summary.get('total_gangs', 0)} 个",
        f"- 需求询单信号：{summary.get('total_demand_signals', 0)} 个",
        f"- 露出联系方式：{summary.get('total_contacts_exposed', 0)} 个",
        "",
        "## 数据漏斗",
        "",
        table(
            ["阶段", "数量"],
            [
                ["原始采集", pipeline.get("raw", "未知")],
                ["去重后", pipeline.get("kept", "未知")],
                ["噪声过滤", pipeline.get("noise_filtered", "未知")],
                ["风险分过滤", summary.get("record_risk_filtered", 0)],
                ["最终情报", summary.get("total_records", 0)],
                ["最终团伙", summary.get("total_gangs", 0)],
            ],
        ),
        "## 风险分布",
        "",
        table(["风险段", "数量"], risk.items()),
        "## 业务类目 TOP",
        "",
        table(["类目", "数量"], top_pairs(summary.get("by_category", []))),
        "## 目标平台 TOP",
        "",
        table(["平台", "数量"], top_pairs(summary.get("by_platform", []))),
        "## 属地来源 TOP",
        "",
        table(["属地", "数量"], top_pairs(summary.get("by_ip", []))),
        "## 高优先级团伙",
        "",
        table(["团伙ID", "峰值风险", "帖子数", "运营号", "主要类目", "询单热度"], top_gangs),
        "## 高风险情报明细",
        "",
        table(["风险分", "帖子ID", "作者", "标题/摘要", "类目", "风险标签"], top_notes),
        "## 黑话搜索种子",
        "",
        table(["黑话", "频次", "类型", "平台", "类目", "证据样本"], seed_rows),
        "## 处置建议",
        "",
        "- 优先核查峰值风险最高的团伙簇，尤其是同时出现联系方式、报价、评论询单和反诈伪装话术的记录。",
        "- 将黑话搜索种子回灌采集器，围绕高频词和团伙共现平台进行下一轮扩面采集。",
        "- 对共享联系方式、相同作者 ID、重复文案形成的团伙关联进行人工复核，再进入平台处置或执法协作流程。",
        "",
        "## 合规说明",
        "",
        "本报告仅用于反诈、平台风控、信任与安全治理、安全研究等防御性场景。联系方式和黑话仅作为情报线索，不应用于联系、交易或实施任何违法违规活动。",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="analysis.json")
    ap.add_argument("-o", "--output", default="analysis_report.md")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        analysis = json.load(f)
    report = render_report(analysis)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[report] 输出 -> {args.output}")


if __name__ == "__main__":
    main()
