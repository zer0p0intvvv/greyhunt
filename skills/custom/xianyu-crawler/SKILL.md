---
name: xianyu-crawler
description: "Trigger 闲鱼(Goofish) data collection via the local Playwright spider. Takes keywords from conversation, launches the host browser with QR-scan login, saves listing data as goofish_*.json files under the mounted /mnt/xianyu-data directory. Trigger when the user asks to crawl/search/collect/爬/采集 Xianyu or 闲鱼 data for specific keywords."
---

# xianyu-crawler — 闲鱼数据采集（桥接 RPA 爬虫）

## What this skill does

Triggers the local Playwright-based 闲鱼 spider (`search_only.py`) on the host machine.
It opens a visible Chromium browser, waits for the user to scan the QR code to login,
then searches each keyword and saves results as `goofish_*.json` files.

The agent does NOT need to do the QR scan — the human does. The agent's job is to:
1. Accept keywords from the conversation
2. Launch the crawler process
3. Report results (file count, item count, new data volume)

## Data contract

Output files land in `/mnt/xianyu-spider/data/` (host path, accessible via `/mnt/xianyu-data` for analysis).

Each output file is JSON: `{"keyword": "...", "count": N, "items": [{itemId, title, seller, ...}]}`

## Crawl command

The spider runs on the host via `allow_host_bash: true`. The host Python has
Playwright + Openai installed. The browser window pops up on the host desktop
(independent of the sandbox). The command format:

```bash
cd /mnt/xianyu-spider && /opt/homebrew/bin/python3 -u search_only.py "关键词1" "关键词2" --pages 15
```

For crawls that take longer than 10 minutes (many keywords × deep pages),
use background mode so the agent doesn't timeout:

```bash
cd /mnt/xianyu-spider && nohup /opt/homebrew/bin/python3 -u search_only.py "kw1" "kw2" --pages 15 > /mnt/user-data/outputs/crawl.log 2>&1 &
```

Options:
- `--pages N`: pages per keyword (default 2; use 5-15 for deep crawl)
- `--detail N`: visit first N detail pages after search (adds want/view/sold fields)

## Workflow

### Step 1 — Confirm keywords with user

Ask the user: "你要爬哪些关键词？每词爬几页？"
Default `--pages 15` for competition-grade data, `--pages 3` for quick test.

### Step 2 — Count baseline files

```bash
ls /mnt/xianyu-data/goofish_*.json | wc -l
```
This is the "before" count. The "after" count minus this is how many new files were produced.

### Step 3 — Run the crawl (SYNC — wait for it to finish)

**CRITICAL: Run the command synchronously (NOT with `&`). The bash tool will block
until the crawl finishes (~2-3 min for small crawls). The browser pops up on the
host during execution. You will naturally continue after the command returns.**

```bash
mkdir -p /mnt/user-data/outputs && cd /mnt/xianyu-spider && /opt/homebrew/bin/python3 -u search_only.py "keyword1" "keyword2" --pages 2
```

For longer crawls (50+ keywords), use background mode and poll:
```bash
mkdir -p /mnt/user-data/outputs && cd /mnt/xianyu-spider && nohup /opt/homebrew/bin/python3 -u search_only.py "${words[@]}" --pages 15 > /mnt/user-data/outputs/crawl.log 2>&1 &
```

### Step 4 — Report & continue to analysis

After the command returns (sync mode) or after polling confirms completion (bg mode),
report and immediately run the analysis pipeline:

## Pre-flight checks

Before crawling, verify:
- Playwright is installed: `/opt/homebrew/bin/python3 -c "import playwright; print('ok')" 2>&1` should print `ok`
- Chromium is installed: `ls ~/Library/Caches/ms-playwright/ | grep chromium` should show versions
- Data directory exists: `ls /mnt/xianyu-spider/data/` should list existing JSON files

If any check fails, tell the user to run: `/opt/homebrew/bin/python3 -m playwright install chromium`

## Batch crawl from keyword file

To crawl from a keyword file in background mode:

```bash
mkdir -p /mnt/user-data/outputs && cd /mnt/xianyu-spider
words=("${(@f)$(< /path/to/keywords.txt)}")
nohup /opt/homebrew/bin/python3 -u search_only.py "${words[@]}" --pages 15 > /mnt/user-data/outputs/crawl.log 2>&1 &
```

For hygiene, kill any stale crawler before starting a new one:
```bash
pkill -f "search_only.py" 2>/dev/null
```

## Performance

- Each keyword × 15 pages ≈ 300-450 items · 60-120 seconds
- 50 keywords × 15 pages ≈ 20,000 items · 50-80 minutes
- QR login is needed ONCE per crawl session

## Anti-bot notes

The spider uses real browser interaction (types in search box, clicks submit) to
trigger the page's JS SDK which auto-signs the MTOP API request. It does NOT
construct search URLs directly. Delays between pages (2.5-4s) are built in.
If x5sec triggers a slider challenge, the user must solve it manually in the
browser window.