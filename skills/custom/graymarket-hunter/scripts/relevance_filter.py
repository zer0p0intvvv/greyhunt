import argparse
import json
import re

from data_loader import load_items, relevance
from gmh_paths import out_dir
from llm_client import llm

BATCH = 150

# 第3层 LLM 二分类提示。宁漏勿杀：不确定一律判 1(相关)。
_PROMPT_HEAD = (
    "你是黑灰产识别专家。下面是闲鱼商品标题列表(按编号)。判断每条是否属于"
    "【抖音/TikTok/字节系产品的黑灰产业务】：代充值、代投流(Dou+/千川)、刷量涨粉、"
    "账号交易、解封解限、数据爬取工具(蝉妈妈/灰豚等)、会员代开、起号教程、带货权限等。\n"
    "判定规则：\n"
    "- 明确属于上述黑灰产业务 → 1\n"
    "- 明确是无关实物商品(背包/手机/衣服/食品/玩具/数码配件等正常二手物品) → 0\n"
    "- 拿不准/模糊 → 1 (宁可保留)\n"
    "只输出每条的编号和判定，格式 `编号:判定`，每行一条，不要解释。\n\n"
)


def _classify_batch(batch):
    lines = [f"{i}. {it.get('title', '')[:60]}" for i, it in enumerate(batch)]
    out = llm(_PROMPT_HEAD + "\n".join(lines), max_tokens=1800)
    if not out:
        return {}
    verdict = {}
    for m in re.finditer(r"(\d+)\s*[:：]\s*([01])", out):
        verdict[int(m.group(1))] = int(m.group(2))
    return verdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="只处理前N条unknown(调试用)")
    args = ap.parse_args()

    items = load_items(verbose=True)
    unknown = [it for it in items if relevance(it) == "unknown"]
    if args.limit:
        unknown = unknown[: args.limit]
    print(f"\n待 LLM 判定的灰色样本: {len(unknown)} 条 (每批 {BATCH})")

    blacklist = []
    processed = 0
    for start in range(0, len(unknown), BATCH):
        batch = unknown[start : start + BATCH]
        verdict = _classify_batch(batch)
        for i, it in enumerate(batch):
            v = verdict.get(i, 1)
            if v == 0:
                iid = (it.get("itemId") or it.get("_dedup_key") or "").strip()
                if iid:
                    blacklist.append(iid)
        processed += len(batch)
        if processed % 300 == 0 or start + BATCH >= len(unknown):
            print(f"  进度 {processed}/{len(unknown)} | 已判无关 {len(blacklist)} 条")

    od = out_dir()
    od.mkdir(parents=True, exist_ok=True)
    bl_path = od / "relevance_blacklist.json"
    json.dump(
        {"irrelevant_item_ids": sorted(set(blacklist))},
        open(bl_path, "w", encoding="utf-8"),
        ensure_ascii=False,
    )
    print(f"\n💾 已保存无关黑名单: {bl_path}")
    print(
        f"   LLM 从 {len(unknown)} 条灰色样本中剔除 {len(set(blacklist))} 条无关 "
        f"(保留 {len(unknown) - len(set(blacklist))} 条)"
    )


if __name__ == "__main__":
    main()
