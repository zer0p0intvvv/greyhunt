#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段 3 / 分析 (analysis)

输入：extract_intel.py 产出的 records.json
输出：analysis.json —— 聚合统计 + 团伙聚类，供可视化使用。

团伙聚类思路（并查集 union-find）：把帖子按以下共享标识连成同一团伙：
  - 相同 author.user_id
  - 共享联系方式 (type+value)
  - 共享 involved_user_ids
  - 近似重复（铺量）通常已在去重阶段合并，这里按 author 再聚一层

用法：
  python analyze.py records.json -o analysis.json
"""
import argparse
import json
import os
import re
import urllib.error
import urllib.request
from collections import Counter, defaultdict


class UF:
    def __init__(self, items):
        self.p = {i: i for i in items}

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def filter_records_by_risk(records, min_risk=50):
    """最终明细口径：单帖 risk_score 必须严格大于阈值。"""
    if min_risk <= 0:
        return records, 0
    kept = [r for r in records if int(r.get("risk_score") or 0) > min_risk]
    return kept, len(records) - len(kept)


def cluster_gangs(records, min_peak_risk=0):
    """并查集聚类成团伙。

    min_peak_risk：团伙"峰值风险"（簇内最高 risk_score）阈值。
    峰值风险小于等于该值的整个团伙簇（含其全部帖子）直接剔除——
    单帖团伙等价于按该帖自身 risk_score 过滤；多帖团伙只要有一个高危成员就整簇保留，
    因为低分成员仍是高优先级团伙的一部分。返回 (保留的团伙, 保留的记录)。
    """
    ids = [r["note_id"] or f"_idx{i}" for i, r in enumerate(records)]
    for i, r in enumerate(records):
        r["_nid"] = ids[i]
    uf = UF(ids)

    # 建立标识 -> 帖子 的映射
    by_author = defaultdict(list)
    by_contact = defaultdict(list)
    by_involved = defaultdict(list)
    for r in records:
        aid = (r.get("author") or {}).get("user_id")
        if aid:
            by_author[aid].append(r["_nid"])
        for c in r.get("contacts", []):
            by_contact[(c["type"], c["value"])].append(r["_nid"])
        for uid in r.get("involved_user_ids", []):
            by_involved[uid].append(r["_nid"])

    for group in list(by_author.values()) + list(by_contact.values()) + list(by_involved.values()):
        for x in group[1:]:
            uf.union(group[0], x)

    clusters = defaultdict(list)
    rec_by_nid = {r["_nid"]: r for r in records}
    for nid in [r["_nid"] for r in records]:
        clusters[uf.find(nid)].append(nid)

    gangs = []
    gang_members = []  # 与 gangs 一一对应，保存每个簇的原始记录，便于过滤后回收
    for root, members in clusters.items():
        recs = [rec_by_nid[m] for m in members]
        authors = sorted({(r.get("author") or {}).get("nickname") for r in recs if (r.get("author") or {}).get("nickname")})
        ips = sorted({(r.get("author") or {}).get("ip_location") for r in recs if (r.get("author") or {}).get("ip_location")})
        contacts = sorted({f'{c["type"]}:{c["value"]}' for r in recs for c in r.get("contacts", [])})
        cats = Counter()
        for r in recs:
            for cat in r.get("biz_categories", {}):
                cats[cat] += 1
        gangs.append({
            "gang_id": None,  # 过滤+排序后统一编号
            "note_count": len(recs),
            "authors": authors,
            "ip_locations": ips,
            "shared_contacts": contacts,
            "top_categories": cats.most_common(3),
            "max_risk": max((r["risk_score"] for r in recs), default=0),
            "total_demand": sum(r["demand_signals"]["inquiry_count"] for r in recs),
            "note_ids": [r["note_id"] for r in recs],
        })
        gang_members.append(recs)

    # 按峰值风险过滤：max_risk <= 阈值 的整簇剔除（含其全部帖子）
    kept_gangs, kept_records = [], []
    dropped_gangs = dropped_notes = 0
    for g, recs in zip(gangs, gang_members):
        if g["max_risk"] > min_peak_risk:
            kept_gangs.append(g)
            kept_records.extend(recs)
        else:
            dropped_gangs += 1
            dropped_notes += len(recs)

    kept_gangs.sort(key=lambda g: (g["note_count"], g["max_risk"]), reverse=True)
    for i, g in enumerate(kept_gangs):
        g["gang_id"] = f"G{i+1:03d}"
    for r in records:
        r.pop("_nid", None)
    if min_peak_risk > 0:
        print(f"[analyze] 峰值风险<={min_peak_risk} 过滤：剔除 {dropped_gangs} 个团伙 / {dropped_notes} 条帖子")
    return kept_gangs, kept_records


def build_jargon_collection(records):
    """跨语料汇总黑话/类目命中词，产出按频次排序的搜索种子。

    用途：把整批情报里出现过的黑话集中起来，按热度排序，作为下一轮采集的搜索关键词
    （search_seeds），方便顺着黑话进一步扩大检索面。来源有两类：
      - 平台黑话命中 jargon_hits（橱窗/起号/养号…）
      - 各业务类目命中的关键词 biz_categories[cat]['matched']
    每个词附带出现次数、来源类型、共现的平台与业务类目，便于判断该用哪些词去搜。
    """
    term_count = Counter()
    term_type = {}
    term_platforms = defaultdict(set)
    term_categories = defaultdict(set)
    term_evidence = defaultdict(list)

    def sources_for(record):
        src = record.get("jargon_sources") or {}
        items = []
        nick = src.get("author_nickname") or (record.get("author") or {}).get("nickname") or ""
        if nick:
            items.append(("作者昵称", nick))
        content = src.get("content") or " ".join([record.get("title") or "", record.get("desc_excerpt") or ""])
        if content:
            items.append(("帖子内容", content))
        for cm in src.get("comments", []) or []:
            user = cm.get("user") or ""
            text = cm.get("content") or ""
            if user:
                items.append(("评论用户名", user))
            if text:
                items.append(("评论内容", text))
        return items

    def excerpt(text, term):
        pos = text.find(term)
        if pos < 0:
            return text[:80]
        return text[max(0, pos - 24): pos + len(term) + 36]

    def add_term(term, typ, record, field=None, text=None):
        term = (term or "").strip()
        if not term or len(term) < 2:
            return
        term_count[term] += 1
        term_type.setdefault(term, typ)
        term_platforms[term].update([p for p in record.get("target_platforms", []) if p])
        term_categories[term].update(record.get("biz_categories", {}).keys())
        if field and text and len(term_evidence[term]) < 3:
            term_evidence[term].append({
                "note_id": record.get("note_id"),
                "nickname": (record.get("author") or {}).get("nickname"),
                "field": field,
                "excerpt": excerpt(text, term),
            })

    def add_with_source(term, typ, record):
        matched = False
        for field, text in sources_for(record):
            if term in text:
                add_term(term, typ, record, field, text)
                matched = True
                break
        if not matched:
            add_term(term, typ, record)

    for r in records:
        for j in r.get("jargon_hits", []):
            add_with_source(j, "平台黑话", r)
        for cat, cfg in r.get("biz_categories", {}).items():
            for kw in cfg.get("matched", []):
                add_with_source(kw, "类目黑话", r)

    terms = []
    for term, cnt in term_count.most_common():
        terms.append({
            "term": term,
            "count": cnt,
            "type": term_type[term],
            "platforms": sorted(term_platforms[term]),
            "categories": sorted(term_categories[term]),
            "evidence": term_evidence[term],
        })
    return {
        "total_unique_terms": len(terms),
        "terms": terms,
        # 扁平、按频次降序、去重的搜索种子词，直接回灌采集器做下一轮检索
        "search_seeds": [t["term"] for t in terms],
    }


def extract_llm_jargon(records, api_key=None, model_endpoint=None, base_url=None, max_records=30):
    """用火山方舟 OpenAI-compatible 接口补充词典外黑话；失败时静默降级。"""
    api_key = api_key or os.getenv("ARK_API_KEY") or os.getenv("DOUBAO_API_KEY")
    model_endpoint = model_endpoint or os.getenv("ARK_MODEL_ENDPOINT") or os.getenv("DOUBAO_MODEL_ENDPOINT")
    base_url = (base_url or os.getenv("ARK_BASE_URL") or "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
    if not api_key or not model_endpoint:
        return []

    samples = []
    for r in sorted(records, key=lambda x: x.get("risk_score", 0), reverse=True)[:max_records]:
        src = r.get("jargon_sources") or {}
        comments = "；".join(
            f"{c.get('user','')}:{c.get('content','')}" for c in (src.get("comments") or [])[:5]
        )
        samples.append({
            "note_id": r.get("note_id"),
            "nickname": src.get("author_nickname") or (r.get("author") or {}).get("nickname"),
            "content": (src.get("content") or r.get("desc_excerpt") or "")[:700],
            "comments": comments[:500],
            "categories": list((r.get("biz_categories") or {}).keys()),
        })

    prompt = (
        "你是反诈/平台风控情报分析助手。请只从给定帖子作者昵称、正文、评论中抽取黑灰产黑话、隐晦业务词、交易暗语、平台规避词。"
        "不要生成操作建议，不要补充原文没有的词。返回 JSON 数组，每项包含 term、type、note_id、evidence。"
        "type 只能是 新黑话、隐晦业务词、联系方式暗语、平台规避词。"
    )
    payload = {
        "model": model_endpoint,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(samples, ensure_ascii=False)},
        ],
        "temperature": 0.1,
        "max_tokens": 1200,
    }
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        m = re.search(r"\[[\s\S]*\]", content)
        return json.loads(m.group(0) if m else content)
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as e:
        print(f"[analyze][warn] LLM 黑话提取失败，已降级为词典提取：{e}")
        return []


def merge_llm_jargon(collection, records, llm_terms):
    if not llm_terms:
        return collection
    by_id = {r.get("note_id"): r for r in records}
    terms = {t["term"]: t for t in collection["terms"]}
    for item in llm_terms:
        term = (item.get("term") or "").strip()
        if not term or len(term) < 2:
            continue
        rec = by_id.get(item.get("note_id")) or {}
        if term not in terms:
            terms[term] = {
                "term": term,
                "count": 0,
                "type": item.get("type") or "模型提取黑话",
                "platforms": [],
                "categories": [],
                "evidence": [],
            }
        t = terms[term]
        t["count"] += 1
        t["type"] = t["type"] if t["type"] != "模型提取黑话" else (item.get("type") or t["type"])
        t["platforms"] = sorted(set(t.get("platforms", [])) | set(rec.get("target_platforms", [])))
        t["categories"] = sorted(set(t.get("categories", [])) | set((rec.get("biz_categories") or {}).keys()))
        if len(t.get("evidence", [])) < 3:
            t.setdefault("evidence", []).append({
                "note_id": item.get("note_id"),
                "nickname": (rec.get("author") or {}).get("nickname"),
                "field": "LLM提取",
                "excerpt": item.get("evidence") or "",
            })
    ordered = sorted(terms.values(), key=lambda x: (x.get("count", 0), len(x.get("categories", []))), reverse=True)
    return {
        "total_unique_terms": len(ordered),
        "terms": ordered,
        "search_seeds": [t["term"] for t in ordered],
    }


def aggregate(records, gangs, min_peak_risk=60, min_risk=50, risk_filtered=0, llm_terms=None):
    cat_counter = Counter()
    plat_counter = Counter()
    ip_counter = Counter()
    keyword_counter = Counter()
    risk_buckets = {"高危(70-100)": 0, "中危(40-69)": 0, "低危(0-39)": 0}
    timeline = Counter()
    total_demand = 0
    contacts_total = 0

    for r in records:
        for cat in r["biz_categories"]:
            cat_counter[cat] += 1
        for p in r["target_platforms"]:
            plat_counter[p] += 1
        ip = (r.get("author") or {}).get("ip_location")
        if ip:
            ip_counter[ip] += 1
        if r.get("source_keyword"):
            keyword_counter[r["source_keyword"]] += 1
        s = r["risk_score"]
        if s >= 70:
            risk_buckets["高危(70-100)"] += 1
        elif s >= 40:
            risk_buckets["中危(40-69)"] += 1
        else:
            risk_buckets["低危(0-39)"] += 1
        total_demand += r["demand_signals"]["inquiry_count"]
        contacts_total += len(r["contacts"])
        pt = (r.get("publish_time") or "")[:10]
        if pt:
            timeline[pt] += 1

    return {
        "total_records": len(records),
        "total_gangs": len(gangs),
        "min_peak_risk": min_peak_risk,
        "min_record_risk": min_risk,
        "record_risk_filtered": risk_filtered,
        "total_demand_signals": total_demand,
        "total_contacts_exposed": contacts_total,
        "by_category": cat_counter.most_common(),
        "by_platform": plat_counter.most_common(),
        "by_ip": ip_counter.most_common(10),
        "by_source_keyword": keyword_counter.most_common(),
        "risk_distribution": risk_buckets,
        "jargon_collection": merge_llm_jargon(build_jargon_collection(records), records, llm_terms),
        "timeline": sorted(timeline.items()),
        "top_risk_notes": [
            {"note_id": r["note_id"], "title": r["title"] or r["desc_excerpt"][:40],
             "risk_score": r["risk_score"], "tags": r["risk_tags"],
             "nickname": (r.get("author") or {}).get("nickname")}
            for r in sorted(records, key=lambda x: x["risk_score"], reverse=True)[:15]
        ],
    }


def load_pipeline_stats(input_path, clean_meta=None, extract_meta=None):
    """汇总各阶段计数，供看板"数据全貌"展示端到端漏斗。

    自动探测：extract 边车默认在 `<records 同名>.meta.json`；clean 边车默认在
    records 同目录下的 `cleaned.meta.json`。也可用 --clean-meta / --extract-meta 显式指定。
    找不到时静默降级（看板只展示能算出的卡片）。
    """
    stats = {}
    cand_extract = extract_meta or (os.path.splitext(input_path)[0] + ".meta.json")
    cand_clean = clean_meta or os.path.join(os.path.dirname(os.path.abspath(input_path)), "cleaned.meta.json")
    for p in (cand_clean, cand_extract):
        try:
            with open(p, "r", encoding="utf-8") as f:
                stats.update(json.load(f))
        except Exception:
            pass
    stats.pop("stage", None)
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="records.json")
    ap.add_argument("-o", "--output", default="analysis.json")
    ap.add_argument("--min-peak-risk", type=int, default=60,
                    help="团伙峰值风险(簇内最高分)阈值，必须大于此值才保留；设 0 关闭过滤。默认 60")
    ap.add_argument("--min-risk", type=int, default=50,
                    help="单帖风险分阈值，必须大于此值才进入 analysis/dashboard 明细；设 0 关闭过滤。默认 50")
    ap.add_argument("--llm-jargon", action="store_true",
                    help="启用火山方舟大模型，从作者昵称/正文/评论中补充抽取词典外黑话")
    ap.add_argument("--llm-api-key", default=None,
                    help="方舟 API key；建议用环境变量 ARK_API_KEY，避免写入命令历史")
    ap.add_argument("--llm-endpoint", default=None,
                    help="方舟 endpoint/model id；也可用环境变量 ARK_MODEL_ENDPOINT")
    ap.add_argument("--llm-base-url", default=None,
                    help="OpenAI-compatible base URL，默认 https://ark.cn-beijing.volces.com/api/v3")
    ap.add_argument("--clean-meta", default=None, help="clean 阶段计数边车路径（默认自动探测）")
    ap.add_argument("--extract-meta", default=None, help="extract 阶段计数边车路径（默认自动探测）")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        records = json.load(f)

    records, risk_filtered = filter_records_by_risk(records, min_risk=args.min_risk)
    if args.min_risk > 0:
        print(f"[analyze] 单帖风险<={args.min_risk} 过滤：剔除 {risk_filtered} 条帖子")
    gangs, records = cluster_gangs(records, min_peak_risk=args.min_peak_risk)
    llm_terms = extract_llm_jargon(
        records,
        api_key=args.llm_api_key,
        model_endpoint=args.llm_endpoint,
        base_url=args.llm_base_url,
    ) if args.llm_jargon else None
    agg = aggregate(records, gangs, min_peak_risk=args.min_peak_risk,
                    min_risk=args.min_risk, risk_filtered=risk_filtered, llm_terms=llm_terms)
    agg["pipeline_stats"] = load_pipeline_stats(args.input, args.clean_meta, args.extract_meta)
    out = {"summary": agg, "gangs": gangs, "records": records}

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"[analyze] {len(records)} 条情报 -> {len(gangs)} 个团伙簇"
          f"（单帖风险>{args.min_risk}，峰值风险>{args.min_peak_risk}）")
    print(f"[analyze] 黑话搜索种子 {agg['jargon_collection']['total_unique_terms']} 个")
    print(f"[analyze] 输出 -> {args.output}")


if __name__ == "__main__":
    main()
