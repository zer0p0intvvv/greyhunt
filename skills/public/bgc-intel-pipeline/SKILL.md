---
name: bgc-intel-pipeline
description: 把社交平台（小红书/抖音等）采集到的原始帖子 JSON，加工成黑灰产（黑产/灰产）威胁情报：清洗去重、结构化情报提取（业务类目、目标平台、报价、联系方式、黑话、需求热度、风险评分）、团伙聚类分析，并最终生成离线 HTML 情报看板和 Markdown 分析文档。只要用户提到黑灰产 / 黑产 / 灰产 / 刷粉 / 刷量 / 刷单 / 跑分 / 引流 / 接码 / 反诈情报 / 平台风控 / 爬下来的帖子要做情报分析 / 把这些数据做成看板或报告，就应该使用本 skill——即使他们没有明确说出"情报流水线"几个字。处理的是「关于」黑灰产的情报（用于反诈、平台风控、安全研究），不是协助实施黑灰产。
---

# 黑灰产情报流水线 (BGC Threat-Intel Pipeline)

把采集来的社媒帖子，变成可供**反诈、平台信任与安全（Trust & Safety）、风控、安全研究**使用的结构化威胁情报。

这是一条防御性情报分析流水线：从公开/已采集的帖子里识别黑灰产**售卖方与需求方**的特征、归类业务、还原被混淆的联系方式、聚类团伙、量化风险，最终只交付一个可交互的离线看板和一份分析文档。它**不**生成任何用于实施黑灰产的内容或工具。

## 何时使用

用户手里有一批爬下来的帖子（通常是 JSON），想要：识别其中的黑灰产信息、清洗去重、提取情报、判断哪些最该处置、看团伙关联、做成可视化看板和分析报告。典型触发词：刷粉/刷量/刷单/跑分/接码/解封/引流/菠菜/黑话识别/反诈/风控/情报/团伙/看板/报告。

## 五个阶段（可一键串联，也可单独运行）

内部数据流：`原始 JSON → cleaned.json → records.json → analysis.json → dashboard.html + analysis_report.md`

最终交付只需要两个文件：
- `dashboard.html`：离线交互看板
- `analysis_report.md`：Markdown 分析文档

| 阶段 | 脚本 | 输入 → 输出 | 做什么 |
|---|---|---|---|
| 1 清洗去重 | `scripts/clean_dedup.py` | 采集目录/文件 → cleaned.json | 兼容多种 JSON 结构、字段归一化、note_id 精确去重、文本近似去重（识别铺量） |
| 2 情报提取 | `scripts/extract_intel.py` | cleaned.json → records.json | 结构化抽取各情报维度 + 风险评分，过滤无黑灰产特征的噪声 |
| 3 分析 | `scripts/analyze.py` | records.json → analysis.json | 团伙聚类（并查集）、供需/趋势/属地聚合；**按峰值风险过滤团伙**；**汇总黑话搜索种子** |
| 4 可视化 | `scripts/build_dashboard.py` | analysis.json → dashboard.html | 自包含离线 HTML 看板（无 CDN 依赖，可交互筛选） |
| 5 分析文档 | `scripts/build_report.py` | analysis.json → analysis_report.md | 面向处置和复盘的 Markdown 分析文档 |

### 一键运行（推荐默认）

```bash
python scripts/run_pipeline.py <采集目录或单个JSON> -o /mnt/user-data/outputs/<任务名>
# 例：python scripts/run_pipeline.py ./crawled_data -o /mnt/user-data/outputs/bgc_out
# 最终产出 /mnt/user-data/outputs/bgc_out/dashboard.html + analysis_report.md
```

运行完，用 `present_files` 把 `/mnt/user-data/outputs/<任务名>/dashboard.html` 和 `/mnt/user-data/outputs/<任务名>/analysis_report.md` 交给用户即可。交付给前端预览/下载的文件必须位于 `/mnt/user-data/outputs/`；可以读取 `/mnt/grayhunt-db` 等共享数据源，但不要把这些共享库路径直接传给 `present_files`。

### 分阶段运行（需要中途人工核查时）

