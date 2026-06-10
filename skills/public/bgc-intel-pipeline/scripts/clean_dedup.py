#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段 1 / 清洗去重 (clean & dedup)

输入：一个目录或单个 JSON 文件（采集产出）。兼容三种结构：
  1) 顶层是 list[note]
  2) 顶层是 {"notes": [...]}
  3) 顶层是单个 note 对象
输出：归一化后的 notes 数组（去重 + 字段标准化 + 噪声过滤）。

去重策略（按优先级）：
  - 精确去重：note_id 相同视为同一条，保留互动数据更全的一条。
  - 近似去重：标题+正文做 SimHash 风格的归一化指纹，文本高度相似(默认>0.92)视为重复发帖（同一团伙铺量常见）。

用法：
  python clean_dedup.py <input_dir_or_file> -o cleaned.json
"""
import argparse
import json
import os
import re
import sys
import hashlib
from collections import defaultdict

WS_RE = re.compile(r"\s+")
TAG_RE = re.compile(r"#[^#\[\]]+(?:\[话题\])?#|\[话题\]|\[搜索高亮\]")
EMOJI_TAG_RE = re.compile(r"\[[^\]]{1,6}R\]")  # 小红书表情如 [赞R]


def load_any(path):
    """从目录或文件递归收集所有 note。"""
    notes = []
    files = []
    if os.path.isdir(path):
        for root, _, fnames in os.walk(path):
            for fn in fnames:
                if fn.endswith(".json"):
                    files.append(os.path.join(root, fn))
    else:
        files = [path]

    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[warn] 跳过无法解析的文件 {fp}: {e}", file=sys.stderr)
            continue
        if isinstance(data, list):
            batch = data
        elif isinstance(data, dict) and "notes" in data:
            batch = data["notes"]
        elif isinstance(data, dict):
            batch = [data]
        else:
            continue
        for n in batch:
            if isinstance(n, dict):
                n.setdefault("_source_files", [os.path.basename(fp)])
                notes.append(n)
    return notes


def normalize_text(s):
    if not s:
        return ""
    s = TAG_RE.sub(" ", s)
    s = EMOJI_TAG_RE.sub(" ", s)
    s = WS_RE.sub(" ", s)
    return s.strip()


def text_fingerprint(s):
    """字符 3-gram 集合，用于近似去重的 Jaccard 相似度。"""
    s = re.sub(r"[^\u4e00-\u9fffa-zA-Z0-9]", "", s.lower())
    if len(s) < 3:
        return frozenset([s]) if s else frozenset()
    return frozenset(s[i:i + 3] for i in range(len(s) - 2))


def jaccard(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def engagement_score(note):
    st = note.get("stats", {}) or {}
    def to_int(v):
        try:
            return int(str(v).replace("w", "0000").replace("万", "0000").replace("+", ""))
        except Exception:
            return 0
    return sum(to_int(st.get(k, 0)) for k in
               ("liked_count", "collected_count", "comment_count", "share_count"))


def standardize(note):
    """统一字段，方便下游提取。原始字段保留。"""
    content = note.get("content", {}) or {}
    note["_clean"] = {
        "title": normalize_text(content.get("title", "")),
        "desc": normalize_text(content.get("desc", "")),
        "full_text": normalize_text(
            (content.get("title", "") or "") + " " + (content.get("desc", "") or "")
        ),
        "engagement": engagement_score(note),
    }
    return note


def dedup(notes, sim_threshold=0.92):
    # 1) note_id 精确去重
    by_id = {}
    no_id = []
    for n in notes:
        nid = n.get("note_id")
        if not nid:
            no_id.append(n)
            continue
        if nid not in by_id or engagement_score(n) > engagement_score(by_id[nid]):
            # 合并来源文件
            if nid in by_id:
                src = set(by_id[nid].get("_source_files", [])) | set(n.get("_source_files", []))
                n["_source_files"] = sorted(src)
            by_id[nid] = n
    deduped = list(by_id.values()) + no_id

    # 2) 文本近似去重（铺量识别）
    kept = []
    fingerprints = []
    dup_clusters = 0
    for n in sorted(deduped, key=engagement_score, reverse=True):
        fp = text_fingerprint(n.get("_clean", {}).get("full_text", "") or
                              ((n.get("content", {}) or {}).get("desc", "") or ""))
        is_dup = False
        for kfp, kn in fingerprints:
            if jaccard(fp, kfp) >= sim_threshold:
                kn.setdefault("_near_duplicates", []).append(n.get("note_id"))
                is_dup = True
                dup_clusters += 1
                break
        if not is_dup:
            kept.append(n)
            fingerprints.append((fp, n))
    return kept, len(deduped), dup_clusters


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="采集产出目录或单个 JSON 文件")
    ap.add_argument("-o", "--output", default="cleaned.json")
    ap.add_argument("--sim", type=float, default=0.92, help="近似去重阈值")
    args = ap.parse_args()

    raw = load_any(args.input)
    raw = [standardize(n) for n in raw]
    kept, after_id, near_dups = dedup(raw, args.sim)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    # 写出阶段计数边车（供看板"数据全貌"展示漏斗数字）
    meta = {
        "stage": "clean",
        "raw": len(raw),
        "after_id_dedup": after_id,
        "near_dup_removed": near_dups,
        "kept": len(kept),
        "dedup_removed": len(raw) - len(kept),
        "source_keywords": len({n.get("source_keyword") for n in raw if n.get("source_keyword")}),
    }
    meta_path = os.path.splitext(args.output)[0] + ".meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[clean] 原始 {len(raw)} 条 -> ID去重后 {after_id} 条 -> 文本近似去重后 {len(kept)} 条 "
          f"(近似重复 {near_dups} 条)")
    print(f"[clean] 输出 -> {args.output}")


if __name__ == "__main__":
    main()
