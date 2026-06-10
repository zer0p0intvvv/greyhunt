import json
import re
import os
from pathlib import Path

from gmh_paths import data_dir, data_glob, out_dir

_BOOK_PAT = re.compile(
    r"正版|图书|书店|书屋|书铺|书城|出版社|未拆封|纸质书|教材|主编|著，|ISBN|"
    r"全新正版|包邮正版|书一本|册）|册\)|二手书|旧书|考研|课本"
)

# ============================================================================
# 三层漏斗相关性过滤 (规则 + LLM)
# 闲鱼搜索是模糊匹配，搜"抖币/皮皮虾"会带出大量字面误匹配的实物商品。
# 第1层 正向词：明确黑产意图 → 直接判定相关 (不送 LLM)
# 第2层 负向词：明确实物商品 → 直接判定无关 (剔除)
# 第3层 LLM：两层都没命中的灰色地带 → LLM 二分类 (宁漏勿杀)
# ============================================================================

# 第1层 · 强黑产正向词：标题命中即判定为相关业务，强保留
_GANG_POS_PAT = re.compile(
    r"代充|代投|代刷|代付|代开|代练|代拍|代运营|代发|秒到|秒发|直充|自动发货|自助下单|"
    r"卡密|卡号|激活码|兑换码|出黑|解封|解限|养号|起号|涨粉|涨赞|刷量|刷粉|刷赞|刷播放|"
    r"权限|开通|投流|投放|引流|上热门|上热搜|冲榜|占位|加热|曝光|流量|播放量|"
    r"会员|svip|vip|月卡|周卡|日卡|年卡|账号|共享号|一手货源|货源|接单|批发价|"
    r"星图|千川|巨量|蝉妈妈|飞瓜|灰豚|考古加|抖查查|新榜|达多多|数据查询|数据工具|"
    r"抖币|dy币|dou币|音浪|钻石充值|金币充值|嘉年华|装扮|"
    r"投诉|限流|封禁|解除|申诉|防封|"
    r"教程|课程|陪跑|全套|玩法|打法|搬运|带货|矩阵|私域",
    re.IGNORECASE,
)

# 第2层 · 实物商品负向词：标题/卖家命中即判定为无关实物，剔除
# (这些是模糊搜索误带出来的真实物品：食品/玩具/服饰/数码配件/工艺品/卡牌)
_PHYSICAL_NEG_PAT = re.compile(
    r"包活|活苗|鹅苗|鸭苗|鸡苗|疫苗齐全|放养|斤左右|一箱|一斤|白菜价|海鲜|生鲜|水果|"
    r"雪糕|可乐|食玩|零食|拼豆|挂件|挂饰|收纳包|化妆包|手机链|钥匙扣|"
    r"洞洞鞋|球鞋|衣服|外套|裤子|卫衣|t恤|连衣裙|码|尺码|"
    r"电钻|电池外壳|配件|数据线|充电器|手机壳|钢化膜|"
    r"模型|摆件|工艺品|手办|卡套|卡牌|拆卡|set|迷宫卡|"
    r"成色如图|尺寸如图|售出不退|不退不换|所见即所得|快递|包邮包活",
    re.IGNORECASE,
)


def is_noise(it):
    title = it.get("title", "")
    seller = it.get("seller", "")
    # 原有：图书/教程类硬噪音
    if _BOOK_PAT.search(title) or _BOOK_PAT.search(seller):
        return True
    if re.search(r"图书|书店|书屋|书铺|图书店|书行", seller):
        return True
    return False


def relevance(it):
    title = it.get("title", "") or ""
    # 第1层优先：黑产正向词命中 → 相关 (即使也含实物词，黑产意图优先)
    if _GANG_POS_PAT.search(title):
        return "relevant"
    # 第2层：实物商品负向词命中 → 无关
    if _PHYSICAL_NEG_PAT.search(title):
        return "irrelevant"
    # 第3层交给 LLM
    return "unknown"


def _dedup_key(it):
    iid = (it.get("itemId") or "").strip()
    if iid:
        return f"id:{iid}"
    link = it.get("link") or ""
    m = re.search(r"id=(\d+)", link)
    if m:
        return f"id:{m.group(1)}"
    seller = (it.get("seller") or "").strip()
    title = (it.get("title") or "").strip()
    return f"st:{seller}|{title}"


def _load_blacklist():
    bl_path = out_dir() / "relevance_blacklist.json"
    if not bl_path.exists():
        return set()
    try:
        d = json.load(open(bl_path, encoding="utf-8"))
        return set(d.get("irrelevant_item_ids", []))
    except Exception:
        return set()


def _checkpoint_path():
    return out_dir() / ".dedup_checkpoint.json"


def _load_checkpoint():
    cp = _checkpoint_path()
    if not cp.exists():
        return {}, set()
    d = json.loads(cp.read_text(encoding="utf-8"))
    return d.get("items", {}), set(d.get("seen_files", []))