```bash
python scripts/clean_dedup.py   ./crawled_data -o cleaned.json   [--sim 0.92]
python scripts/extract_intel.py cleaned.json   -o records.json   [--lexicon references/bgc_lexicon.json]
python scripts/analyze.py       records.json   -o analysis.json [--min-risk 50] [--min-peak-risk 60]
python scripts/build_dashboard.py analysis.json -o dashboard.html
python scripts/build_report.py    analysis.json -o analysis_report.md
```

一键运行同样支持透传：`python scripts/run_pipeline.py <输入> -o <输出目录> [--min-risk 50] [--min-peak-risk 60] [--sim 0.92]`

## 提取的情报维度（records.json 每条字段）

- `biz_categories`：业务类目及命中的黑话（刷量造假 / 电商刷单 / 引流截流 / 账号买卖申诉 / 资金洗钱 / 赌博诈骗 / 违规技术）
- `target_platforms`：目标平台（抖音/快手/小红书/…）
- `prices`：报价（金额 + 就近量纲，如 `200元/1000粉`、`0.2元/粉`）
- `contacts`：联系方式（微信/QQ/Telegram/手机；先做**去混淆**再正则匹配，能抓 `薇➕：xxx`、`扣扣：xxx`、`飞机：@xxx` 这类）
- `jargon_hits`：平台黑话命中（橱窗/起号/养号/有效粉/四件套…）
- `jargon_sources`：用于黑话复核/扩展的作者昵称、帖子正文、评论用户名和评论内容片段
- `demand_signals`：评论区**需求热度**——买家询单意向计数 + 样本（"怎么联系""礼貌问价"）
- `scam_disguise`：**反诈伪装话术**命中（"私信你们的可能是骗子""认准官方"——把流量引回自家渠道的高可信度指征）
- `risk_score` (0-100) 与 `risk_tags`：综合业务危害权重、联系方式露出、明码标价、需求热度、伪装话术、黑话密度

## 分析阶段：风险过滤 + 黑话搜索种子

`analyze.py` 在聚类与聚合之外，多做三件事：

**① 按单帖风险过滤情报明细（`--min-risk`，默认 50）**
- `risk_score <= 50` 的帖子默认不进入 `analysis.json` 与 `dashboard.html` 情报明细，避免低质噪声污染明细、聚合、黑话种子。
- 设 `--min-risk 0` 可关闭单帖过滤，用于全量复盘或调试评分。

**② 按峰值风险过滤团伙（`--min-peak-risk`，默认 60）**
- "峰值风险"指**团伙簇内最高的 `risk_score`**（`gang.max_risk`）。峰值 `<= 60` 的整簇——连同它的全部帖子——直接剔除，团伙聚类区只展示 `max_risk > 60` 的目标。
- 单帖低分会先被 `--min-risk` 剔除；剩余记录再按团伙峰值过滤和重编号。
- 过滤后 `records` 与 `gangs` 同步收缩、保持一致，`gang_id` 重新连续编号。
- 设 `--min-peak-risk 0` 关闭团伙峰值过滤。阈值并非越高越好：单纯挂联系方式的卖家约落在 50–70，带报价+伪装话术+评论区高需求的强信号轻松过 60；默认 60 用于滤掉买家/新手/泛泛而谈的噪声。需要更全的线索时调低（如 40），只盯最该处置的目标时调高。

**③ 汇总黑话搜索种子（`summary.jargon_collection`）**
- 把整批高风险情报里出现过的黑话（`jargon_hits` 平台黑话 + `biz_categories[*].matched` 类目命中词）**跨语料汇总**，按出现频次降序排列。
- 每个词带：`count` 频次、`type`（平台黑话/类目黑话/模型提取类型）、共现的 `platforms` 与 `categories`，以及来自作者昵称、正文、评论用户名或评论内容的 `evidence` 样本，便于判断拿哪些词、在哪个平台继续搜。
- `search_seeds` 是扁平、去重、按热度排序的词表——**直接回灌采集器做下一轮检索**，顺着黑话把检索面滚大。看板里有专门的"黑话搜索种子"区，可一键复制全部种子词。
- 可选启用火山方舟大模型从昵称/正文/评论中补充词典外黑话：

