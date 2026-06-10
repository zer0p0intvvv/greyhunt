"use client";

import {
  Database, ScanEye, Filter, ShieldCheck, TrendingUp, Zap,
  Rocket, Search, Fingerprint, Bolt, RefreshCw, Cpu,
} from "lucide-react";
import { NumberTicker } from "@/components/ui/number-ticker";
import { Section } from "@/components/landing/section";
import SpotlightCard from "@/components/ui/spotlight-card";

const metrics = [
  { icon: Database, value: 138051, unit: "条", label: "原始数据采集", detail: "4轮飞轮·446个关键词·15页深爬·覆盖20条字节产品线", color: "from-blue-500 to-cyan-400", iconBg: "bg-blue-500/10" },
  { icon: Filter, value: 48026, unit: "条重复", label: "跨关键词去重", detail: "34.8%去重率·itemId精确去重·增量缓存秒级加载", color: "from-slate-400 to-gray-300", iconBg: "bg-slate-500/10" },
  { icon: Search, value: 18470, unit: "条噪音", label: "三层漏斗剔除", detail: "规则正向/负向词 75%零Token·LLM仅处理灰色地带", color: "from-amber-500 to-yellow-400", iconBg: "bg-amber-500/10" },
  { icon: ShieldCheck, value: 71794, unit: "条", label: "高质量黑产数据", detail: "去重·去噪·相关性过滤·数据质量提升3倍", color: "from-emerald-500 to-green-400", iconBg: "bg-emerald-500/10" },
  { icon: ScanEye, value: 514, unit: "个", label: "核心马甲团伙", detail: "话术模板指纹聚类·每个团伙业务纯净·可审计可解释", color: "from-red-500 to-rose-400", iconBg: "bg-red-500/10" },
  { icon: TrendingUp, value: 20, unit: "个", label: "超级团伙网络", detail: "union-find交叉关联·#1=18团579人·#2=16团199人", color: "from-purple-500 to-pink-400", iconBg: "bg-purple-500/10" },
  { icon: Zap, value: 89, unit: "个", label: "LLM挖掘黑话变体", detail: "同音/拆字/缩写/emoji·4轮飞轮持续回灌爬虫", color: "from-orange-500 to-red-400", iconBg: "bg-orange-500/10" },
  { icon: Rocket, value: 446, unit: "个", label: "关键词覆盖", detail: "20条产品线·代充/代投/刷量/账号/解封/数据/公会", color: "from-indigo-500 to-violet-400", iconBg: "bg-indigo-500/10" },
  { icon: Bolt, value: 4, unit: "轮", label: "飞轮自我强化", detail: "增量加载·自动回流·每轮新数据→新黑话→自动回灌", color: "from-cyan-500 to-teal-400", iconBg: "bg-cyan-500/10" },
];

export function MetricsSection({ className }: { className?: string }) {
  return (
    <Section className={className} title="数据全貌" subtitle="从零爬取到团伙挖掘·端到端闭环·4轮飞轮自我强化">
      <div className="container-md mt-10 grid grid-cols-1 gap-4 px-4 md:grid-cols-2 md:gap-6 lg:grid-cols-3">
        {metrics.map((m) => (
          <SpotlightCard key={m.label} spotlightColor="rgba(239, 68, 68, 0.18)" className="group relative overflow-hidden rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm transition-all duration-300 hover:border-white/20">
            <div className="flex items-start justify-between">
              <div className={`rounded-lg ${m.iconBg} p-2.5`}>
                <m.icon className="size-5 text-white/80" />
              </div>
              <span className={`bg-gradient-to-r ${m.color} bg-clip-text text-4xl font-bold tabular-nums text-transparent`}>
                <NumberTicker value={m.value} className="text-inherit" />
                <span className="ml-1 text-lg">{m.unit}</span>
              </span>
            </div>
            <div className="mt-3">
              <h3 className="text-sm font-semibold text-white">{m.label}</h3>
              <p className="mt-1 text-xs text-white/50">{m.detail}</p>
            </div>
          </SpotlightCard>
        ))}
      </div>
    </Section>
  );
}