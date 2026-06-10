---
name: graymarket-hunter
description: "Analyze gray-market / black-market (黑灰产) seller gangs on second-hand or social platforms (闲鱼/Goofish, 转转, 微博, 小红书, 贴吧). Takes locally-collected listing data (JSON), runs dedup and denoise, builds a TWO-LAYER gang model (core gangs by sales-script fingerprint plus super-gang networks of one-crew-many-businesses), mines coded slang variants, renders an interactive force-directed graph, and writes a governance report. Trigger when the user mentions 黑灰产团伙挖掘, 马甲群识别, 超级团伙, 黑话暗语, 团伙图谱, 闲鱼黑产, or asks to analyze gray-market seller data they already collected. Data collection itself is out of scope (manual anti-bot); this skill only analyzes."
---

# graymarket-hunter — 黑灰产团伙挖掘（分析层）

## What this skill does

A platform-agnostic analysis pipeline for gray-market gang detection. The user has
already collected listing data locally (manual, anti-bot). This skill consumes that
data and produces:

1. **Dedup + denoise stats** — remove cross-keyword duplicates (by `itemId`) and book/tutorial noise.
2. **Two-layer gang graph** (`gang_graph.json`) — the core deliverable:
   - **Layer 1 — Core gangs**: cluster sellers by *dominant sales-script template* (title skeleton). Same copy = one set of sock-puppet accounts. No BFS chaining (avoids giant blobs).
   - **Layer 2 — Super-gang networks**: link core gangs that share sellers / images / script skeletons via union-find. Reveals "one crew, many businesses".
3. **Slang expansion** (`slang_expanded.json`) — coded-word variants (homophone/split-char/abbrev) via rules + LLM.
4. **Interactive graph** (`gang_viz.html`) — self-contained force-directed visualization.
5. **Governance report** — analyst-grade narrative synthesized from the above.

## Data contract (unified format)

Each input file is JSON: `{ "keyword": "...", "items": [ {itemId, title, seller, area?, image?, publishTime?, link?}, ... ] }`.
Minimum required per item: `itemId` (dedup key), `title` (script fingerprint), `seller` (graph node).

## Where the data is

