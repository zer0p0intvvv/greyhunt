"use client";

import { Zap, Layers, BarChart3, Cpu, TrendingDown, ArrowRight, RefreshCw, Bolt } from "lucide-react";
import { Section } from "@/components/landing/section";

export function LLMSection({ className }: { className?: string }) {
  return (
    <Section className={className} title="工程优化" subtitle="LLM Token 极限压缩 + 增量计算 + 自动飞轮回流">
      <div className="container-md mt-10 px-4">

        <div className="mx-auto grid max-w-5xl grid-cols-1 gap-6 md:grid-cols-3">
          <StrategyCard
            icon={Layers}
            title="三层漏斗"
            desc="第1层正向词强保留、第2层负向词剔除——75%数据零Token规则层判定，只有25%进入LLM。批量150条/次，调用压缩99.8%"
            stat="节省 99%+ Token"
            color="emerald"
          />
          <StrategyCard
            icon={RefreshCw}
            title="增量加载"
            desc="首次全量存checkpoint（83MB），后续仅处理新增文件。375文件→0-5新文件，加载从5秒→秒过，IO减少98%"
            stat="IO 减少 98%"
            color="purple"
          />
          <StrategyCard
            icon={Bolt}
            title="飞轮自动回流"
            desc="slang_expand --auto-append 挖出新黑话后自动追加到关键词库，自动备份去重。agent下次爬全程无人介入"
            stat="飞轮 全自动"
            color="amber"
          />
        </div>

        <div className="mx-auto mt-12 max-w-4xl rounded-2xl border border-white/10 bg-black/30 p-8 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-3 md:flex-row md:justify-center md:gap-6">
            <FlowNode value="138K" label="原始数据" />
            <ArrowRight className="size-5 text-white/30 shrink-0 rotate-90 md:rotate-0" />
            <FlowNode value="90K" label="去重" sub="itemId · 34.8%" />
            <ArrowRight className="size-5 text-white/30 shrink-0 rotate-90 md:rotate-0" />
            <FlowNode value="71.8K" label="三层漏斗" sub="规则75% + LLM25%" color="emerald" />
            <ArrowRight className="size-5 text-white/30 shrink-0 rotate-90 md:rotate-0" />
            <FlowNode value="514团" label="团伙检测" sub="20超级团伙" color="purple" />
          </div>

          <div className="mt-6 grid grid-cols-4 gap-4 text-center">
            {[
              { label: "增量加载", value: "秒过", color: "text-purple-400" },
              { label: "Token成本", value: "<$0.30", color: "text-emerald-400" },
              { label: "飞轮回流", value: "全自动", color: "text-amber-400" },
              { label: "总处理时间", value: "<3min", color: "text-blue-400" },
            ].map((s) => (
              <div key={s.label} className="rounded-lg border border-white/5 bg-white/5 p-3">
                <div className={`text-lg font-bold ${s.color}`}>{s.value}</div>
                <div className="text-[11px] text-white/40">{s.label}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="mx-auto mt-8 max-w-3xl rounded-xl border border-white/10 bg-black/20 p-6 text-center backdrop-blur-sm">
          <div className="flex items-center justify-center gap-2 text-sm text-white/40">
            <Cpu className="size-4" />
            若不使用三层漏斗+增量加载+自动回流，每次分析需全量加载375文件·逐条LLM判定$15-30·人工写词库
            <ArrowRight className="size-3" />
          </div>
          <div className="mt-2 text-xl font-bold text-emerald-400">
            实际消耗 &lt;$0.30 · IO减少98% · 飞轮全自动
          </div>
        </div>
      </div>
    </Section>
  );
}

function FlowNode({ value, label, sub, color = "white" }: { value: string; label: string; sub?: string; color?: string }) {
  return (
    <div className={`flex flex-col items-center rounded-xl border px-5 py-3 text-center backdrop-blur-sm ${
      color === "emerald" ? "border-emerald-500/30 bg-emerald-500/5" : color === "purple" ? "border-purple-500/30 bg-purple-500/5" : "border-white/10 bg-white/5"
    }`}>
      <span className={`text-2xl font-bold ${color === "emerald" ? "text-emerald-400" : color === "purple" ? "text-purple-400" : "text-white"}`}>{value}</span>
      <span className="text-xs text-white/60">{label}</span>
      {sub && <span className="text-[10px] text-white/30 mt-0.5">{sub}</span>}
    </div>
  );
}

function StrategyCard({ icon: Icon, title, desc, stat, color }: { icon: React.ComponentType<{ className?: string }>; title: string; desc: string; stat: string; color: string }) {
  const colors: Record<string, string> = { emerald: "border-emerald-500/20 bg-emerald-500/5", purple: "border-purple-500/20 bg-purple-500/5", amber: "border-amber-500/20 bg-amber-500/5" };
  return (
    <div className={`rounded-xl border ${colors[color] || "border-white/10 bg-white/5"} p-6 backdrop-blur-sm`}>
      <div className={`mb-3 rounded-lg ${color === "emerald" ? "bg-emerald-500/10" : color === "purple" ? "bg-purple-500/10" : "bg-amber-500/10"} w-fit p-2`}>
        <Icon className="size-5 text-white/70" />
      </div>
      <h3 className="text-base font-semibold text-white">{title}</h3>
      <p className="mt-2 text-xs leading-relaxed text-white/50">{desc}</p>
      <span className={`mt-3 inline-block rounded-full border px-3 py-1 text-xs font-bold ${color === "emerald" ? "border-emerald-500/30 text-emerald-400" : color === "purple" ? "border-purple-500/30 text-purple-400" : "border-amber-500/30 text-amber-400"}`}>{stat}</span>
    </div>
  );
}