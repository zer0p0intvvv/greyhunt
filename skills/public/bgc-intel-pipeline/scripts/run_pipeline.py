#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键流水线：清洗去重 -> 情报提取 -> 分析 -> 可视化

用法：
  python run_pipeline.py <采集目录或文件> [-o 输出目录]

最终产出（默认在 ./bgc_out/）：
  dashboard.html / analysis_report.md
"""
import argparse
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def run(script, *args):
    cmd = [sys.executable]
    if sys.flags.no_site:
        cmd.append("-S")
    cmd.extend([os.path.join(HERE, script), *args])
    print("»", " ".join(os.path.basename(c) for c in cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(f"步骤失败：{script}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="采集产出目录或单个 JSON")
    ap.add_argument("-o", "--outdir", default="bgc_out")
    ap.add_argument("--sim", type=float, default=0.92)
    ap.add_argument("--min-risk", type=int, default=50,
                    help="单帖风险分阈值，必须大于此值才进入 analysis/dashboard 明细；0 关闭。默认 50")
    ap.add_argument("--min-peak-risk", type=int, default=60,
                    help="团伙峰值风险阈值，必须大于此值才保留；0 关闭。默认 60")
    ap.add_argument("--llm-jargon", action="store_true",
                    help="启用火山方舟大模型，从作者昵称/正文/评论中补充抽取黑话")
    ap.add_argument("--llm-endpoint", default=None,
                    help="方舟 endpoint/model id；也可用环境变量 ARK_MODEL_ENDPOINT")
    ap.add_argument("--llm-base-url", default=None,
                    help="OpenAI-compatible base URL，默认 https://ark.cn-beijing.volces.com/api/v3")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    dashboard = os.path.join(args.outdir, "dashboard.html")
    report = os.path.join(args.outdir, "analysis_report.md")

    with tempfile.TemporaryDirectory(prefix="bgc-intel-") as workdir:
        cleaned = os.path.join(workdir, "cleaned.json")
        records = os.path.join(workdir, "records.json")
        analysis = os.path.join(workdir, "analysis.json")

        run("clean_dedup.py", args.input, "-o", cleaned, "--sim", str(args.sim))
        run("extract_intel.py", cleaned, "-o", records)
        analyze_args = [
            records, "-o", analysis,
            "--min-risk", str(args.min_risk),
            "--min-peak-risk", str(args.min_peak_risk),
        ]
        if args.llm_jargon:
            analyze_args.append("--llm-jargon")
        if args.llm_endpoint:
            analyze_args.extend(["--llm-endpoint", args.llm_endpoint])
        if args.llm_base_url:
            analyze_args.extend(["--llm-base-url", args.llm_base_url])
        run("analyze.py", *analyze_args)
        run("build_dashboard.py", analysis, "-o", dashboard)
        run("build_report.py", analysis, "-o", report)

    print("\n完成 ✓ 最终交付：")
    print(f"- HTML 看板：{dashboard}")
    print(f"- 分析文档：{report}")


if __name__ == "__main__":
    main()