- **Pre-mounted 闲鱼 dataset**: `/mnt/xianyu-data/` (the user's local `xianyu_spider/data`, read-only, ~140 files).
- **User-uploaded data**: `/mnt/user-data/uploads/`.
- Pick whichever the user refers to. Default to `/mnt/xianyu-data/` for the 闲鱼 competition case.

## Environment the scripts read

All scripts live under `/mnt/skills/custom/graymarket-hunter/scripts/` and are driven by env vars:

| Env var | Meaning | Typical value |
|---|---|---|
| `GMH_DATA_DIR` | input data directory | `/mnt/xianyu-data` or `/mnt/user-data/uploads` |
| `GMH_OUT_DIR` | output directory (writable) | `/mnt/user-data/outputs` |
| `GMH_DATA_GLOB` | which files to load | `*.json` (default) or `goofish_*.json` |

LLM annotation reuses DeerFlow's Doubao/Ark key automatically: the scripts read
`VOLCENGINE_API_KEY` (set in `.env`) and `GMH_LLM_MODEL` (the Ark endpoint `ep-...`
or model name). If `GMH_LLM_MODEL` is unset, run the pure-algorithm path (no `--llm`).

## Setup (run once per session, before analysis)

```bash
pip3 install -q -r /mnt/skills/custom/graymarket-hunter/scripts/requirements.txt 2>/dev/null
```

## Workflow

### Step 1 — Confirm data source & set env

Decide `GMH_DATA_DIR`. For the 闲鱼 case use the mounted dataset:

```bash
export GMH_DATA_DIR=/mnt/xianyu-data
export GMH_OUT_DIR=/mnt/user-data/outputs
export GMH_DATA_GLOB='goofish_*.json'
```

### Step 2 — Dedup + denoise sanity check

```bash
cd /mnt/skills/custom/graymarket-hunter/scripts && python3 data_loader.py
```

Report the dedup rate and noise-removal count to the user. A healthy run removes
~10–40% duplicates. If 0 files load, the data dir / glob is wrong — fix and retry.

### Step 2.5 — Relevance filter (THREE-LAYER FUNNEL)

闲鱼搜索是模糊匹配，会带出大量字面误匹配的无关实物商品（如搜"DB"带出"DB滑雪背包"，
搜"皮皮虾"带出海鲜）。这些噪音会制造虚假团伙、污染图谱。`data_loader` 内置三层漏斗自动过滤：

- 第1层 正向词：标题含明确黑产意图（代充/代投/秒到/养号/数据工具…）→ 强保留
- 第2层 负向词：标题含实物商品特征（背包/食品/服饰/数码配件…）→ 直接剔除
- 第3层 LLM：前两层未命中的灰色样本 → LLM 二分类（宁漏勿杀，不确定保留）

第3层需要先跑一次生成黑名单缓存（需 `GMH_LLM_MODEL` 设好）：

```bash
cd /mnt/skills/custom/graymarket-hunter/scripts && python3 relevance_filter.py
```

它写 `$GMH_OUT_DIR/relevance_blacklist.json`。之后 `data_loader`（及下游所有脚本）
会自动加载该黑名单并应用三层过滤。健康的过滤会剔除 ~20–30% 无关商品，但**真实黑产
团伙数应基本不变**（伪团伙消失、真团伙保留）。若无 LLM，仅前两层规则也能剔除大部分噪音。

### Step 3 — Two-layer gang model (CORE)

Pure-algorithm (fast, no LLM):

```bash
cd /mnt/skills/custom/graymarket-hunter/scripts && python3 gang_detect.py --min-gang 3
```

With LLM annotation (names/biz/risk for the largest gangs — needs `GMH_LLM_MODEL` set):

```bash
cd /mnt/skills/custom/graymarket-hunter/scripts && python3 gang_detect.py --llm --min-gang 3 --llm-top 30
```

Writes `$GMH_OUT_DIR/gang_graph.json`. **Sanity check**: the largest core gang should be
< 5% of total sellers and business-pure. If a >1000-person blob appears, the script
template is too broad — note it; do not silently proceed.

### Step 4 — Slang expansion

```bash
cd /mnt/skills/custom/graymarket-hunter/scripts && python3 slang_expand.py --llm
```

Writes `$GMH_OUT_DIR/slang_expanded.json`. Falls back to `--mine` (rules only) if no LLM.

### Step 5 — Visualization

```bash
cd /mnt/skills/custom/graymarket-hunter/scripts && python3 build_viz.py --top 80
```

Writes `$GMH_OUT_DIR/gang_viz.html`. Present it to the user with the `present_file` tool.

### Step 6 — Governance report

Read `$GMH_OUT_DIR/gang_graph.json` and synthesize an analyst report covering:
summary metrics; top super-gangs (the "one crew, many businesses" finding — this is
the headline); business-type distribution; geographic clustering; and prioritized
governance recommendations (target super-gangs, not single listings).

## Sub-agent fan-out (for large / multi-angle analysis)

When the dataset is large or the user wants depth, parallelize via sub-agents after
`gang_graph.json` exists. Each sub-agent has isolated context — give it the output
file path and a single focused question:

- **sub-agent A — Super-gang deep dive**: read `gang_graph.json`, for the top 5 `super_gangs` write the cross-business attack-chain narrative and rank by threat.
- **sub-agent B — Slang report**: read `slang_expanded.json`, group variants by business line, flag the highest-evasion ones, propose seed words to re-collect.
- **sub-agent C — Geo & business distribution**: aggregate `top_areas` / `top_segments` across gangs into tables + insights.
- **sub-agent D — Visualization QA**: open `gang_viz.html`, verify it renders and the top gangs are visible.

Then synthesize all sub-agent results into the final report.

## One-shot full pipeline

```bash
cd /mnt/skills/custom/graymarket-hunter/scripts \
  && export GMH_DATA_DIR=/mnt/xianyu-data GMH_OUT_DIR=/mnt/user-data/outputs GMH_DATA_GLOB='goofish_*.json' \
  && python3 gang_detect.py --min-gang 3 \
  && python3 slang_expand.py --mine \
  && python3 build_viz.py --top 80
```

(Add `--llm` flags once `GMH_LLM_MODEL` is set to your Ark endpoint.)

## Outputs

| File | Content |
|---|---|
| `gang_graph.json` | two-layer gang graph (core gangs + super-gang networks) — core deliverable |
| `slang_expanded.json` | coded-slang variant lexicon |
| `gang_viz.html` | interactive force-directed graph |

## Failure handling

- **Giant blob gang (>1000 people)**: template too broad. Note it; the fix is shortening the title-template length in `gang_detect.py` (`title_template`).
- **Gangs too fragmented**: lower `--min-gang` or loosen the template.
- **LLM failed / no key**: drop `--llm`, run the pure-algorithm path; report which annotations are rule-based vs LLM.
- **No data loaded**: wrong `GMH_DATA_DIR` or `GMH_DATA_GLOB`; verify with `ls /mnt/xianyu-data | head`.

## Notes

- Data collection is out of scope (manual anti-bot). This skill only analyzes.
- Dedup is by `itemId`. Two-layer model is mandatory — never use bare BFS connected components.
- Do NOT read the Python scripts; call them with the parameters above.
