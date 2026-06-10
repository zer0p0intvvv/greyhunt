"""HTML 可视化导出器：把情报库渲染成按「来源群组」聚合的单页 HTML。

设计：
- 直接只读查询 SQLite 里所有 ``*_intel_filtered`` 表（多源 UNION）。
- 按 ``source_group`` 分组（同类群组的情报聚在一起），每组一张卡片。
- 群组标题旁渲染可点击的群链接（``source_group_url``）。
- 每条情报展示：风险等级徽章、风险类型、原文、研判摘要、抽取实体、作者、原文链接。
- 顶部有概览统计 + 关键词搜索 + 风险等级过滤（纯前端 JS，无外部依赖）。

用法：
    from tg_intel_crawler.storage.html_reporter import HtmlReporter
    out = HtmlReporter("output/intel.db").render("output/reports/intel.html")
"""

from __future__ import annotations

import html
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


_RISK_ORDER = {"high": 0, "medium": 1, "low": 2, "": 3}
_RISK_LABEL = {"high": "高危", "medium": "中危", "low": "低危"}


class HtmlReporter:
    """Render filtered intel from one or more SQLite DBs into a single HTML page."""

    def __init__(self, db_path: str | list[str]):
        # 支持单个库或多个库（多源/多项目合并展示）
        if isinstance(db_path, (list, tuple)):
            self._db_paths = [str(p) for p in db_path]
        else:
            self._db_paths = [str(db_path)]

    # ---------- data ----------

    def _filtered_tables(self, conn: sqlite3.Connection) -> list[str]:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name LIKE '%_intel_filtered'"
        ).fetchall()
        return [r[0] for r in rows]

    @staticmethod
    def _derive_group_url(source_group_url: str, source_url: str, platform: str = "") -> str:
        """群链接派生（严格）。

        - 已有 source_group_url（来自 group_id 派生或采集时的真实群链接）→ 直接用，最可靠。
        - Telegram：**绝不**从 source_url 派生群链接。source_url 是正文里推广的
          关联群/机器人链接（如 @souso/@jisou 搜索 bot），并非情报真正所属的源群，
          用它会张冠李戴。源群链接只能来自 group_id（已在回填阶段写入 source_group_url）。
        - Twitter：source_url 是该作者自己的推文链接，派生作者主页是同一账号，准确，可派生。
        """
        if source_group_url:
            return source_group_url
        p = (platform or "").lower()
        if p == "twitter" and source_url:
            m = re.match(r"(https?://(?:twitter|x)\.com/[^/]+)(?:/status/.*)?", source_url)
            if m:
                return m.group(1)
        # Telegram / bot / 其它：不从 source_url 猜群链接
        return ""

    def _load_records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()  # (platform, original_text) 跨库去重
        for db_path in self._db_paths:
            if not Path(db_path).exists():
                continue
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            try:
                for table in self._filtered_tables(conn):
                    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
                    group_url_sel = (
                        "source_group_url" if "source_group_url" in cols
                        else "'' AS source_group_url"
                    )
                    media_sel = (
                        "media_urls" if "media_urls" in cols else "'' AS media_urls"
                    )
                    ocr_sel = (
                        "media_ocr_text" if "media_ocr_text" in cols
                        else "'' AS media_ocr_text"
                    )
                    rows = conn.execute(
                        f"""
                        SELECT source_platform, source_group, {group_url_sel},
                               msg_date, sender_name, sender_username,
                               original_text, risk_type, risk_level,
                               entities, summary, source_url,
                               {media_sel}, {ocr_sel}
                        FROM {table}
                        """
                    ).fetchall()
                    for row in rows:
                        rec = dict(row)
                        # 跨库去重（同平台同原文视为同一条）
                        dedup_key = (
                            rec.get("source_platform") or "",
                            (rec.get("original_text") or "")[:200],
                        )
                        if dedup_key in seen:
                            continue
                        seen.add(dedup_key)
                        # 派生群链接（仅 Twitter 可从 source_url 派生作者主页；
                        # Telegram 严格只用 group_id 回填的 source_group_url）
                        rec["source_group_url"] = self._derive_group_url(
                            rec.get("source_group_url") or "",
                            rec.get("source_url") or "",
                            rec.get("source_platform") or "",
                        )
                        records.append(rec)
            finally:
                conn.close()
        return records

    @staticmethod
    def _group_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Group by (platform, source_group); keep a representative group_url."""
        groups: dict[tuple[str, str], dict[str, Any]] = {}
        for r in records:
            platform = r.get("source_platform") or "unknown"
            name = r.get("source_group") or "(未知来源)"
            key = (platform, name)
            g = groups.get(key)
            if g is None:
                g = {
                    "platform": platform,
                    "name": name,
                    "group_url": r.get("source_group_url") or "",
                    "items": [],
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                }
                groups[key] = g
            if not g["group_url"] and r.get("source_group_url"):
                g["group_url"] = r["source_group_url"]
            lvl = (r.get("risk_level") or "").lower()
            if lvl in ("high", "medium", "low"):
                g[lvl] += 1
            g["items"].append(r)

        result = list(groups.values())
        # 组内按风险等级排序（high 在前），组间按 high 数量降序
        for g in result:
            g["items"].sort(key=lambda x: _RISK_ORDER.get((x.get("risk_level") or "").lower(), 3))
        result.sort(key=lambda g: (-g["high"], -len(g["items"])))
        return result

    # ---------- render ----------

    def render(self, output_path: str, *, embed_images: bool = False) -> str:
        records = self._load_records()
        groups = self._group_records(records)
        total = len(records)
        total_high = sum(1 for r in records if (r.get("risk_level") or "").lower() == "high")
        total_groups = len(groups)
        platforms = sorted({(r.get("source_platform") or "unknown") for r in records})

        # 各筛选维度按情报数量降序统计
        from collections import Counter
        rtype_counter: Counter = Counter()
        platform_counter: Counter = Counter()
        source_counter: Counter = Counter()
        for r in records:
            rtype_counter[r.get("risk_type") or "未分类"] += 1
            platform_counter[r.get("source_platform") or "unknown"] += 1
            source_counter[r.get("source_group") or "(未知来源)"] += 1

        html_str = self._build_html(
            groups=groups,
            total=total,
            total_high=total_high,
            total_groups=total_groups,
            platforms=platforms,
            rtype_options=rtype_counter.most_common(),
            platform_options=platform_counter.most_common(),
            source_options=source_counter.most_common(),
        )

        if embed_images:
            html_str = self._embed_images(html_str)

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html_str, encoding="utf-8")
        return str(out.resolve())

    @staticmethod
    def _embed_images(html_str: str) -> str:
        """把 <img src="http..."> 的图片下载并内嵌为 base64 data URI，
        生成完全离线自包含的 HTML（适合作为项目首页静态展示）。

        下载失败的图保留原 URL（不影响其它）。并发下载提速。
        """
        import asyncio
        import base64

        import httpx

        urls = sorted(set(re.findall(r'<img class="thumb" src="(https?://[^"]+)"', html_str)))
        if not urls:
            return html_str

        async def fetch_all() -> dict:
            mapping: dict[str, str] = {}
            sem = asyncio.Semaphore(8)

            async def one(client: httpx.AsyncClient, u: str):
                async with sem:
                    try:
                        r = await client.get(u)
                        r.raise_for_status()
                        if len(r.content) > 4 * 1024 * 1024:
                            return
                        ctype = r.headers.get("content-type", "image/jpeg").split(";")[0]
                        if not ctype.startswith("image/"):
                            ctype = "image/jpeg"
                        b64 = base64.b64encode(r.content).decode("ascii")
                        mapping[u] = f"data:{ctype};base64,{b64}"
                    except Exception:
                        pass

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0), follow_redirects=True
            ) as client:
                await asyncio.gather(*[one(client, u) for u in urls])
            return mapping

        mapping = asyncio.run(fetch_all())
        for u, data_uri in mapping.items():
            html_str = html_str.replace(f'src="{u}"', f'src="{data_uri}"')
        return html_str

    _PLATFORM_LABEL = {
        "twitter": "𝕏 Twitter/X", "telegram": "✈️ Telegram", "bot": "🤖 @JISOU 搜索",
        "weibo": "🔴 微博", "unknown": "未知",
    }

    def _build_options(self, counter_items, *, label_map=None) -> str:
        """按数量降序生成 <option>，文案带数量。"""
        opts = []
        for value, count in counter_items:
            label = (label_map or {}).get(value, value)
            opts.append(
                f'<option value="{self._esc(value)}">{self._esc(label)} ({count})</option>'
            )
        return "".join(opts)

    @staticmethod
    def _esc(v: Any) -> str:
        return html.escape(str(v if v is not None else ""))

    @staticmethod
    def _linkify(v: Any) -> str:
        """HTML-escape text, then turn any URL into a clickable blue link.

        Handles full URLs (http/https) and bare domains starting with t.me/ or
        t.co/ (common in tweets). Escapes first to stay XSS-safe, then linkifies.
        """
        escaped = html.escape(str(v if v is not None else ""))
        # 匹配 http(s):// 开头的完整 URL，或裸写的 t.me/ t.co/ 短链
        pattern = re.compile(
            r"(https?://[^\s<>\"']+|(?:www\.|t\.me/|t\.co/)[^\s<>\"']+)"
        )

        def repl(m: re.Match) -> str:
            raw = m.group(0)
            href = raw if raw.startswith("http") else f"https://{raw}"
            return (
                f'<a class="inline-link" href="{href}" '
                f'target="_blank" rel="noopener">{raw}</a>'
            )

        return pattern.sub(repl, escaped)

    def _render_entities(self, entities_raw: Any) -> str:
        if not entities_raw:
            return ""
        try:
            ent = entities_raw if isinstance(entities_raw, dict) else json.loads(entities_raw)
        except (json.JSONDecodeError, TypeError):
            return ""
        chips: list[str] = []
        label_map = {
            "accounts": "账号", "contacts": "联系方式", "links": "链接",
            "domains": "域名", "invite_codes": "邀请码", "tools": "工具", "prices": "价格",
        }
        linkify_keys = {"links", "domains"}  # 这些值渲染成可点击蓝链
        for key, label in label_map.items():
            vals = ent.get(key) or []
            for v in vals:
                if not v:
                    continue
                value_html = self._linkify(v) if key in linkify_keys else self._esc(v)
                chips.append(
                    f'<span class="chip chip-{key}">{self._esc(label)}: {value_html}</span>'
                )
        return "".join(chips)

    def _render_item(self, item: dict[str, Any], *, platform: str = "", source: str = "") -> str:
        lvl = (item.get("risk_level") or "").lower()
        lvl_label = _RISK_LABEL.get(lvl, lvl or "—")
        raw_text = item.get("original_text") or ""
        text_attr = self._esc(raw_text).lower()  # 纯文本用于搜索 data-text
        text_html = self._linkify(raw_text)       # 正文渲染：URL 变蓝链
        summary_html = self._linkify(item.get("summary"))
        rtype_raw = item.get("risk_type") or "未分类"
        rtype = self._esc(rtype_raw)
        author = self._esc(item.get("sender_username") or item.get("sender_name"))
        src_url = item.get("source_url") or ""
        entities_html = self._render_entities(item.get("entities"))
        src_link = (
            f'<a class="src-link" href="{self._esc(src_url)}" target="_blank" rel="noopener">原文↗</a>'
            if src_url else ""
        )
        author_html = f'<span class="author">@{author}</span>' if author else ""
        media_html = self._render_media(item.get("media_urls"))
        ocr = item.get("media_ocr_text") or ""
        ocr_html = (
            f'<div class="item-ocr">🖼️ 图中信息：{self._linkify(ocr)}</div>' if ocr else ""
        )
        return f"""
        <div class="item" data-risk="{self._esc(lvl)}" data-rtype="{rtype}"
             data-platform="{self._esc(platform)}" data-source="{self._esc(source)}"
             data-text="{text_attr}">
          <div class="item-head">
            <span class="badge badge-{self._esc(lvl)}">{self._esc(lvl_label)}</span>
            <span class="rtype">{rtype}</span>
            {author_html}
            {src_link}
          </div>
          <div class="item-text">{text_html}</div>
          {f'<div class="item-summary">研判：{summary_html}</div>' if item.get("summary") else ''}
          {ocr_html}
          {media_html}
          {f'<div class="item-entities">{entities_html}</div>' if entities_html else ''}
        </div>"""

    def _render_media(self, media_urls_raw: Any) -> str:
        """渲染图片/视频封面缩略图（可点击放大查看原图）。"""
        if not media_urls_raw:
            return ""
        urls = media_urls_raw
        if isinstance(urls, str):
            try:
                urls = json.loads(urls)
            except (json.JSONDecodeError, TypeError):
                urls = [urls] if urls.startswith("http") else []
        if not isinstance(urls, list) or not urls:
            return ""
        thumbs = "".join(
            f'<a href="{self._esc(u)}" target="_blank" rel="noopener" class="thumb-link">'
            f'<img class="thumb" src="{self._esc(u)}" loading="lazy" alt="媒体"></a>'
            for u in urls if u
        )
        return f'<div class="item-media">{thumbs}</div>' if thumbs else ""

    def _render_platform_badge(self, platform: str, source_group: str = "") -> str:
        """渲染来源平台标签（友好名称 + 图标 + 颜色）。

        bot 数据源特别标注：均来自 Telegram 的 @JISOU 搜索机器人。
        """
        p = (platform or "unknown").lower()
        meta = {
            "twitter": ("𝕏 Twitter/X", "plat-twitter", ""),
            "telegram": ("✈️ Telegram 群组", "plat-telegram", ""),
            "bot": (
                "🤖 @JISOU 机器人搜索",
                "plat-bot",
                "该情报通过 Telegram 的 @JISOU 搜索机器人按关键词检索而来，并非直接采集自某个群组",
            ),
            "weibo": ("🔴 微博", "plat-weibo", ""),
        }
        label, cls, tip = meta.get(p, (self._esc(platform), "plat-unknown", ""))
        title_attr = f' title="{self._esc(tip)}"' if tip else ""
        return f'<span class="platform {cls}"{title_attr}>{label}</span>'

    def _render_group(self, g: dict[str, Any]) -> str:
        url = g.get("group_url") or ""
        name = self._esc(g["name"])
        platform = g.get("platform") or "unknown"
        platform_badge = self._render_platform_badge(platform, g.get("name", ""))
        # 私密群：t.me/c/<id> 是源群的内部链接，无公开用户名，
        # 只能在已登录且为成员的 Telegram 客户端内打开；浏览器/非成员点击会跳到官网首页。
        is_private = "t.me/c/" in url
        is_bot = (platform or "").lower() == "bot"
        if url:
            private_tag = (
                '<span class="private-tag" title="私密群：这是情报来源的源群，'
                '无公开用户名（链接为 t.me/c/内部ID）。'
                '需在已登录的 Telegram 客户端内、且为该群成员才能打开；'
                '浏览器或非成员直接点击会跳到 Telegram 官网首页">🔒 私密群（无公开链接，需为成员）</span>'
                if is_private else ""
            )
            title_link = (
                f'<a class="group-link" href="{self._esc(url)}" target="_blank" '
                f'rel="noopener">{name} ↗</a>{private_tag}'
            )
        else:
            title_link = f"<span>{name}</span>"
        # bot 来源额外提示条
        bot_note = (
            '<div class="bot-note">🤖 本组情报来自 Telegram <b>@JISOU</b> '
            '搜索机器人的关键词检索结果，非直接群组采集</div>'
            if is_bot else ""
        )
        items_html = "".join(
            self._render_item(it, platform=platform, source=g.get("name", ""))
            for it in g["items"]
        )
        return f"""
      <section class="group" data-group="{name.lower()}">
        <div class="group-head">
          <h2>{title_link}</h2>
          <div class="group-meta">
            {platform_badge}
            <span class="count">{len(g['items'])} 条</span>
            <span class="badge badge-high">{g['high']} 高危</span>
            <span class="badge badge-medium">{g['medium']} 中危</span>
            <span class="badge badge-low">{g['low']} 低危</span>
          </div>
        </div>
        {bot_note}
        <div class="group-body">{items_html}</div>
      </section>"""

    def _build_html(
        self,
        *,
        groups: list[dict[str, Any]],
        total: int,
        total_high: int,
        total_groups: int,
        platforms: list[str],
        rtype_options=None,
        platform_options=None,
        source_options=None,
    ) -> str:
        groups_html = "".join(self._render_group(g) for g in groups) or (
            '<p class="empty">暂无情报数据。请先运行采集（crawl / crawl-twitter）。</p>'
        )
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        platforms_str = self._esc(", ".join(platforms) or "—")
        rtype_opts = self._build_options(rtype_options or [])
        platform_opts = self._build_options(platform_options or [], label_map=self._PLATFORM_LABEL)
        source_opts = self._build_options(source_options or [])
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GrayHunt</title>
<style>
  :root {{ --bg:#0f1115; --card:#1a1d24; --card2:#22262f; --text:#e6e8eb; --muted:#9aa0aa;
           --high:#ff4d4f; --medium:#faad14; --low:#52c41a; --link:#4ea1ff; --border:#2c313a; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text);
          font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; }}
  header {{ position:sticky; top:0; z-index:10; background:var(--card); border-bottom:1px solid var(--border);
            padding:16px 24px; }}
  h1 {{ margin:0 0 6px; font-size:20px; }}
  .stats {{ color:var(--muted); font-size:13px; display:flex; gap:16px; flex-wrap:wrap; align-items:center; }}
  .stats b {{ color:var(--text); }}
  .controls {{ margin-top:12px; display:flex; gap:10px; flex-wrap:wrap; }}
  .controls input, .controls select {{ background:var(--card2); border:1px solid var(--border); color:var(--text);
            padding:8px 12px; border-radius:8px; font-size:14px; }}
  .controls input {{ flex:1; min-width:200px; }}
  main {{ padding:20px 24px; max-width:1100px; margin:0 auto; }}
  .group {{ background:var(--card); border:1px solid var(--border); border-radius:12px; margin-bottom:20px; overflow:hidden; }}
  .group-head {{ padding:14px 18px; background:var(--card2); border-bottom:1px solid var(--border);
                 display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }}
  .group-head h2 {{ margin:0; font-size:16px; }}
  .group-link {{ color:var(--link); text-decoration:none; }}
  .group-link:hover {{ text-decoration:underline; }}
  .private-tag {{ margin-left:8px; font-size:11px; font-weight:normal; color:var(--medium);
                  background:rgba(250,173,20,.15); border:1px solid var(--medium);
                  padding:1px 7px; border-radius:6px; vertical-align:middle; cursor:help; white-space:nowrap; }}
  .group-meta {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; font-size:12px; color:var(--muted); }}
  .platform {{ background:#2b3340; padding:2px 8px; border-radius:6px; font-weight:600; }}
  .plat-twitter {{ background:#1d3a4d; color:#7fd1ff; }}
  .plat-telegram {{ background:#1f3a52; color:#6cc0ff; }}
  .plat-bot {{ background:#4a3a1f; color:#ffcf6c; cursor:help; }}
  .plat-weibo {{ background:#4d1f24; color:#ff8a95; }}
  .bot-note {{ margin:0 18px 8px; padding:7px 12px; font-size:12px; color:#ffcf6c;
               background:rgba(250,173,20,.10); border:1px dashed var(--medium); border-radius:8px; }}
  .bot-note b {{ color:#ffd98a; }}
  .group-body {{ padding:8px 18px 16px; }}
  .item {{ padding:12px 0; border-bottom:1px dashed var(--border); }}
  .item:last-child {{ border-bottom:none; }}
  .item-head {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-bottom:6px; }}
  .badge {{ font-size:12px; padding:2px 8px; border-radius:6px; color:#fff; font-weight:600; }}
  .badge-high {{ background:var(--high); }}
  .badge-medium {{ background:var(--medium); }}
  .badge-low {{ background:var(--low); }}
  .rtype {{ font-size:13px; color:var(--muted); }}
  .author {{ font-size:12px; color:var(--link); }}
  .src-link {{ font-size:12px; color:var(--link); text-decoration:none; margin-left:auto; }}
  .item-text {{ font-size:14px; line-height:1.6; white-space:pre-wrap; word-break:break-word; }}
  .inline-link {{ color:var(--link); text-decoration:none; word-break:break-all; }}
  .inline-link:hover {{ text-decoration:underline; }}
  .chip .inline-link {{ color:var(--link); }}
  .item-summary {{ margin-top:6px; font-size:13px; color:var(--muted); }}
  .item-ocr {{ margin-top:6px; font-size:13px; color:#a8e0a0; background:rgba(82,196,26,.08);
               border-left:3px solid var(--low); padding:6px 10px; border-radius:6px;
               line-height:1.6; white-space:pre-wrap; word-break:break-word; }}
  .item-media {{ margin-top:8px; display:flex; gap:8px; flex-wrap:wrap; }}
  .thumb {{ width:120px; height:120px; object-fit:cover; border-radius:8px;
            border:1px solid var(--border); cursor:zoom-in; transition:transform .15s; background:#000; }}
  .thumb:hover {{ transform:scale(1.04); border-color:var(--link); }}
  .item-entities {{ margin-top:8px; display:flex; gap:6px; flex-wrap:wrap; }}
  .chip {{ font-size:12px; padding:2px 8px; border-radius:6px; background:#2b3340; color:var(--text); }}
  .chip-contacts {{ background:#4a2b2b; }}
  .chip-domains {{ background:#2b3a4a; }}
  .chip-invite_codes {{ background:#3a2b4a; }}
  .empty {{ color:var(--muted); text-align:center; padding:60px; }}
  .hidden {{ display:none !important; }}
</style>
</head>
<body>
<header>
  <h1>🛡️ GrayHunt</h1>
  <div class="stats">
    <span>共 <b>{total}</b> 条情报</span>
    <span><b>{total_groups}</b> 个来源群组</span>
    <span><b style="color:var(--high)">{total_high}</b> 条高危</span>
    <span>来源平台：{platforms_str}</span>
    <span>生成时间：{now}</span>
  </div>
  <div class="controls">
    <input id="search" type="text" placeholder="搜索原文 / 群组名…">
    <select id="riskFilter">
      <option value="">全部风险等级</option>
      <option value="high">仅高危</option>
      <option value="medium">仅中危</option>
      <option value="low">仅低危</option>
    </select>
    <select id="rtypeFilter">
      <option value="">全部风险类别</option>
      {rtype_opts}
    </select>
    <select id="platformFilter">
      <option value="">全部来源平台</option>
      {platform_opts}
    </select>
    <select id="sourceFilter">
      <option value="">全部来源（群组/账号）</option>
      {source_opts}
    </select>
  </div>
</header>
<main id="content">
{groups_html}
</main>
<script>
  const search = document.getElementById('search');
  const riskFilter = document.getElementById('riskFilter');
  const rtypeFilter = document.getElementById('rtypeFilter');
  const platformFilter = document.getElementById('platformFilter');
  const sourceFilter = document.getElementById('sourceFilter');
  function applyFilter() {{
    const q = search.value.trim().toLowerCase();
    const risk = riskFilter.value;
    const rtype = rtypeFilter.value;
    const platform = platformFilter.value;
    const source = sourceFilter.value;
    document.querySelectorAll('.group').forEach(group => {{
      let visibleInGroup = 0;
      group.querySelectorAll('.item').forEach(item => {{
        const text = item.getAttribute('data-text') || '';
        const itemRisk = item.getAttribute('data-risk') || '';
        const itemType = item.getAttribute('data-rtype') || '';
        const itemPlatform = item.getAttribute('data-platform') || '';
        const itemSource = item.getAttribute('data-source') || '';
        const matchQ = !q || text.includes(q) || (group.getAttribute('data-group')||'').includes(q);
        const matchRisk = !risk || itemRisk === risk;
        const matchType = !rtype || itemType === rtype;
        const matchPlatform = !platform || itemPlatform === platform;
        const matchSource = !source || itemSource === source;
        const show = matchQ && matchRisk && matchType && matchPlatform && matchSource;
        item.classList.toggle('hidden', !show);
        if (show) visibleInGroup++;
      }});
      group.classList.toggle('hidden', visibleInGroup === 0);
    }});
  }}
  [search].forEach(el => el.addEventListener('input', applyFilter));
  [riskFilter, rtypeFilter, platformFilter, sourceFilter].forEach(
    el => el.addEventListener('change', applyFilter)
  );
</script>
</body>
</html>"""
