# 🛡️ GrayHunt · 黑灰产情报智能体

> Telegram + Twitter/X + 闲鱼 + 小红书/抖音 多平台黑灰产情报系统。**一条对话**驱动
> 采集 → 清洗去重 → 落库 → 情报提取 → 团伙挖掘 → 黑话飞轮 → 研判 → 可视化 全链路。
> 用**多模态视觉**挖出藏在图片里的情报,用**两层团伙模型**挖出"一波人做多业务"的超级网络,用**规则 + LLM 双层架构**把成本压到极致。

针对抖音 / TikTok / 字节系平台的刷量作弊、账号交易、代充代投、引流诈骗、跑分洗钱、工具交易等黑灰产风险,做自动化情报作业与团伙级治理。**本项目只做识别、分析、聚合和展示,不生成任何用于实施黑灰产的工具或话术。**

---

## ✨ 核心能力

| 能力 | 说明 |
|---|---|
| **多平台采集** | Telegram(已加入群,零封号)+ Twitter/X(TikHub API)+ 闲鱼(Playwright MTOP API)+ 小红书/抖音(采集 JSON 接入) |
| **多模态提取** | LLM 视觉识别**图片里**的微信/TG/QQ 账号、域名、价目表、二维码(纯文本搜不到的情报) |
| **智能清洗** | 精确 + 近似去重(文本相似度),字段归一化,关键词预筛 + LLM 双层过滤 |
| **情报提取** | 业务类目、目标平台、报价、联系方式、黑话、评论询单、反诈伪装话术、**风险分** |
| **沉淀落库** | SQLite 按数据源分表 + JSON/CSV,实体不脱敏、可溯源,支持多库联邦合并 |
| **团伙挖掘** | 两层团伙模型:话术指纹聚出核心团伙(马甲号),union-find 关联出超级团伙 |
| **黑话飞轮** | 自动挖掘黑话变体并回灌词典,采集-分析自我强化闭环 |
| **情报研判** | SQL 聚合(风险分布/Top 高危群/高频引流渠道)+ LLM 研判报告 + 治理建议 |
| **可视化** | 离线交互式 HTML 情报大屏 + D3 团伙知识图谱 + Markdown 分析报告 |
| **低成本** | 规则层压缩 LLM 调用 99%+,单次全流程 < $0.30 |

---

## 🎯 关键数据

| 指标 | 数值 |
|---|---|
| 原始数据 → 高质量数据 | 138K+(375 文件)→ 71.8K(漏斗去噪后) |
| 核心团伙 / 超级团伙 | 514 / 20,头号超级团伙 **18 团 / 579 人**(跨业务联合作案) |
| 黑话词库 | 446 关键词覆盖 20 条产品线 + 黑话词典(去混淆映射/询单话术/报价正则),飞轮自动挖掘 89 个变体 |
| LLM 成本 | 实测 2795 条消息仅 2 条进 LLM(省 99.9%);单次全流程 < $0.30 / < 3 min |

---

## 💡 设计亮点

### 1. 规则 + LLM 双层架构,把成本压到极致
设计原则:**规则处理确定性任务,LLM 处理不确定语义。**
- 去重、字段清洗、联系方式/报价提取、关键词命中、风险分计算全部用代码零 Token 完成
- 本地关键词矩阵(products × actions)粗筛,低风险/无命中内容不调用 LLM——实测某 Telegram 群 30 天 2795 条仅 2 条进 LLM
- 送 LLM 的输入只保留昵称、标题、正文摘要、高价值评论与已命中标签,批量传入(15 条/次)、返回结构化 JSON
- 历史结果按 `note_id` / 文本 hash / 联系方式 hash 复用,不重复研判

### 2. 多模态情报提取:挖出"藏在图片里"的情报
黑产为规避文本检测,把微信号、TG 号、域名、价目表、二维码印在图片里。GrayHunt 用视觉 LLM **OCR + 视觉理解还原图中信息**(如完整识别"支付宝白号¥158 / 年号¥439"价目表)——纯文本采集完全拿不到的关键情报。

### 3. 两层团伙模型:从散点情报到团伙网络
```
第一层:核心团伙 —— 相同话术模板 = 同一团伙的马甲号(sock-puppets)
                    不做 BFS 链式膨胀,每个团伙业务纯净、可审计、可解释
                        ↓ union-find(共享卖家/联系方式 + 同图 + 同话术)
第二层:超级团伙 —— 把多个表面独立的业务团伙连成「一波人做多业务」的超级网络
```
**头条结论永远是超级团伙网络——治理应针对超级团伙,而非单个群组或商品链接。**
团伙聚类支持风险口径过滤(默认:情报明细 `risk_score > 50`,团伙簇峰值 `max_risk > 60`,可调可关)。

