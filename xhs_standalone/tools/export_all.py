# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#
# 声明：本代码仅供学习和研究目的使用。

"""
全平台数据导出工具
将 SQLite 中所有平台数据整合为统一结构的 JSON 文件
用于黑灰产账号/卖家识别分析

用法:
    python tools/export_all.py              # 导出全部平台
    python tools/export_all.py xhs dy wb   # 只导出指定平台
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "sqlite_tables.db"
OUT_PATH = Path(__file__).parent.parent / "data" / "export"


# ─── 工具函数 ──────────────────────────────────────────────────────────────────

def ts(t, ms=True) -> str:
    """时间戳 → 可读字符串，ms=True 表示毫秒级"""
    if not t:
        return ""
    try:
        v = int(t)
        if ms and v > 1_000_000_000_000:
            v //= 1000
        return datetime.fromtimestamp(v).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(t)


def nest_comments(rows: list, id_field: str, pid_field: str) -> list:
    """
    将平铺的评论列表按 parent_id 嵌套为树形结构。
    顶层评论 parent_id 为 None / '0' / '' / 0。
    """
    top, sub_map = {}, {}
    for r in rows:
        cid = str(r.get(id_field, ""))
        pid = str(r.get(pid_field) or "0").strip()
        if pid in ("0", "", "None"):
            top[cid] = {**r, "sub_comments": []}
        else:
            sub_map.setdefault(pid, []).append(r)

    for pid, subs in sub_map.items():
        if pid in top:
            top[pid]["sub_comments"] = subs
        else:
            # 父评论已删除，作为孤立节点保留
            top[f"__orphan_{pid}"] = {
                id_field: pid,
                "user_id": "",
                "nickname": "[已删除]",
                "content": "",
                "sub_comments": subs,
            }
    return list(top.values())


def involved_ids(author_id: str, comments: list) -> list:
    ids = {author_id} if author_id else set()
    for c in comments:
        if c.get("user_id"):
            ids.add(str(c["user_id"]))
        for s in c.get("sub_comments", []):
            if s.get("user_id"):
                ids.add(str(s["user_id"]))
    return sorted(ids)


def load_comments(cur, table: str, content_id_field: str, content_id,
                  id_field: str, pid_field: str, field_map: dict) -> list:
    """通用评论加载，field_map 把 DB 字段映射到统一字段名"""
    db_fields = list(field_map.keys())
    sql = f"SELECT {', '.join(db_fields)} FROM {table} WHERE {content_id_field} = ? ORDER BY create_time ASC"
    try:
        cur.execute(sql, (content_id,))
    except Exception:
        return []
    rows = []
    for r in cur.fetchall():
        d = dict(zip(db_fields, r))
        mapped = {field_map[k]: d[k] for k in db_fields}
        rows.append(mapped)
    return nest_comments(rows, id_field, pid_field)


# ─── 各平台导出函数 ────────────────────────────────────────────────────────────

def export_douyin(cur) -> list:
    cur.execute("""
        SELECT aweme_id, user_id, nickname, avatar, ip_location,
               title, desc, aweme_type, aweme_url, cover_url,
               video_download_url, note_download_url,
               create_time, add_ts,
               liked_count, comment_count, share_count, collected_count,
               source_keyword
        FROM douyin_aweme ORDER BY add_ts DESC
    """)
    notes = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

    comment_field_map = {
        "comment_id": "comment_id", "user_id": "user_id", "nickname": "nickname",
        "ip_location": "ip_location", "content": "content",
        "create_time": "create_time_raw", "like_count": "like_count",
        "sub_comment_count": "sub_comment_count", "parent_comment_id": "parent_comment_id",
        "pictures": "pictures",
    }

    records = []
    for n in notes:
        raw_comments = load_comments(
            cur, "douyin_aweme_comment", "aweme_id", n["aweme_id"],
            "comment_id", "parent_comment_id", comment_field_map
        )
        comments = []
        for c in raw_comments:
            c["create_time"] = ts(c.pop("create_time_raw", ""), ms=False)
            c["sub_comments"] = [{
                **s,
                "create_time": ts(s.pop("create_time_raw", s.get("create_time", "")), ms=False)
            } for s in c.get("sub_comments", [])]
            comments.append(c)

        records.append({
            "platform": "douyin",
            "content_id": str(n["aweme_id"]),
            "author": {
                "user_id": str(n["user_id"] or ""),
                "nickname": n["nickname"] or "",
                "avatar": n["avatar"] or "",
                "ip_location": n["ip_location"] or "",
            },
            "content": {
                "title": n["title"] or "",
                "desc": n["desc"] or "",
                "type": n["aweme_type"] or "",
                "cover_url": n["cover_url"] or "",
                "video_url": n["video_download_url"] or "",
                "image_urls": [u for u in (n["note_download_url"] or "").split(",") if u],
            },
            "stats": {
                "liked_count": str(n["liked_count"] or "0"),
                "comment_count": str(n["comment_count"] or "0"),
                "share_count": str(n["share_count"] or "0"),
                "collected_count": str(n["collected_count"] or "0"),
            },
            "publish_time": ts(n["create_time"], ms=False),
            "crawl_time": ts(n["add_ts"]),
            "link": n["aweme_url"] or "",
            "source_keyword": n["source_keyword"] or "",
            "involved_user_ids": involved_ids(str(n["user_id"] or ""), comments),
            "comments": comments,
            "comment_count_crawled": len(comments),
        })
    return records


def export_weibo(cur) -> list:
    cur.execute("""
        SELECT note_id, user_id, nickname, avatar, gender, ip_location,
               title, content, create_time, add_ts,
               liked_count, comments_count, shared_count,
               note_url, source_keyword, profile_url
        FROM weibo_note ORDER BY add_ts DESC
    """)
    notes = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

    comment_field_map = {
        "comment_id": "comment_id", "user_id": "user_id", "nickname": "nickname",
        "ip_location": "ip_location", "content": "content",
        "create_time": "create_time_raw", "comment_like_count": "like_count",
        "sub_comment_count": "sub_comment_count", "parent_comment_id": "parent_comment_id",
    }

    records = []
    for n in notes:
        raw_comments = load_comments(
            cur, "weibo_note_comment", "note_id", n["note_id"],
            "comment_id", "parent_comment_id", comment_field_map
        )
        comments = []
        for c in raw_comments:
            c["create_time"] = ts(c.pop("create_time_raw", ""), ms=False)
            c["sub_comments"] = [{**s, "create_time": ts(s.pop("create_time_raw", s.get("create_time", "")), ms=False)} for s in c.get("sub_comments", [])]
            comments.append(c)

        records.append({
            "platform": "weibo",
            "content_id": str(n["note_id"]),
            "author": {
                "user_id": str(n["user_id"] or ""),
                "nickname": n["nickname"] or "",
                "avatar": n["avatar"] or "",
                "ip_location": n["ip_location"] or "",
                "gender": n["gender"] or "",
                "profile_url": n["profile_url"] or "",
            },
            "content": {
                "title": n["title"] or "",
                "desc": n["content"] or "",
                "type": "weibo",
            },
            "stats": {
                "liked_count": str(n["liked_count"] or "0"),
                "comment_count": str(n["comments_count"] or "0"),
                "share_count": str(n["shared_count"] or "0"),
            },
            "publish_time": ts(n["create_time"], ms=False),
            "crawl_time": ts(n["add_ts"]),
            "link": n["note_url"] or "",
            "source_keyword": n["source_keyword"] or "",
            "involved_user_ids": involved_ids(str(n["user_id"] or ""), comments),
            "comments": comments,
            "comment_count_crawled": len(comments),
        })
    return records


def export_tieba(cur) -> list:
    cur.execute("""
        SELECT note_id, user_id, user_nickname, user_avatar, ip_location,
               title, desc, note_url, publish_time, publish_ts, add_ts, last_modify_ts,
               tieba_id, tieba_name, tieba_link,
               total_replay_num, source_keyword
        FROM tieba_note ORDER BY last_modify_ts DESC
    """)
    notes = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

    comment_field_map = {
        "comment_id": "comment_id", "user_nickname": "nickname", "ip_location": "ip_location",
        "content": "content", "publish_time": "create_time_raw",
        "sub_comment_count": "sub_comment_count", "parent_comment_id": "parent_comment_id",
    }

    records = []
    for n in notes:
        raw_comments = load_comments(
            cur, "tieba_comment", "note_id", n["note_id"],
            "comment_id", "parent_comment_id", comment_field_map
        )
        comments = []
        for c in raw_comments:
            c["user_id"] = ""
            c["create_time"] = c.pop("create_time_raw", "")
            c["sub_comments"] = [{**s, "create_time": s.pop("create_time_raw", s.get("create_time", ""))} for s in c.get("sub_comments", [])]
            comments.append(c)

        records.append({
            "platform": "tieba",
            "content_id": str(n["note_id"]),
            "author": {
                "user_id": str(n["user_id"] or ""),
                "nickname": n["user_nickname"] or "",
                "avatar": n["user_avatar"] or "",
                "ip_location": n["ip_location"] or "",
            },
            "content": {
                "title": n["title"] or "",
                "desc": n["desc"] or "",
                "type": "tieba_post",
                "tieba_name": n["tieba_name"] or "",
                "tieba_link": n["tieba_link"] or "",
            },
            "stats": {
                "reply_count": str(n["total_replay_num"] or "0"),
            },
            "publish_time": n["publish_time"] or ts(n["publish_ts"], ms=False),
            "crawl_time": ts(n["add_ts"]) or ts(n["last_modify_ts"]),
            "link": n["note_url"] or "",
            "source_keyword": n["source_keyword"] or "",
            "involved_user_ids": involved_ids(str(n["user_id"] or ""), comments),
            "comments": comments,
            "comment_count_crawled": len(comments),
        })
    return records


def export_zhihu(cur) -> list:
    cur.execute("""
        SELECT content_id, content_type, content_text, content_url, question_id,
               title, desc, created_time, updated_time, add_ts,
               voteup_count, comment_count, source_keyword,
               user_id, user_nickname, user_avatar, user_url_token
        FROM zhihu_content ORDER BY add_ts DESC
    """)
    notes = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

    comment_field_map = {
        "comment_id": "comment_id", "user_id": "user_id", "user_nickname": "nickname",
        "ip_location": "ip_location", "content": "content",
        "publish_time": "create_time_raw", "like_count": "like_count",
        "sub_comment_count": "sub_comment_count", "parent_comment_id": "parent_comment_id",
    }

    records = []
    for n in notes:
        raw_comments = load_comments(
            cur, "zhihu_comment", "content_id", n["content_id"],
            "comment_id", "parent_comment_id", comment_field_map
        )
        comments = []
        for c in raw_comments:
            c["create_time"] = ts(c.pop("create_time_raw", ""), ms=False)
            c["sub_comments"] = [{**s, "create_time": ts(s.pop("create_time_raw", s.get("create_time", "")), ms=False)} for s in c.get("sub_comments", [])]
            comments.append(c)

        records.append({
            "platform": "zhihu",
            "content_id": str(n["content_id"]),
            "author": {
                "user_id": str(n["user_id"] or ""),
                "nickname": n["user_nickname"] or "",
                "avatar": n["user_avatar"] or "",
                "ip_location": "",
                "user_url_token": n["user_url_token"] or "",
            },
            "content": {
                "title": n["title"] or "",
                "desc": n["desc"] or "",
                "type": n["content_type"] or "",
                "full_text": n["content_text"] or "",
                "question_id": str(n["question_id"] or ""),
            },
            "stats": {
                "voteup_count": str(n["voteup_count"] or "0"),
                "comment_count": str(n["comment_count"] or "0"),
            },
            "publish_time": ts(n["created_time"], ms=False),
            "crawl_time": ts(n["add_ts"]),
            "link": n["content_url"] or "",
            "source_keyword": n["source_keyword"] or "",
            "involved_user_ids": involved_ids(str(n["user_id"] or ""), comments),
            "comments": comments,
            "comment_count_crawled": len(comments),
        })
    return records


def export_kuaishou(cur) -> list:
    cur.execute("""
        SELECT video_id, user_id, nickname, avatar,
               title, desc, video_type, video_url, video_cover_url, video_play_url,
               create_time, add_ts,
               liked_count, viewd_count, source_keyword
        FROM kuaishou_video ORDER BY add_ts DESC
    """)
    notes = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

    comment_field_map = {
        "comment_id": "comment_id", "user_id": "user_id", "nickname": "nickname",
        "content": "content", "create_time": "create_time_raw",
        "sub_comment_count": "sub_comment_count",
    }

    records = []
    for n in notes:
        raw_comments = load_comments(
            cur, "kuaishou_video_comment", "video_id", n["video_id"],
            "comment_id", "parent_comment_id", comment_field_map
        )
        comments = []
        for c in raw_comments:
            c["ip_location"] = ""
            c["parent_comment_id"] = "0"
            c["create_time"] = ts(c.pop("create_time_raw", ""), ms=False)
            c["sub_comments"] = []
            comments.append(c)

        records.append({
            "platform": "kuaishou",
            "content_id": str(n["video_id"]),
            "author": {
                "user_id": str(n["user_id"] or ""),
                "nickname": n["nickname"] or "",
                "avatar": n["avatar"] or "",
                "ip_location": "",
            },
            "content": {
                "title": n["title"] or "",
                "desc": n["desc"] or "",
                "type": n["video_type"] or "video",
                "video_url": n["video_url"] or "",
                "cover_url": n["video_cover_url"] or "",
                "play_url": n["video_play_url"] or "",
            },
            "stats": {
                "liked_count": str(n["liked_count"] or "0"),
                "view_count": str(n["viewd_count"] or "0"),
            },
            "publish_time": ts(n["create_time"]),
            "crawl_time": ts(n["add_ts"]),
            "link": n["video_url"] or "",
            "source_keyword": n["source_keyword"] or "",
            "involved_user_ids": involved_ids(str(n["user_id"] or ""), comments),
            "comments": comments,
            "comment_count_crawled": len(comments),
        })
    return records


def export_bilibili(cur) -> list:
    cur.execute("""
        SELECT video_id, user_id, nickname, avatar,
               title, desc, video_type, video_url, video_cover_url,
               create_time, add_ts,
               liked_count, disliked_count, video_play_count,
               video_favorite_count, video_share_count, video_coin_count,
               video_danmaku, video_comment, source_keyword
        FROM bilibili_video ORDER BY add_ts DESC
    """)
    notes = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

    comment_field_map = {
        "comment_id": "comment_id", "user_id": "user_id", "nickname": "nickname",
        "content": "content", "create_time": "create_time_raw", "like_count": "like_count",
        "sub_comment_count": "sub_comment_count", "parent_comment_id": "parent_comment_id",
        "sex": "gender", "sign": "signature",
    }

    records = []
    for n in notes:
        raw_comments = load_comments(
            cur, "bilibili_video_comment", "video_id", n["video_id"],
            "comment_id", "parent_comment_id", comment_field_map
        )
        comments = []
        for c in raw_comments:
            c["ip_location"] = ""
            c["create_time"] = ts(c.pop("create_time_raw", ""), ms=False)
            c["sub_comments"] = [{**s, "create_time": ts(s.pop("create_time_raw", s.get("create_time", "")), ms=False)} for s in c.get("sub_comments", [])]
            comments.append(c)

        records.append({
            "platform": "bilibili",
            "content_id": str(n["video_id"]),
            "author": {
                "user_id": str(n["user_id"] or ""),
                "nickname": n["nickname"] or "",
                "avatar": n["avatar"] or "",
                "ip_location": "",
            },
            "content": {
                "title": n["title"] or "",
                "desc": n["desc"] or "",
                "type": n["video_type"] or "video",
                "video_url": n["video_url"] or "",
                "cover_url": n["video_cover_url"] or "",
            },
            "stats": {
                "liked_count": str(n["liked_count"] or "0"),
                "play_count": str(n["video_play_count"] or "0"),
                "comment_count": str(n["video_comment"] or "0"),
                "favorite_count": str(n["video_favorite_count"] or "0"),
                "share_count": str(n["video_share_count"] or "0"),
                "coin_count": str(n["video_coin_count"] or "0"),
                "danmaku_count": str(n["video_danmaku"] or "0"),
            },
            "publish_time": ts(n["create_time"], ms=False),
            "crawl_time": ts(n["add_ts"]),
            "link": n["video_url"] or "",
            "source_keyword": n["source_keyword"] or "",
            "involved_user_ids": involved_ids(str(n["user_id"] or ""), comments),
            "comments": comments,
            "comment_count_crawled": len(comments),
        })
    return records


def export_xhs(cur) -> list:
    cur.execute("""
        SELECT note_id, user_id, nickname, avatar, ip_location,
               title, desc, type, tag_list, image_list, video_url,
               time, add_ts, note_url, source_keyword,
               liked_count, collected_count, comment_count, share_count
        FROM xhs_note ORDER BY add_ts DESC
    """)
    notes = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]

    comment_field_map = {
        "comment_id": "comment_id", "user_id": "user_id", "nickname": "nickname",
        "ip_location": "ip_location", "content": "content",
        "create_time": "create_time_raw", "like_count": "like_count",
        "sub_comment_count": "sub_comment_count", "parent_comment_id": "parent_comment_id",
        "pictures": "pictures",
    }

    records = []
    for n in notes:
        raw_comments = load_comments(
            cur, "xhs_note_comment", "note_id", n["note_id"],
            "comment_id", "parent_comment_id", comment_field_map
        )
        comments = []
        for c in raw_comments:
            c["create_time"] = ts(c.pop("create_time_raw", ""))
            c["sub_comments"] = [{**s, "create_time": ts(s.pop("create_time_raw", s.get("create_time", "")))} for s in c.get("sub_comments", [])]
            comments.append(c)

        tags = []
        try:
            raw = json.loads(n.get("tag_list") or "[]")
            tags = raw if isinstance(raw, list) else [raw]
        except Exception:
            pass

        records.append({
            "platform": "xiaohongshu",
            "content_id": n["note_id"],
            "author": {
                "user_id": str(n["user_id"] or ""),
                "nickname": n["nickname"] or "",
                "avatar": n["avatar"] or "",
                "ip_location": n["ip_location"] or "",
            },
            "content": {
                "title": n["title"] or "",
                "desc": n["desc"] or "",
                "type": n["type"] or "",
                "tags": tags,
                "image_list": [u for u in (n["image_list"] or "").split(",") if u],
                "video_url": n["video_url"] or "",
            },
            "stats": {
                "liked_count": str(n["liked_count"] or "0"),
                "collected_count": str(n["collected_count"] or "0"),
                "comment_count": str(n["comment_count"] or "0"),
                "share_count": str(n["share_count"] or "0"),
            },
            "publish_time": ts(n["time"]),
            "crawl_time": ts(n["add_ts"]),
            "link": n["note_url"] or "",
            "source_keyword": n["source_keyword"] or "",
            "involved_user_ids": involved_ids(str(n["user_id"] or ""), comments),
            "comments": comments,
            "comment_count_crawled": len(comments),
        })
    return records


# ─── 主入口 ────────────────────────────────────────────────────────────────────

PLATFORM_EXPORTERS = {
    "dy":    ("douyin",      export_douyin),
    "wb":    ("weibo",       export_weibo),
    "tieba": ("tieba",       export_tieba),
    "zhihu": ("zhihu",       export_zhihu),
    "ks":    ("kuaishou",    export_kuaishou),
    "bili":  ("bilibili",    export_bilibili),
    "xhs":   ("xiaohongshu", export_xhs),
}


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(PLATFORM_EXPORTERS.keys())
    unknown = [t for t in targets if t not in PLATFORM_EXPORTERS]
    if unknown:
        print(f"未知平台: {unknown}，可选: {list(PLATFORM_EXPORTERS.keys())}")
        sys.exit(1)

    OUT_PATH.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    summary = []
    for key in targets:
        name, fn = PLATFORM_EXPORTERS[key]
        print(f"正在导出 {name}...", end=" ", flush=True)
        try:
            records = fn(cur)
        except Exception as e:
            print(f"失败: {e}")
            continue

        out_file = OUT_PATH / f"{name}_{date_str}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        print(f"{len(records)} 条 → {out_file.name}")
        summary.append((name, len(records), str(out_file)))

    conn.close()

    print("\n========== 导出汇总 ==========")
    total = 0
    for name, cnt, path in summary:
        print(f"  {name:<14} {cnt:>5} 条  {path}")
        total += cnt
    print(f"  {'合计':<14} {total:>5} 条")
    print(f"  输出目录: {OUT_PATH}")


if __name__ == "__main__":
    main()