```bash
export ARK_MODEL_ENDPOINT="ep-20260508212150-wgqpg"
export ARK_API_KEY="<挑战周期提供的 API key>"
python scripts/run_pipeline.py ./crawled_data -o ./bgc_out --llm-jargon
```

> 注意：过滤发生在**汇总之前**，所以黑话种子只来自被保留下来的高风险情报，避免低质噪声污染下一轮搜索词。若想从全量语料提种子，用 `--min-risk 0 --min-peak-risk 0` 单独跑一次 `analyze.py`。

## 核心知识库：`references/bgc_lexicon.json`

整条流水线的"识别大脑"，**优先扩充这里**而不是改脚本逻辑。包含：
- `business_categories`：各业务类目的黑话词 + 危害权重（weight 越高风险贡献越大）
- `platforms` / `platform_jargon`：平台词与黑话释义
- `contact_patterns`：各联系方式的触发词 + ID 正则
- `obfuscation_map`：同音/形近/全角混淆字归一化表（如 `薇→微`、`➕→+`、`壹→1`）
- `demand_signal_keywords` / `scam_disguise_keywords` / `price_patterns`

新增黑话/平台/混淆变体时，直接编辑此 JSON，无需动代码。分类体系的设计说明见 `references/taxonomy.md`。

## 调参与排错经验（实测踩过的坑）

- **平台词别用单字**：`快`会误命中"快速"，`抖`会误命中"抖动"。平台关键词保留双字以上或专有 token（千川/星图/橱窗），单字 token 一律不要。
- **联系方式先去混淆再匹配**：`薇➕：daihao_2026` 去混淆后是 `微+：daihao_2026`。触发词表里要同时有 `微信` 和**裸字 `微`**，否则去混淆后反而漏掉。新增混淆写法时，成对更新 `obfuscation_map` 和对应 `trigger_words`。
- **报价就近匹配**：金额与量词分开抽，再按字符距离（默认 25 字符内）配对，避免把"算法变动"里的数字当报价。
- **近似去重阈值** `--sim`：默认 0.92。团伙常换号铺同一段文案，调低到 0.85 可合并更多变体，但会误并相似模板帖；调高更保守。
- **联系方式缺失是常态**：合规账号常把联系方式藏在评论/私信/二维码图片里。正文无联系方式但评论区询单密集 + 有伪装话术，本身就是强信号——风险分会据此抬高。

## 输出与交付

最终交给用户的只有：
- `dashboard.html`（双击即可离线打开）：顶部是**"数据全貌"卡片墙**，原始采集→跨关键词去重→噪声剔除→高质量情报→团伙聚类→高危帖子→黑话搜索种子→联系方式→需求询单，端到端漏斗一屏看完；往下是类目/平台分布、风险分布、属地 TOP、黑话搜索种子区、团伙簇、可搜索筛选排序的情报明细。
- `analysis_report.md`：包含数据漏斗、风险分布、类目/平台/属地 TOP、高优先级团伙、高风险明细、黑话搜索种子、处置建议和合规说明。

漏斗数字来自各阶段写出的计数边车：`clean_dedup.py` 写 `cleaned.meta.json`、`extract_intel.py` 写 `records.meta.json`，`analyze.py` 自动汇入 `summary.pipeline_stats`（单独跑 analyze 且无边车时，看板会自动跳过缺数据的卡片，只展示能算出的）。一键运行时 `cleaned.json` / `records.json` / `analysis.json` 都是内部中间产物，不作为最终交付文件。

路径规则：最终看板和分析文档统一写入 `/mnt/user-data/outputs/<任务名>/`。如果中间过程读取了 `/mnt/grayhunt-db` 中的历史数据或共享数据库，需要把面向用户的最终交付副本复制或重新生成到 `/mnt/user-data/outputs/` 后再调用 `present_files`。

## 合规边界

本 skill 仅用于**识别与分析**黑灰产活动以支持反诈、平台治理与安全研究。不要用它去联系黑灰产卖家、不要据此实施任何刷量/引流/洗钱等行为、不要生成营销话术或攻击工具。提取出的联系方式仅作为情报线索，交由平台/执法等有权方处置。