### 4. 黑话飞轮(自我强化闭环)
```
①采集 → ②清洗落库 → ③情报提取 → ④团伙挖掘 → ⑤黑话挖掘 → ⑥研判报告
                                        │
        ⑦命中黑话扩展成新搜索词 ──自动回灌词典──→ 回到①
```
LLM 发现的新黑话自动沉淀回本地词典(备份 + 去重),下次由规则直接零成本命中。4 轮飞轮:原始量 55K → 138K,核心团伙 312 → 514。

### 5. 黑话词典即知识库
核心词典 `references/bgc_lexicon.json` 集中维护:业务类目关键词与风险权重、平台黑话、联系方式触发词与 ID 正则、去混淆映射、评论询单关键词、反诈伪装话术、报价提取正则。**扩充词典优先于改脚本逻辑**,分类体系见 `references/taxonomy.md`。

### 6. 群链接精准溯源
**用 Telegram 的 `group_id` 派生真实群链接**(而非误用正文里推广的关联群链接),公开群可直接点进、私密群带 🔒 标识——保证每条情报都能准确回溯到源头。

### 7. 多源统一情报库 + 把库当知识库
采集**即清洗即落库**,按数据源分表(`telegram_intel_*` / `twitter_intel_*` / `xianyu_intel_*` / `xhs_intel_*`)。分析层既有确定性 SQL 聚合,也支持 **agent 自由写只读 SQL** 把整个情报库当知识库问。

### 8. 内置安全护栏
智能体 SOUL 内置完整工作流与**硬护栏**:严禁编造/模拟数据、账号实体不脱敏(情报溯源需要)、Telegram 高危操作先确认防 FloodWait、`discover` 默认只列出不加群。

### 9. 离线自包含可视化
最终只交付两个文件:`dashboard.html`(离线交互式情报大屏,`--embed-images` 图片内嵌 base64)+ `analysis_report.md`(Markdown 研判报告);另有 D3 团伙图谱 `gang-viz.html`。全部零外部依赖,双击即开,可直接分发。

---

## 🚀 快速开始

