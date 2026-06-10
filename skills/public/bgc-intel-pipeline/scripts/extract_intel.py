#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段 2 / 情报提取 (intelligence extraction)

输入：clean_dedup.py 产出的 cleaned.json
输出：每条帖子的结构化情报 records.json

抽取维度：
  - biz_categories  业务分类（基于黑话词典）
  - target_platforms 目标平台
  - prices          报价（金额 / 量纲）
  - contacts        联系方式（去混淆后正则匹配，含正文+评论）
  - jargon_hits     黑话命中
  - demand_signals  需求热度（评论区询单意向）
  - scam_disguise   反诈伪装话术命中（高可信度黑灰产指征）
  - risk_score      风险分 (0-100)
  - risk_tags       风险标签

用法：
  python extract_intel.py cleaned.json -o records.json [--lexicon ../references/bgc_lexicon.json]
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LEXICON = os.path.join(HERE, "..", "references", "bgc_lexicon.json")


def load_lexicon(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def deobfuscate(text, omap):
    if not text:
        return ""
    for k, v in omap.items():
        if k == "_comment":
            continue
        text = text.replace(k, v)
    return text


def gather_text(note):
    """正文 + 评论 合并文本（评论里往往藏着报价和需求信号）。"""
    c = note.get("_clean", {})
    parts = [c.get("full_text", "")]
    for cm in note.get("comments", []) or []:
        parts.append(cm.get("content", "") or "")
    return "\n".join(p for p in parts if p)


def gather_comments(note, limit=20):
    """保留评论用户名+内容，供下游按用户名称/内容挖掘黑话。"""
    out = []
    for cm in note.get("comments", []) or []:
        content = cm.get("content", "") or ""
        if not content:
            continue
        out.append({
            "user": cm.get("user", ""),
            "content": content[:220],
            "like_count": cm.get("like_count", 0),
        })
        if len(out) >= limit:
            break
    return out


def match_categories(text, lex):
    hits = {}
    for cat, cfg in lex["business_categories"].items():
        found = [kw for kw in cfg["keywords"] if kw.lower() in text.lower()]
        if found:
            hits[cat] = {"weight": cfg["weight"], "matched": sorted(set(found))}
    return hits


def match_platforms(text, lex):
    found = []
    low = text.lower()
    for plat, kws in lex["platforms"].items():
        if any(kw.lower() in low for kw in kws):
            found.append(plat)
    return sorted(set(found))


def match_jargon(text, lex):
    return sorted({j for j in lex["platform_jargon"] if j in text})


def extract_prices(text, lex):
    prices = []
    money_re = re.compile(lex["price_patterns"]["money_regex"], re.I)
    unit_re = re.compile(lex["price_patterns"]["unit_regex"], re.I)
    moneys = [(m.group(1), m.start()) for m in money_re.finditer(text)]
    units = [(u.group(0), u.start()) for u in unit_re.finditer(text)]
    for amt, pos in moneys:
        # 就近找量词（前后 25 字符内）
        near = ""
        for uval, upos in units:
            if abs(upos - pos) <= 25:
                near = uval
                break
        prices.append({"amount": amt, "near_unit": near.strip()})
    # 去重
    seen, out = set(), []
    for p in prices:
        key = (p["amount"], p["near_unit"])
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def extract_contacts(text, lex):
    contacts = []
    low = text
    for ctype, cfg in lex["contact_patterns"].items():
        if ctype == "_comment":
            continue
        triggers = cfg["trigger_words"]
        if not any(t.lower() in low.lower() for t in triggers):
            # phone 不依赖触发词
            if ctype != "phone":
                continue
        idre = re.compile(cfg["id_regex"])
        for tw in triggers + [""]:
            # 在触发词附近窗口找 id
            idx = 0
            hay = low.lower()
            twl = tw.lower()
            while tw and twl in hay[idx:]:
                p = hay.index(twl, idx)
                window = low[p: p + 40]
                m = idre.search(window[len(tw):])
                if m:
                    val = m.group(0)
                    contacts.append({"type": ctype, "value": val, "context": window.strip()})
                idx = p + len(tw)
            if not tw and ctype == "phone":
                for m in idre.finditer(low):
                    contacts.append({"type": "phone", "value": m.group(0),
                                     "context": low[max(0, m.start() - 10):m.start() + 21].strip()})
    # 去重
    seen, out = set(), []
    for c in contacts:
        key = (c["type"], c["value"])
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def demand_signals(note, lex):
    kws = lex["demand_signal_keywords"]["keywords"]
    samples = []
    count = 0
    for cm in note.get("comments", []) or []:
        content = cm.get("content", "") or ""
        if any(k in content for k in kws):
            count += 1
            if len(samples) < 5:
                samples.append({"user": cm.get("user", ""),
                                "content": content,
                                "like_count": cm.get("like_count", 0)})
    return {"inquiry_count": count, "samples": samples}


def scam_disguise(text, lex):
    kws = lex["scam_disguise_keywords"]["keywords"]
    return [k for k in kws if k in text]


def to_int(v):
    try:
        s = str(v).replace("+", "").strip()
        if s.endswith("w") or s.endswith("万"):
            return int(float(s[:-1]) * 10000)
        return int(s)
    except Exception:
        return 0


def risk_score(rec):
    """0-100 综合风险分。"""
    score = 0
    # 业务类别权重（取最高 + 其余递减）
    cat_weights = sorted((c["weight"] for c in rec["biz_categories"].values()), reverse=True)
    for i, w in enumerate(cat_weights):
        score += w * (1.0 if i == 0 else 0.4)
    # 联系方式越多越可疑（已落地交易通道）
    score += min(len(rec["contacts"]), 3) * 6
    # 报价存在 = 明确售卖
    score += 8 if rec["prices"] else 0
    # 需求热度（评论区询单）
    score += min(rec["demand_signals"]["inquiry_count"], 10) * 2
    # 反诈伪装话术（强指征）
    score += len(rec["scam_disguise"]) * 5
    # 黑话密度
    score += min(len(rec["jargon_hits"]), 5) * 2
    return min(int(round(score * 2.2)), 100)


def risk_tags(rec):
    tags = []
    if rec["contacts"]:
        tags.append("已露出联系方式")
    if rec["prices"]:
        tags.append("明码标价")
    if rec["scam_disguise"]:
        tags.append("反诈伪装话术")
    if rec["demand_signals"]["inquiry_count"] >= 5:
        tags.append("高需求热度")
    if rec["demand_signals"]["inquiry_count"] >= 3:
        tags.append("评论区导流")
    high = {"资金洗钱", "赌博诈骗", "违规技术"}
    if high & set(rec["biz_categories"].keys()):
        tags.append("高危业务类目")
    if rec.get("near_duplicate_count", 0) > 0:
        tags.append("批量铺量")
    return tags


def extract_one(note, lex):
    omap = lex["obfuscation_map"]
    raw_text = gather_text(note)
    text = deobfuscate(raw_text, omap)
    author = note.get("author", {}) or {}
    stats = note.get("stats", {}) or {}

    rec = {
        "note_id": note.get("note_id"),
        "platform": note.get("platform"),
        "source_keyword": note.get("source_keyword"),
        "publish_time": note.get("publish_time"),
        "link": note.get("link"),
        "author": {
            "user_id": author.get("user_id"),
            "nickname": author.get("nickname"),
            "ip_location": author.get("ip_location"),
        },
        "title": note.get("_clean", {}).get("title", ""),
        "desc_excerpt": (note.get("_clean", {}).get("desc", "") or "")[:160],
        "jargon_sources": {
            "author_nickname": author.get("nickname") or "",
            "content": raw_text[:1200],
            "comments": gather_comments(note),
        },
        "biz_categories": match_categories(text, lex),
        "target_platforms": match_platforms(text, lex),
        "prices": extract_prices(text, lex),
        "contacts": extract_contacts(text, lex),
        "jargon_hits": match_jargon(text, lex),
        "demand_signals": demand_signals(note, lex),
        "scam_disguise": scam_disguise(text, lex),
        "near_duplicate_count": len(note.get("_near_duplicates", []) or []),
        "engagement": {
            "liked": to_int(stats.get("liked_count", 0)),
            "collected": to_int(stats.get("collected_count", 0)),
            "comment": to_int(stats.get("comment_count", 0)),
            "share": to_int(stats.get("share_count", 0)),
        },
        "involved_user_ids": note.get("involved_user_ids", []) or [],
    }
    rec["risk_score"] = risk_score(rec)
    rec["risk_tags"] = risk_tags(rec)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="cleaned.json")
    ap.add_argument("-o", "--output", default="records.json")
    ap.add_argument("--lexicon", default=DEFAULT_LEXICON)
    args = ap.parse_args()

    lex = load_lexicon(args.lexicon)
    with open(args.input, "r", encoding="utf-8") as f:
        notes = json.load(f)

    records = [extract_one(n, lex) for n in notes]
    # 仅保留命中黑灰产特征的（至少一个业务类目）；其余记为 noise 计数
    intel = [r for r in records if r["biz_categories"]]
    noise = len(records) - len(intel)
    intel.sort(key=lambda r: r["risk_score"], reverse=True)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(intel, f, ensure_ascii=False, indent=2)

    meta = {
        "stage": "extract",
        "input": len(records),
        "intel": len(intel),
        "noise_filtered": noise,
    }
    meta_path = os.path.splitext(args.output)[0] + ".meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[extract] 输入 {len(records)} 条 -> 命中黑灰产情报 {len(intel)} 条 (过滤噪声 {noise} 条)")
    print(f"[extract] 输出 -> {args.output}")


if __name__ == "__main__":
    main()
