# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#
# 声明：本代码仅供学习和研究目的使用。

"""
小红书数据导出工具
将 SQLite 中的 xhs_note + xhs_note_comment 整合为结构化 JSON
用于黑灰产账号/卖家识别分析
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "database" / "sqlite_tables.db"
OUT_PATH = Path(__file__).parent.parent / "data" / "export"


def ts_to_str(ts) -> str:
    """毫秒或秒级时间戳 → 可读字符串"""
    if not ts:
        return ""
    try:
        v = int(ts)
        if v > 1_000_000_000_000:
            v //= 1000
        return datetime.fromtimestamp(v).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts)


def load_notes(cur, keyword_filter: str = None) -> list:
    sql = """
        SELECT note_id, user_id, nickname, avatar, ip_location,
               title, desc, type, tag_list, image_list, video_url,
               time, add_ts, note_url, source_keyword,
               liked_count, collected_count, comment_count, share_count
        FROM xhs_note
    """
    params = []
    if keyword_filter:
        sql += " WHERE source_keyword LIKE ?"
        params.append(f"%{keyword_filter}%")
    sql += " ORDER BY add_ts DESC"
    cur.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def load_comments_for_note(cur, note_id: str) -> dict:
    """返回 {comment_id: {comment_data, sub_comments: []}}"""
    cur.execute("""
        SELECT comment_id, user_id, nickname, ip_location,
               content, create_time, add_ts, like_count,
               sub_comment_count, parent_comment_id, pictures
        FROM xhs_note_comment
        WHERE note_id = ?
        ORDER BY create_time ASC
    """, (note_id,))
    rows = [dict(r) for r in cur.fetchall()]

    top_level = {}   # comment_id -> comment dict
    sub_map = {}     # parent_comment_id -> [sub_comment, ...]

    for row in rows:
        pid = str(row.get("parent_comment_id") or "0")
        if pid in ("0", "", None):
            top_level[row["comment_id"]] = {
                "comment_id": row["comment_id"],
                "user_id": row["user_id"],
                "nickname": row["nickname"],
                "ip_location": row.get("ip_location") or "",
                "content": row["content"],
                "create_time": ts_to_str(row["create_time"]),
                "like_count": row.get("like_count") or "0",
                "sub_comment_count": row.get("sub_comment_count") or 0,
                "sub_comments": [],
            }
        else:
            sub_map.setdefault(pid, []).append({
                "comment_id": row["comment_id"],
                "user_id": row["user_id"],
                "nickname": row["nickname"],
                "ip_location": row.get("ip_location") or "",
                "content": row["content"],
                "create_time": ts_to_str(row["create_time"]),
                "like_count": row.get("like_count") or "0",
                "parent_comment_id": pid,
            })

    # 把子评论挂到父评论下
    for cid, subs in sub_map.items():
        if cid in top_level:
            top_level[cid]["sub_comments"] = subs
        else:
            # 父评论不在 top_level（可能被平台删除），作为孤立条目补充
            top_level[f"__orphan_{cid}"] = {
                "comment_id": cid,
                "user_id": "",
                "nickname": "[已删除]",
                "ip_location": "",
                "content": "",
                "create_time": "",
                "like_count": "0",
                "sub_comment_count": len(subs),
                "sub_comments": subs,
            }

    return list(top_level.values())


def build_record(note: dict, comments: list) -> dict:
    tags = []
    try:
        raw = note.get("tag_list") or "[]"
        parsed = json.loads(raw)
        tags = parsed if isinstance(parsed, list) else [parsed]
    except Exception:
        tags = [note.get("tag_list")] if note.get("tag_list") else []

    # 收集本笔记涉及的所有唯一 user_id（作者 + 评论者）
    involved_user_ids = {note["user_id"]}
    for c in comments:
        if c.get("user_id"):
            involved_user_ids.add(c["user_id"])
        for s in c.get("sub_comments", []):
            if s.get("user_id"):
                involved_user_ids.add(s["user_id"])

    return {
        "platform": "xiaohongshu",
        "note_id": note["note_id"],
        "author": {
            "user_id": note["user_id"],
            "nickname": note["nickname"],
            "avatar": note.get("avatar") or "",
            "ip_location": note.get("ip_location") or "",
        },
        "content": {
            "title": note.get("title") or "",
            "desc": note.get("desc") or "",
            "type": note.get("type") or "",           # normal / video
            "tags": tags,
            "image_list": (note.get("image_list") or "").split(",") if note.get("image_list") else [],
            "video_url": note.get("video_url") or "",
        },
        "stats": {
            "liked_count": note.get("liked_count") or "0",
            "collected_count": note.get("collected_count") or "0",
            "comment_count": note.get("comment_count") or "0",
            "share_count": note.get("share_count") or "0",
        },
        "publish_time": ts_to_str(note.get("time")),
        "crawl_time": ts_to_str(note.get("add_ts")),
        "link": note.get("note_url") or "",
        "source_keyword": note.get("source_keyword") or "",
        "involved_user_ids": sorted(involved_user_ids),  # 所有涉及账号 ID，方便去重/关联分析
        "comments": comments,
        "comment_count_crawled": len(comments),
    }


def export(keyword_filter: str = None, out_file: str = None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    notes = load_notes(cur, keyword_filter)
    records = []
    for note in notes:
        comments = load_comments_for_note(cur, note["note_id"])
        records.append(build_record(note, comments))

    conn.close()

    OUT_PATH.mkdir(parents=True, exist_ok=True)
    if not out_file:
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{keyword_filter}" if keyword_filter else ""
        out_file = str(OUT_PATH / f"xhs{suffix}_{date_str}.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"导出完成: {len(records)} 条笔记 → {out_file}")
    return records, out_file


if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else None
    export(keyword_filter=kw)
