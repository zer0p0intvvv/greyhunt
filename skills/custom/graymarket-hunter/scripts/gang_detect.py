"""
黑灰产团伙检测 V2 - 两层模型

第一层【核心团伙】：以"主导话术模板"为锚，同模板的卖家 = 一个核心团伙。
  - 不做 BFS 链式传播，避免不同业务被桥接节点串成巨无霸
  - 每个核心团伙业务单一、话术一致，是"铁打的同一组马甲"

第二层【超级团伙网络】：核心团伙之间的关联（揭示"一波人做多业务"）
  - 同一卖家出现在多个核心团伙 → 跨业务同主体
  - 核心团伙之间同图 / 话术骨架相近 → 同一货源/文案库
  - 输出团伙间的关联边，构成"超级团伙"

用法:
  python3 gang_detection_v2.py --min-gang 3
  python3 gang_detection_v2.py --llm --llm-top 30
"""

import json, re, argparse
from pathlib import Path
from collections import Counter, defaultdict

from gmh_paths import out_dir

OUT_DIR = out_dir()

from data_loader import load_items
from llm_client import llm

# ─── 特征提取（复用 v1 逻辑）───
_SEGMENT_KEYS = [
    "起号",
    "涨粉",
    "上热门",
    "Dou+",
    "抖+",
    "豆荚",
    "抖jia",
    "dou",
    "dou+",
    "抖币",
    "充值",
    "钻石",
    "直播",
    "代投",
    "推广",
    "曝光",
    "数据",
    "会员",
    "卡券",
    "代拍",
    "客服",
    "外包",
    "运营",
    "精选",
    "短视频",
    "抖店",
    "千川",
    "灰豚",
    "蝉妈妈",
    "考古加",
    "抖查查",
    "抖狸",
    "Nico",
    "douli",
    "本地推",
    "图文",
    "带货",
    "权限",
    "开通",
    "回流",
    "升级",
    "限流",
    "搬运",
    "新号",
    "老号",
    "粉丝",
    "流量",
    "权重",
    "黄V",
    "蓝V",
    "解封",
    "养号",
    "音浪",
    "tk",
    "tiktok",
    "剪映",
    "capcut",
    "ai",
    "v",
    "qq",
    "Q",
    "扣",
    "薇",
    "地球",
    "微",
    "加我",
    "私",
    "联系",
]


def segment_sig(title):
    t = title.lower()
    return tuple(sorted(set(kw for kw in _SEGMENT_KEYS if kw.lower() in t))[:10])


def image_fp(item):
    m = re.search(r"O1CN01.{13,20}", item.get("image", ""))
    return m.group(0)[:18] if m else ""


def publish_bucket(item):
    m = re.match(r"(\d{4}-\d{2}-\d{2})\s(\d{2}):", item.get("publishTime", ""))
    return f"{m.group(1)} {m.group(2)}h" if m else ""


def title_template(title):
    """标题话术模板指纹：去数字/符号/英文，取前 12 个中文字"""
    if not title:
        return ""
    t = re.sub(r"[^\u4e00-\u9fff]", "", re.sub(r"[0-9]+", "", title))
    return t[:12]


BLACK_KW = re.compile(
    r"抖币|钻石|充值|代充|直充|秒到|代投|dou\+|抖\+|豆荚|抖加|抖jia|千川|抖店|"
    r"涨粉|刷|起号|养号|解封|限流|权重|蓝v|黄v|企业号|认证|开通|权限|带货|"
    r"灰豚|蝉妈妈|考古加|抖查查|飞瓜|数据.{0,4}(会员|卡|版)|卡券|卡卷|卡密|"
    r"代运营|矩阵|引流|代拍|快充|慢充|金币|音浪|tk|tiktok|教程|陪跑|出单|剪映|capcut",
    re.I,
)


# ─── 第一层：核心团伙（以主导话术模板聚类）───
def build_core_gangs(items, min_gang=3):
    # 卖家聚合
    sellers = defaultdict(list)
    for it in items:
        s = (it.get("seller") or "").strip()
        if s:
            sellers[s].append(it)

    # 每个卖家的特征
    node = {}
    for s, its in sellers.items():
        areas = [it.get("area", "") for it in its]
        segs = []
        for it in its:
            segs.extend(segment_sig(it.get("title", "")))
        imgs = [image_fp(it) for it in its if image_fp(it)]
        pubs = [publish_bucket(it) for it in its if publish_bucket(it)]
        tpls = [title_template(it.get("title", "")) for it in its]
        tpls = [t for t in tpls if len(t) >= 6]
        node[s] = {
            "count": len(its),
            "area": Counter(areas).most_common(1)[0][0] if areas else "",
            "segment": tuple(sorted(set(segs))[:8]),
            "image_fp": Counter(imgs).most_common(1)[0][0] if imgs else "",
            "pubs": pubs,
            "templates": set(tpls),
            # 主导话术模板（该卖家用得最多的那套文案）
            "main_tpl": Counter(tpls).most_common(1)[0][0] if tpls else "",
            "sample_title": its[0].get("title", "")[:80],
            "sample_link": its[0].get("link", ""),
        }

    # 按主导话术模板分组 = 核心团伙
    tpl_group = defaultdict(list)
    for s, n in node.items():
        if n["main_tpl"]:
            tpl_group[n["main_tpl"]].append(s)

    core_gangs = []
    for tpl, members in tpl_group.items():
        if len(members) < min_gang:
            continue
        # 黑产过滤
        black = sum(1 for s in members if BLACK_KW.search(node[s]["sample_title"]))
        if black < max(2, len(members) * 0.4):
            continue
        core_gangs.append({"tpl": tpl, "members": members})

    core_gangs.sort(key=lambda g: -len(g["members"]))
    return node, core_gangs