### 前置依赖
- **Node.js ≥ 22**、**pnpm**、**uv**、**nginx**(macOS:`brew install node@22 pnpm uv nginx`)
- 支持视觉的大模型(推荐火山方舟 Doubao,需 `supports_vision`)
- Telegram 采集:Telegram API(api_id/api_hash/手机号)+ 本地 socks5 代理
- Twitter 采集:[TikHub](https://tikhub.io) API Key

### 步骤 1 · 安装与配置

```bash
make config                       # 复制 config.example.yaml -> config.yaml
echo "VOLCENGINE_API_KEY=ark-xxxx" >> .env
make check && make install
```

编辑 `tg-intel-crawler/config/config.yaml`:

```yaml
telegram:
  api_id: <你的>                  # https://my.telegram.org 申请
  api_hash: <你的>
  phone: "+86xxxxxxxxxxx"
  proxy: { type: socks5, host: 127.0.0.1, port: 7897 }
llm:
  api_key: <你的模型key>
  base_url: https://ark.cn-beijing.volces.com/api/v3
  model: <你的 EP>
twitter:
  api_key: <TikHub key>
```

> ⚠️ `config.yaml`、`.env`、`*.session` 含密钥/登录态,已被 `.gitignore` 忽略,不会提交。

### 步骤 2 · 启动服务

```bash
make dev
```

访问 **http://localhost:2026**(Nginx 统一入口),首次需注册/登录。

---

## 🤖 使用方式一:对智能体说一句话

进 **Agents** 页面,选择 `telegram-twitter-gray-hunter`,一条提示词跑通全流程:

```
完成一次完整的黑灰产情报作业:
① Telegram crawl --joined-only --days 30 + Twitter crawl-twitter --days 7 --vision
   + 闲鱼/小红书采集数据接入
② 清洗去重落库,提取情报与风险分,挖掘核心团伙与超级团伙,黑话变体回灌词典
③ analyst 研判:风险分布、TOP 超级团伙、高频引流渠道(不脱敏),出治理建议
④ 生成 dashboard.html 情报大屏(--embed-images)+ 团伙图谱 + analysis_report.md
全程真实数据严禁编造,实体不脱敏,每步汇报关键统计。
```

---

## 🛠️ 使用方式二:命令行

### 采集与大屏(tg-crawler CLI)

```bash
cd tg-intel-crawler
export TG_INTEL_CRAWLER_HOME=$(pwd)

tg-crawler crawl --joined-only --mode history --days 30   # Telegram 已加入群(最安全)
tg-crawler crawl-twitter --days 7 --vision                # Twitter + 图片视觉提取
tg-crawler report-html --embed-images --output grayhunt.html
```

| 命令 | 作用 | 是否触碰 Telegram |
|---|---|---|
| `crawl --joined-only` | 爬已加入群历史(最安全) | 是(只读,零封号) |
| `crawl-twitter [--vision]` | 爬 Twitter/X,可视觉提取图片 | 否(走 TikHub API) |
| `discover` | 按关键词发现新群(默认只列出) | 是(有 FloodWait 风险) |
| `candidates` | 候选群池治理(stats/verify/approve) | 部分 |
| `report-html` | 生成可视化 HTML 大屏 | 否 |

### 社交平台采集数据分析(BGC Pipeline)

针对小红书/抖音等已采集的帖子 JSON,一键产出看板 + 报告:

```bash
python scripts/run_pipeline.py ./crawled_data -o ./bgc_out \
  --min-risk 50 --min-peak-risk 60        # 风险口径可调,设 0 关闭过滤
```

```text
原始 JSON → clean_dedup.py(清洗去重)→ extract_intel.py(情报提取+风险分)
         → analyze.py(过滤+团伙聚类)→ build_dashboard.py + build_report.py
```

需要补充词典外黑话时开启可选 LLM 增强:

```bash
export ARK_API_KEY="<your-api-key>"
python scripts/run_pipeline.py ./crawled_data -o ./bgc_out --llm-jargon
```

支持三类 JSON 输入(帖子数组 / `{"notes": [...]}` / 单条对象),字段缺失会降级处理;也可分阶段运行各脚本以便人工检查中间结果。

---

## 📁 项目结构

```
grayhunt/
├── backend/  frontend/             # Agent 后端 + Next.js 前端
├── skills/
│   ├── threat-intel-collector/     # Telegram/Twitter 采集 + 清洗 + 落库
│   ├── threat-intel-curator/       # 候选群池治理
│   ├── threat-intel-analyst/       # 分析研判 + 可视化大屏
│   ├── graymarket-hunter/          # 团伙挖掘:两层团伙 / 黑话飞轮 / 图谱
│   │   └── scripts/                #   gang_detect / slang_expand / build_viz ...
│   └── bgc-intel-pipeline/         # 小红书/抖音采集数据分析流水线
│       ├── references/             #   bgc_lexicon.json 黑话词典 + taxonomy.md
│       └── scripts/                #   clean_dedup / extract_intel / analyze
│                                   #   build_dashboard / build_report / run_pipeline
├── tg-intel-crawler/               # 底层采集器(CLI: tg-crawler)
│   └── output/intel.db             #   情报库(SQLite,gitignore)
├── grayhunt.html                   # 情报大屏快照(离线自包含)
└── gang-viz.html                   # 交互式团伙图谱
```

---

## 📊 可视化

- **情报大屏 `dashboard.html` / `grayhunt.html`**:按来源群组/作者聚合,四维筛选(风险等级/类别/平台/来源),群链接可点(私密群 🔒),图片缩略图 + 图中 OCR 信息,完全离线单文件
- **团伙知识图谱 `gang-viz.html`**:D3 力导向图,直观呈现核心团伙与超级团伙的关联网络
- **研判报告 `analysis_report.md`**:团伙总览 / TOP 超级团伙 / 风险分布 / 黑话种子 / 治理建议

---

## 🔒 安全与合规

- 本项目仅用于**反诈、平台治理、Trust & Safety 与安全研究**等防御性场景,只做识别、分析、聚合和展示
- **不要**用它联系黑灰产卖家,**不要**据此实施刷量、引流、洗钱、诈骗、绕过风控等行为;提取出的联系方式、黑话和团伙线索仅作为情报线索,应交由平台安全/风控团队或有权机构处置
- 所有 API key 经环境变量引用,代码与配置中无明文凭证;`config.yaml`、`.env`、`*.session`、情报库均被 `.gitignore` 忽略
- SOUL 硬护栏:严禁编造数据、Telegram 高危操作先确认防封号、`discover` 默认不加群
