# BGC Intel Pipeline

面向小红书 / 抖音等社交平台采集数据的黑灰产情报分析流水线。它把原始帖子 JSON 加工成防御性威胁情报，用于反诈、平台风控、Trust & Safety 和安全研究。

本项目只做识别、分析、聚合和展示，不生成任何用于实施黑灰产的工具或话术。

## 能做什么

- 清洗和去重采集到的帖子数据
- 从标题、正文、作者昵称、评论用户名、评论内容中提取黑话和风险信号
- 识别联系方式、报价、评论区询单、反诈伪装话术
- 计算帖子风险分
- 按作者、联系方式、参与用户等线索聚类团伙
- 输出离线 HTML 看板和 Markdown 分析报告

## 最终产出

一键运行后，最终只需要交付两个文件：

- `dashboard.html`：离线交互式情报看板
- `analysis_report.md`：Markdown 分析文档

中间的 `cleaned.json`、`records.json`、`analysis.json` 只作为内部流水线产物使用，默认不放进最终输出目录。

## 快速开始

```bash
python scripts/run_pipeline.py <采集目录或单个JSON> -o <输出目录>
```

示例：

```bash
python scripts/run_pipeline.py ./crawled_data -o ./bgc_out
```

输出：

```text
bgc_out/
  dashboard.html
  analysis_report.md
```

如果在 Codex / OpenHands 这类环境中交付给用户，建议写入：

```bash
python scripts/run_pipeline.py ./crawled_data -o /mnt/user-data/outputs/bgc_out
```

## Pipeline

```text
原始 JSON
  ↓
clean_dedup.py      清洗、字段归一化、精确/近似去重
  ↓
extract_intel.py    结构化情报提取、风险分计算
  ↓
analyze.py          风险过滤、团伙聚类、黑话种子汇总
  ↓
build_dashboard.py  生成 dashboard.html
build_report.py     生成 analysis_report.md
```

## 风险过滤口径

默认阈值：

- 情报明细：`risk_score > 50`
- 团伙聚类：`max_risk > 60`

也就是说：

- 单帖风险分小于等于 50，不进入最终情报明细
- 团伙簇峰值风险小于等于 60，不进入团伙聚类展示

可通过参数调整：

```bash
python scripts/run_pipeline.py ./crawled_data -o ./bgc_out \
  --min-risk 50 \
  --min-peak-risk 60
```

设为 `0` 可关闭对应过滤：

```bash
python scripts/run_pipeline.py ./crawled_data -o ./bgc_out \
  --min-risk 0 \
  --min-peak-risk 0
```

## 分阶段运行

需要人工检查中间结果时，可以分阶段运行：

```bash
python scripts/clean_dedup.py ./crawled_data -o cleaned.json --sim 0.92
python scripts/extract_intel.py cleaned.json -o records.json
python scripts/analyze.py records.json -o analysis.json --min-risk 50 --min-peak-risk 60
python scripts/build_dashboard.py analysis.json -o dashboard.html
python scripts/build_report.py analysis.json -o analysis_report.md
```

## 输入数据格式

支持三类 JSON 输入：

- 顶层是帖子数组：`[ {...}, {...} ]`
- 顶层是对象且包含 `notes`：`{ "notes": [ ... ] }`
- 顶层是单条帖子对象：`{ ... }`

推荐字段结构：

```json
{
  "note_id": "xxx",
  "platform": "xhs",
  "source_keyword": "跑分",
  "publish_time": "2026-06-10",
  "link": "https://...",
  "author": {
    "user_id": "u123",
    "nickname": "账号昵称",
    "ip_location": "广东"
  },
  "content": {
    "title": "标题",
    "desc": "正文"
  },
  "stats": {
    "liked_count": 10,
    "collected_count": 2,
    "comment_count": 3,
    "share_count": 1
  },
  "comments": [
    {
      "user": "评论用户",
      "content": "怎么联系",
      "like_count": 1
    }
  ]
}
```

字段缺失时脚本会尽量降级处理，但字段越完整，风险评估和团伙聚类越准确。

## 黑话与知识库

核心词典在：

```text
references/bgc_lexicon.json
```

建议优先扩充词典，而不是直接改脚本逻辑。词典包含：

- 业务类目关键词和风险权重
- 平台关键词
- 平台黑话
- 联系方式触发词和 ID 正则
- 去混淆映射
- 评论询单关键词
- 反诈伪装话术
- 报价提取正则

分类体系说明见：

```text
references/taxonomy.md
```

## 可选 LLM 黑话增强

默认情况下，流水线主要依赖规则和词典，不需要 LLM。

如果需要从高风险帖子的作者昵称、正文、评论中补充提取词典外黑话，可以开启：

```bash
export ARK_MODEL_ENDPOINT="ep-20260508212150-wgqpg"
export ARK_API_KEY="<your-api-key>"

python scripts/run_pipeline.py ./crawled_data -o ./bgc_out --llm-jargon
```

也可以显式传 endpoint：

```bash
python scripts/run_pipeline.py ./crawled_data -o ./bgc_out \
  --llm-jargon \
  --llm-endpoint ep-20260508212150-wgqpg
```

API key 不应写入代码或提交到仓库。

## 如何节省 LLM Token

设计原则：

```text
规则处理确定性任务，LLM 处理不确定语义。
```

具体策略：

- 去重、字段清洗、联系方式提取、报价提取、关键词命中、风险分计算都用代码完成
- 低风险、无业务命中、无评论询单、无黑话、无联系方式的内容不调用 LLM
- 给 LLM 的输入只保留作者昵称、标题、正文摘要、高价值评论、已命中标签和风险分
- 批量传入多条压缩记录，让 LLM 返回结构化 JSON
- LLM 发现的新黑话沉淀回本地词典，下次由规则直接命中
- 历史结果可按 `note_id`、文本 hash、联系方式 hash 复用

项目中的展示页：

```text
xhs_bgc_intel_thinking.html
```

用于说明 XHS 黑灰产情报收集思路、Pipeline、风险模型和 Token 优化策略，可直接用浏览器打开。

## 目录结构

```text
.
├── README.md
├── SKILL.md
├── xhs_bgc_intel_thinking.html
├── references/
│   ├── bgc_lexicon.json
│   └── taxonomy.md
└── scripts/
    ├── clean_dedup.py
    ├── extract_intel.py
    ├── analyze.py
    ├── build_dashboard.py
    ├── build_report.py
    └── run_pipeline.py
```

## 脚本说明

| 脚本 | 作用 |
|---|---|
| `clean_dedup.py` | 兼容多种 JSON 输入，清洗字段，按 `note_id` 和文本相似度去重 |
| `extract_intel.py` | 提取类目、平台、报价、联系方式、黑话、评论询单、风险分 |
| `analyze.py` | 风险过滤、团伙聚类、聚合统计、黑话搜索种子汇总 |
| `build_dashboard.py` | 生成自包含离线 HTML 看板 |
| `build_report.py` | 生成 Markdown 分析报告 |
| `run_pipeline.py` | 一键串联全部阶段，最终只输出 HTML 和分析文档 |

## 合规边界

本项目仅用于反诈、平台治理、信任与安全、安全研究等防御性场景。

不要用它去联系黑灰产卖家，不要据此实施刷量、引流、洗钱、诈骗、绕过风控等行为。提取出的联系方式、黑话和团伙线索仅作为情报线索，应交由平台安全团队、风控团队或有权机构进行处置。
