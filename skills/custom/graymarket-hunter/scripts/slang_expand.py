"""
暗语黑话发现 & 词库自演进
用法: python3 slang_expand.py --mine (规则挖掘) | --llm (LLM扩展)
"""

import json, re, argparse, os
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

from gmh_paths import data_dir, out_dir, data_glob

DATA_DIR = data_dir()
OUT_DIR = out_dir()

from llm_client import llm


def load_titles():
    from data_loader import load_items

    return [it.get("title", "") for it in load_items(verbose=False)]


def rule_mine(titles, min_freq=3):
    nc = Counter()
    for t in titles:
        text = re.sub(r"[，。！？；：、\s△№▲★●◆■▶▼▽☆★*]", "", t)
        for n in (2, 3, 4):
            for i in range(len(text) - n + 1):
                ng = text[i : i + n]
                if re.search(r"[\u4e00-\u9fff]", ng):
                    nc[ng] += 1
    stop = {
        "服务",
        "商品",
        "下单",
        "咨询",
        "价格",
        "充值",
        "商家",
        "官方",
        "正版",
        "直充",
        "快充",
        "秒到",
        "到账",
        "自动",
        "发货",
        "联系",
        "备注",
        "注意",
        "说明",
        "介绍",
        "详情",
        "点击",
        "购买",
        "套餐",
        "产品",
        "提供",
        "支持",
        "使用",
        "需要",
        "通知",
        "闲鱼",
        "认证",
        "放心",
        "平台",
        "信息",
        "闲置",
        "全新",
    }
    cand = [
        (ng, c)
        for ng, c in nc.items()
        if c >= min_freq and ng not in stop and not re.match(r"^[\d.]+$", ng)
    ]
    cand.sort(key=lambda x: -x[1])
    print(f"  高频片段(>={min_freq}次): {len(cand)}个")
    cls = defaultdict(list)
    for ng, c in cand[:200]:
        cls[ng[:2]].append(ng)
    var = {p: list(set(vs)) for p, vs in cls.items() if len(set(vs)) >= 3}
    print(f"  变体簇(>=3): {len(var)}个")
    return cand, var


def llm_expand(seeds, titles):
    ctx = []
    for t in titles[:15]:
        for s in seeds:
            i = t.lower().find(s.lower())
            if i >= 0:
                start = max(0, i - 15)
                end = min(len(t), i + len(s) + 30)
                ctx.append(f"* {t[start:end]}")
                break
    ctxt = "\n".join(ctx[:10])
    prompt = f"""你是安全分析师，追踪闲鱼黑灰产黑话。
这些词指向同一类服务: {", ".join(seeds)}
上下文:
{ctxt}
请找其他同义变体（拆字/谐音/英文/缩写/加符号等），每行一个词，5-15个，不要解释。"""
    r = llm(prompt)
    if not r:
        return []
    words = []
    for line in r.strip().split("\n"):
        w = line.strip().strip("-*.,;: ")
        w = re.sub(r"^\d+\.\s*", "", w)
        if w and len(w) <= 15 and w not in seeds:
            words.append(w)
    return words


def _auto_append_to_keywords(all_exp):
    """将新黑话追加到 keywords_byte.txt，实现飞轮自动回流"""
    from pathlib import Path

    kw_file = Path(
        os.environ.get(
            "GMH_KW_FILE",
            str(Path(os.environ.get("GMH_DATA_DIR", ".")) / "../keywords_byte.txt"),
        )
    )
    if not kw_file.exists():
        kw_file = Path("/mnt/xianyu-spider/keywords_byte.txt")
    if not kw_file.exists():
        print("[飞轮] 未找到 keywords_byte.txt，跳过自动追加")
        return

    existing = set(
        l.strip() for l in open(kw_file) if l.strip() and not l.startswith("#")
    )
    new_words = []
    for cat, v in all_exp.items():
        seeds = set(v.get("seeds", []))
        for w in v.get("expanded", []):
            if w and w not in seeds and w not in existing:
                new_words.append(w)
                existing.add(w)

    if not new_words:
        print("[飞轮] 无新词可追加")
        return

    import shutil

    bak = kw_file.with_suffix(
        kw_file.suffix + f".bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    shutil.copy(kw_file, bak)

    with open(kw_file, "a") as f:
        f.write(f"\n# ── 飞轮自动追加 {datetime.now().strftime('%Y-%m-%d %H:%M')} ──\n")
        for w in new_words:
            f.write(w + "\n")

    print(f"[飞轮] ✅ 已追加 {len(new_words)} 个新词到 {kw_file} (备份: {bak.name})")
    print(f"   {', '.join(new_words[:10])}{'...' if len(new_words) > 10 else ''}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mine", action="store_true")
    p.add_argument("--llm", action="store_true")
    p.add_argument("--seeds", default="")
    p.add_argument(
        "--auto-append",
        action="store_true",
        help="自动将新黑话追加到 keywords_byte.txt，实现飞轮闭环",
    )
    a = p.parse_args()
    titles = load_titles()
    print(f"加载 {len(titles)} 条标题")

    seeds_list = [
        ["dou+", "豆荚", "抖加", "抖+"],
        ["抖币", "钻石"],
        ["灰豚", "蝉妈妈", "考古加", "抖查查"],
        ["起号", "涨粉", "上热门"],
    ]
    if a.seeds:
        seeds_list = [[s.strip() for s in a.seeds.split(",")]]
    all_exp = {}

    if a.llm:
        print("\n=== LLM 暗语扩展 ===")
        for seeds in seeds_list:
            print(f"\n  种子: {seeds}")
            ex = llm_expand(seeds, titles)
            all_exp[seeds[0]] = {"seeds": seeds, "expanded": ex}
            print(f"   -> {ex}")
        (OUT_DIR / "slang_expanded.json").write_text(
            json.dumps(all_exp, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    if a.mine:
        print("\n=== 规则挖掘 ===")
        cand, var = rule_mine(titles)
        for ng, c in cand[:50]:
            print(f"  {ng}: {c}次")
        for pr, vs in list(var.items())[:10]:
            print(f"  [{pr}] -> {vs}")

    (OUT_DIR / "slang_db.json").write_text(
        json.dumps(
            {
                "seeds": sum(seeds_list, []),
                "llm_expanded": all_exp,
                "updated_at": datetime.now().isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("\nDone.")

    if a.auto_append and all_exp:
        _auto_append_to_keywords(all_exp)


if __name__ == "__main__":
    main()