def _save_checkpoint(items_dict, seen_files):
    cp = _checkpoint_path()
    cp.parent.mkdir(parents=True, exist_ok=True)
    serializable = {}
    for k, v in items_dict.items():
        v2 = dict(v)
        for sk in ("_keywords", "_sources"):
            if isinstance(v2.get(sk), set):
                v2[sk] = sorted(v2[sk])
        serializable[k] = v2
    json.dump(
        {
            "items": serializable,
            "seen_files": sorted(seen_files),
            "count": len(serializable),
        },
        open(cp, "w", encoding="utf-8"),
        ensure_ascii=False,
    )


def load_items(
    verbose=True, filter_noise=True, filter_relevance=True, incremental=False
):
    dd = data_dir()
    files = sorted(str(p) for p in dd.glob(data_glob()))
    search_files = [f for f in files if "_detail_" not in f]

    dedup = {}
    raw_count = 0
    file_count = 0
    new_file_count = 0
    seen_files = set()

    if incremental:
        dedup, seen_files = _load_checkpoint()
        if verbose:
            print(
                f"📂 增量模式：已有 {len(dedup)} 条缓存，{len(seen_files)} 个已处理文件"
            )

    for f in search_files:
        fname = Path(f).name
        if fname in seen_files:
            continue
        new_file_count += 1
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            if verbose:
                print(f"⚠️ 读取失败: {Path(f).name} - {e}")
            continue
        file_count += 1
        seen_files.add(fname)
        kw = d.get("keyword", Path(f).stem)
        for it in d.get("items", []):
            raw_count += 1
            k = _dedup_key(it)
            if k in dedup:
                existing = dedup[k]
                existing.setdefault("_keywords", set()).add(kw)
                existing.setdefault("_sources", set()).add(fname)
            else:
                it = dict(it)
                it["_keywords"] = {kw}
                it["_sources"] = {fname}
                it["_dedup_key"] = k
                dedup[k] = it

    if incremental and new_file_count > 0:
        items_dict = {
            it.get("_dedup_key", f"idx:{i}"): it for i, it in enumerate(items)
        }
        _save_checkpoint(items_dict, seen_files)
        if verbose:
            print(
                f"   💾 增量保存：+{new_file_count} 新文件 → checkpoint {len(items)} 条"
            )

    items = list(dedup.values())

    noise_removed = 0
    if filter_noise and (not incremental or new_file_count > 0):
        kept = [it for it in items if not is_noise(it)]
        noise_removed = len(items) - len(kept)
        items = kept

    rel_removed = 0
    if filter_relevance and (not incremental or new_file_count > 0):
        blacklist = _load_blacklist()
        kept = []
        for it in items:
            verdict = relevance(it)
            if verdict == "relevant":
                kept.append(it)
            elif verdict == "irrelevant":
                continue
            else:
                iid = (it.get("itemId") or "").strip()
                if iid and iid in blacklist:
                    continue
                kept.append(it)
        rel_removed = len(items) - len(kept)
        items = kept

    for it in items:
        it["_keywords"] = sorted(it["_keywords"])
        it["_sources"] = sorted(it["_sources"])

    if not incremental:
        items_dict = {
            it.get("_dedup_key", f"idx:{i}"): it for i, it in enumerate(items)
        }
        _save_checkpoint(items_dict, seen_files)
        if verbose:
            print(f"   💾 checkpoint 已保存 ({len(items)} 条)，后续可用 --incremental")

    if verbose:
        mode = "增量" if incremental else "全量"
        print(f"📂 数据目录: {dd}")
        if incremental and new_file_count == 0:
            print(f"📂 [{mode}] 无新文件，复用 {len(items)} 条缓存数据")
        elif incremental:
            print(f"📂 [{mode}] 加载 {file_count} 个文件 (新增 {new_file_count} 个)")
            print(f"   新增 {raw_count} 条 → 去重后共 {len(items)} 条")
        else:
            dup_removed = raw_count - len(dedup)
            print(f"📂 加载 {file_count} 个文件")
            print(
                f"   原始 {raw_count} 条 → 去重后 {len(dedup)} 条 (移除重复 {dup_removed} 条, {dup_removed / max(raw_count, 1) * 100:.1f}%)"
            )
        if filter_noise:
            print(f"   过滤图书/教程噪音 {noise_removed} 条")
        if filter_relevance:
            print(f"   三层漏斗剔除无关商品 {rel_removed} 条")
        print(f"   → 最终相关黑产数据 {len(items)} 条")

    return items


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--incremental", action="store_true", help="仅处理新文件，复用上次去重结果"
    )
    ap.add_argument("--reset", action="store_true", help="重置增量缓存，强制全量")
    args = ap.parse_args()
    if args.reset and _checkpoint_path().exists():
        _checkpoint_path().unlink()
        print("🗑️ 已重置增量缓存")
    items = load_items(incremental=args.incremental)
    multi = sorted(items, key=lambda x: -len(x["_keywords"]))
    print(f"\n🔝 被最多关键词同时命中的商品 (TOP 10)：")
    for it in multi[:10]:
        print(
            f"  [{len(it['_keywords'])}词] {it.get('seller', '?')} | {it.get('title', '')[:40]}"
        )
        print(f"        命中: {', '.join(it['_keywords'][:8])}")