# ─── 第二层：核心团伙之间的关联（超级团伙）───
def link_super_gangs(node, core_gangs):
    """找核心团伙之间的关联：共享卖家 / 同图 / 话术骨架相近"""
    # 团伙 id
    for i, g in enumerate(core_gangs):
        g["id"] = i + 1

    # 卖家 -> 所属核心团伙（一个卖家可能因不同商品归到多个组，但 main_tpl 唯一）
    # 这里用"该卖家的所有话术模板"来找跨团伙
    seller_in = defaultdict(set)  # seller -> {gang_id}
    img_in = defaultdict(set)  # image_fp -> {gang_id}
    tpl_set = {}  # gang_id -> set(所有成员的话术模板)
    area_in = defaultdict(set)  # area -> {gang_id}

    for g in core_gangs:
        gid = g["id"]
        tpls = set()
        for s in g["members"]:
            seller_in[s].add(gid)
            if node[s]["image_fp"]:
                img_in[node[s]["image_fp"]].add(gid)
            tpls |= node[s]["templates"]
            if node[s]["area"]:
                area_in[node[s]["area"]].add(gid)
        tpl_set[gid] = tpls

    # 团伙间关联边
    pair_evidence = defaultdict(lambda: defaultdict(int))  # (g1,g2) -> {reason: count}

    # ① 同一卖家跨团伙（最强证据）
    for s, gids in seller_in.items():
        if len(gids) > 1:
            gl = sorted(gids)
            for i in range(len(gl)):
                for j in range(i + 1, len(gl)):
                    pair_evidence[(gl[i], gl[j])]["同卖家"] += 1

    # ② 同图跨团伙
    for fp, gids in img_in.items():
        if len(gids) > 1:
            gl = sorted(gids)
            for i in range(len(gl)):
                for j in range(i + 1, len(gl)):
                    pair_evidence[(gl[i], gl[j])]["同图"] += 1

    # ③ 话术模板交集跨团伙（同一文案库）
    gids = [g["id"] for g in core_gangs]
    # 用倒排避免 O(n²)：tpl -> gangs
    tpl_to_gangs = defaultdict(set)
    for gid in gids:
        for t in tpl_set[gid]:
            tpl_to_gangs[t].add(gid)
    for t, gs in tpl_to_gangs.items():
        if len(gs) > 1 and len(gs) <= 30:  # 排除超通用模板
            gl = sorted(gs)
            for i in range(len(gl)):
                for j in range(i + 1, len(gl)):
                    pair_evidence[(gl[i], gl[j])]["共享话术"] += 1

    # 汇总成边（要求证据足够）
    super_edges = []
    for (g1, g2), ev in pair_evidence.items():
        strength = (
            ev.get("同卖家", 0) * 3 + ev.get("同图", 0) * 2 + ev.get("共享话术", 0)
        )
        if strength >= 2:  # 至少有实质证据
            super_edges.append(
                {"g1": g1, "g2": g2, "strength": strength, "evidence": dict(ev)}
            )

    super_edges.sort(key=lambda e: -e["strength"])

    # 用并查集把关联的核心团伙聚成"超级团伙"
    parent = {g["id"]: g["id"] for g in core_gangs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for e in super_edges:
        union(e["g1"], e["g2"])

    super_groups = defaultdict(list)
    for g in core_gangs:
        super_groups[find(g["id"])].append(g["id"])
    super_groups = {k: v for k, v in super_groups.items() if len(v) > 1}

    return super_edges, super_groups


# ─── LLM 命名 ───
def llm_gang_label(node, members):
    samples = "\n".join(f"- [{s}] {node[s]['sample_title'][:90]}" for s in members[:8])
    prompt = f"""你是安全分析师。以下闲鱼卖家用同一套话术文案，属于同一黑灰产团伙。请：
1. 起中文团伙名（如"抖音代投马甲群"）
2. 判断核心黑产业务
3. 输出 JSON: {{"name":"团伙名","biz":"核心业务","risk":"高/中/低"}}

卖家：
{samples}"""
    resp = llm(prompt)
    if not resp:
        return {"name": "未知团伙", "biz": "未知", "risk": "中"}
    try:
        j = re.search(r"\{.*\}", resp, re.S)
        if j:
            return json.loads(j.group())
    except:
        pass
    return {"name": "未知团伙", "biz": "未知", "risk": "中"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-gang", type=int, default=3)
    ap.add_argument("--llm", action="store_true")
    ap.add_argument("--llm-top", type=int, default=30)
    args = ap.parse_args()

    items = load_items(verbose=True, filter_noise=True)
    print(f"加载 {len(items)} 条商品数据\n")

    print("【第一层】构建核心团伙（同话术模板）...")
    node, core_gangs = build_core_gangs(items, args.min_gang)
    print(f"  → {len(core_gangs)} 个核心团伙 (业务单一、话术一致)")
    sizes = sorted([len(g["members"]) for g in core_gangs], reverse=True)
    print(
        f"  → 最大 {sizes[0] if sizes else 0} 人, 中位数 {sizes[len(sizes) // 2] if sizes else 0} 人\n"
    )

    print("【第二层】分析跨团伙关联（超级团伙）...")
    super_edges, super_groups = link_super_gangs(node, core_gangs)
    print(f"  → {len(super_edges)} 条跨团伙关联边")
    print(f"  → {len(super_groups)} 个超级团伙网络 (一波人做多业务)\n")

    # LLM 标注核心团伙
    llm_n = min(args.llm_top, len(core_gangs)) if args.llm else 0
    if args.llm:
        print(f"🤖 LLM 标注最大的前 {llm_n} 个核心团伙\n")
        print("=" * 60)

    gang_out = []
    for idx, g in enumerate(core_gangs):
        members = sorted(g["members"], key=lambda s: -node[s]["count"])
        areas = Counter(node[s]["area"] for s in members if node[s]["area"])
        segs = Counter()
        for s in members:
            for x in node[s]["segment"]:
                segs[x] += 1
        top_seg = segs.most_common(1)[0][0] if segs else "黑产"
        label = {
            "name": f"{top_seg}马甲群#{g['id']}",
            "biz": "（规则识别）",
            "risk": "高",
        }
        if args.llm and idx < args.llm_top:
            done = idx + 1
            bar = "█" * int(30 * done / llm_n) + "░" * (30 - int(30 * done / llm_n))
            print(
                f"  [{bar}] {done}/{llm_n} 团伙#{g['id']} ({len(members)}人)...",
                flush=True,
            )
            label = llm_gang_label(node, members)
            print(
                f"       ✓ {label['name']} | {label['risk']} | {label['biz'][:28]}",
                flush=True,
            )

        gang_out.append(
            {
                "id": g["id"],
                "name": label["name"],
                "biz": label["biz"],
                "risk": label["risk"],
                "tpl": g["tpl"],
                "members": len(members),
                "top_areas": areas.most_common(3),
                "top_segments": segs.most_common(5),
                "sellers": [
                    {
                        "seller": s,
                        "count": node[s]["count"],
                        "area": node[s]["area"],
                        "segment": list(node[s]["segment"]),
                        "image_fp": node[s]["image_fp"],
                        "sample_title": node[s]["sample_title"],
                        "sample_link": node[s]["sample_link"],
                    }
                    for s in members
                ],
            }
        )

    # 超级团伙命名（合并旗下核心团伙的业务）
    gang_by_id = {g["id"]: g for g in gang_out}
    super_out = []
    for root, gids in super_groups.items():
        biz_list = [gang_by_id[g]["name"] for g in gids if g in gang_by_id]
        total_members = sum(gang_by_id[g]["members"] for g in gids if g in gang_by_id)
        super_out.append(
            {
                "core_gangs": gids,
                "core_count": len(gids),
                "total_members": total_members,
                "businesses": biz_list[:8],
            }
        )
    super_out.sort(key=lambda x: -x["core_count"])

    result = {
        "summary": {
            "sellers": len(node),
            "core_gangs": len(core_gangs),
            "super_edges": len(super_edges),
            "super_gangs": len(super_groups),
        },
        "gangs": gang_out,
        "super_edges": super_edges,
        "super_gangs": super_out,
    }
    out = OUT_DIR / "gang_graph.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n💾 已保存: {out}")

    # 汇总：超级团伙 TOP
    print(f"\n{'=' * 60}")
    print(f"  🔗 超级团伙网络 TOP 10 (一波人做多业务)")
    print(f"{'=' * 60}")
    for i, sg in enumerate(super_out[:10], 1):
        print(f"  [{i}] {sg['core_count']} 个团伙联动 / 共 {sg['total_members']} 人")
        print(f"       业务: {' + '.join(sg['businesses'][:5])}")


if __name__ == "__main__":
    main()
