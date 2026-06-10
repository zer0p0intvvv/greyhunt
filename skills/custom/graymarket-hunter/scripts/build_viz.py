"""
把 gang_graph.json 转成可视化图谱数据，并内联进 viz_template.html 生成自包含 HTML。
双击 output/gang_viz.html 即可在浏览器看力导向图谱。

针对大规模数据（200+ 团伙 / 2万节点）做了智能采样：
  - 默认只展示 TOP N 个团伙（按人数）
  - 每个团伙最多展示 M 个代表成员（按商品数排序），避免浏览器卡死
  - 团伙节点标注真实总人数

用法:
  python3 build_viz.py                 # 默认 TOP 60 团伙，每团伙最多 25 成员
  python3 build_viz.py --top 100       # TOP 100 团伙
  python3 build_viz.py --max-member 40 # 每团伙最多 40 成员
"""

import json
import argparse
from pathlib import Path

from gmh_paths import out_dir

OUT = out_dir()
_TPL_DIR = Path(__file__).resolve().parent

parser = argparse.ArgumentParser()
parser.add_argument("--top", type=int, default=60, help="展示前 N 个团伙")
parser.add_argument("--max-member", type=int, default=25, help="每团伙最多展示成员数")
args = parser.parse_args()

src = json.loads((OUT / "gang_graph.json").read_text(encoding="utf-8"))

RISK_COLOR = {"高": "#e74c3c", "中": "#f39c12", "低": "#27ae60"}

nodes = []
links = []

all_gangs = sorted(src["gangs"], key=lambda g: -g["members"])
show_gangs = all_gangs[: args.top]

shown_members = 0
for g in show_gangs:
    gid = f"G{g['id']}"
    nodes.append(
        {
            "id": gid,
            "label": g["name"],
            "type": "gang",
            "risk": g["risk"],
            "biz": g["biz"],
            "members": g["members"],
            "areas": dict(g["top_areas"]),
            "segments": dict(g["top_segments"]),
            "size": min(8 + g["members"] ** 0.5 * 2, 55),
            "color": RISK_COLOR.get(g["risk"], "#999"),
        }
    )

    # 成员按商品数降序，取代表性的前 M 个
    members = sorted(g["sellers"], key=lambda s: -s.get("count", 0))
    shown = members[: args.max_member]
    for s in shown:
        sid = f"{gid}_{s['seller']}"
        nodes.append(
            {
                "id": sid,
                "label": s["seller"],
                "type": "seller",
                "gang": gid,
                "risk": g["risk"],
                "area": s["area"],
                "count": s["count"],
                "segment": s["segment"],
                "title": s["sample_title"],
                "link": s["sample_link"],
                "image_fp": s.get("image_fp", ""),
                "size": min(4 + s["count"] * 1.2, 14),
                "color": RISK_COLOR.get(g["risk"], "#999"),
            }
        )
        links.append({"source": gid, "target": sid, "kind": "member"})
        shown_members += 1

    # 若有未展示成员，加一个"+N更多"提示节点
    hidden = len(members) - len(shown)
    if hidden > 0:
        mid = f"{gid}_more"
        nodes.append(
            {
                "id": mid,
                "label": f"+{hidden}人",
                "type": "more",
                "gang": gid,
                "risk": g["risk"],
                "size": 6,
                "color": "#555",
            }
        )
        links.append({"source": gid, "target": mid, "kind": "more"})

# 跨团伙：同 image_fp 的卖家连虚线（潜在更大团伙线索）
fp_map = {}
for n in nodes:
    if n["type"] == "seller" and n.get("image_fp"):
        fp_map.setdefault(n["image_fp"], []).append(n["id"])
samefp_links = 0
for fp, ids in fp_map.items():
    if len(ids) > 1 and len(ids) <= 20:  # 太大的同图桶不连（避免视觉爆炸）
        for i in range(1, len(ids)):
            links.append({"source": ids[0], "target": ids[i], "kind": "samefp"})
            samefp_links += 1

graph = {
    "summary": {
        **src["summary"],
        "shown_gangs": len(show_gangs),
        "shown_members": shown_members,
    },
    "nodes": nodes,
    "links": links,
}

tpl = (_TPL_DIR / "viz_template.html").read_text(encoding="utf-8")
html = tpl.replace("/*__GRAPH_DATA__*/", json.dumps(graph, ensure_ascii=False))
out_html = OUT / "gang_viz.html"
out_html.write_text(html, encoding="utf-8")

print(f"全部 {len(all_gangs)} 个团伙 → 展示 TOP {len(show_gangs)} 个")
print(
    f"节点 {len(nodes)} 个 (团伙 {len(show_gangs)} + 卖家 {shown_members} + 提示节点)"
)
print(f"连线 {len(links)} 条 (含同图关联 {samefp_links} 条)")
print(f"✅ 已生成: {out_html}")
