"use client";

import { TrendingUp, ArrowUpRight, Hash, Zap } from "lucide-react";
import { Section } from "@/components/landing/section";

const rounds = [
  { round: "初始", raw: "55K", gangs: 312, supers: 11, topGang: "11团/403人", method: "228词·1页浅爬" },
  { round: "飞轮1", raw: "76K", gangs: 314, supers: 11, topGang: "18团/565人", method: "LLM掘51黑话·头号暴增7团162人" },
  { round: "飞轮2", raw: "87K", gangs: 391, supers: 15, topGang: "18团/571人", method: "二次掘38黑话·核心+77·超级+4" },
  { round: "飞轮3", raw: "138K", gangs: 514, supers: 20, topGang: "18团/579人", method: "135新词扩20条产品线·超级+5·核心+123" },
];

const kwShowcase = [
  { cat: "抖音代充", words: "抖币充值 · 钻石直充 · DB · 抖B · dy充值 · 音浪币 · 💎" },
  { cat: "Dou+投流", words: "豆荚 · Dou+ · 抖加 · D+投放 · 痘加 · 抖➕ · Doujia · D加" },
  { cat: "数据工具", words: "蝉妈妈 · 灰豚 · 考古加 · 飞瓜 · 星图 · 千川 · kaogujia · chanmama" },
  { cat: "直播/公会", words: "直播人气 · 挂铁 · 弹幕机器人 · TK公会 · 抖音MCN · 无人直播" },
  { cat: "账号/解封", words: "号交易 · 白号 · 实名 · 改实名 · 申诉 · 限流解除 · 蓝V" },
  { cat: "新业务线", words: "飞书企业号 · 即梦AI · 穿山甲 · 西瓜视频 · 番茄小说 · 火山引擎" },
];

export function FlywheelSection({ className }: { className?: string }) {
  return (
    <Section className={className} title="飞轮增长全景" subtitle="4轮自我强化·55K→138K原始·312→514核心团伙·增量加载+自动回流">
      <div className="container-md mt-10 px-4">
        <div className="mx-auto max-w-4xl overflow-x-auto">
          <div className="flex min-w-[640px] items-start gap-2 md:gap-3">
            {rounds.map((r, i) => (
              <div key={r.round} className="flex items-start gap-2 md:gap-3">
                <div className={`flex w-32 shrink-0 flex-col rounded-xl border p-3 md:w-36 md:p-4 ${
                  i === 3 ? "border-white/20 bg-white/10 shadow-lg shadow-white/5" : "border-white/10 bg-white/5"
                }`}>
                  <span className={`rounded-full w-fit px-2 py-0.5 text-[10px] font-bold ${
                    i === 0 ? "bg-slate-500/20 text-slate-400" : i === 3 ? "bg-green-500/20 text-green-400" : "bg-amber-500/20 text-amber-400"
                  }`}>{r.round}</span>
                  <div className="mt-2 space-y-1">
                    <StatRow label="原始" value={r.raw} />
                    <StatRow label="团伙" value={r.gangs} highlight={i === 3} />
                    <StatRow label="超级" value={r.supers} />
                  </div>
                  <div className="mt-2 rounded-lg bg-white/5 p-1.5 text-center">
                    <span className="text-[10px] font-semibold text-red-400">{r.topGang}</span>
                  </div>
                </div>
                {i < rounds.length - 1 && (
                  <div className="flex items-center pt-10">
                    <ArrowUpRight className="size-4 text-green-500/50" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="mx-auto mt-8 max-w-4xl rounded-xl border border-white/10 bg-black/20 p-6">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-white/40 flex items-center gap-1">
              <TrendingUp className="size-3" /> 团伙增长曲线
            </span>
            <span className="text-xs text-white/30">312 → 314 → 391 → 514</span>
          </div>
          <BarRow label="核心团伙" values={[312, 314, 391, 514]} max={514} color="from-red-500 to-rose-500" />
          <BarRow label="超级团伙" values={[11, 11, 15, 20]} max={20} color="from-purple-500 to-pink-500" />
          <BarRow label="头号规模" values={[403, 565, 571, 579]} max={579} color="from-amber-500 to-yellow-500" />
        </div>

        <div className="mx-auto mt-10 max-w-4xl">
          <h3 className="mb-4 text-center text-sm font-semibold text-white/50 flex items-center justify-center gap-2">
            <Hash className="size-3" /> 关键词集群 (446词·20条产品线)
          </h3>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
            {kwShowcase.map((k) => (
              <div key={k.cat} className="rounded-xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm hover:border-white/20 transition-all">
                <div className="mb-2 text-xs font-bold text-white/70">{k.cat}</div>
                <div className="text-[11px] leading-relaxed text-white/40 break-all">{k.words}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
          {["Playwright扫码", "15页深爬", "两层团伙模型", "union-find", "话术指纹", "LLM黑话", "规则+AI过滤", "飞轮闭环"].map((t) => (
            <span key={t} className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/50">{t}</span>
          ))}
        </div>
      </div>
    </Section>
  );
}

function StatRow({ label, value, highlight }: { label: string; value: string | number; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between text-[11px]">
      <span className="text-white/40">{label}</span>
      <span className={highlight ? "font-bold text-white" : "text-white/70"}>{value}</span>
    </div>
  );
}

function BarRow({ label, values, max, color }: { label: string; values: number[]; max: number; color: string }) {
  const labels = ["初始", "飞轮1", "飞轮2", "飞轮3"];
  return (
    <div className="mt-3">
      <div className="mb-1 flex items-center justify-between text-[10px]">
        <span className="text-white/40">{label}</span>
        <span className="text-white/30">{labels.map((l, i) => `${l} ${values[i]}`).join(" → ")}</span>
      </div>
      <div className="flex h-2 gap-0.5">
        {values.map((v, i) => (
          <div key={i} className={`h-full rounded-sm bg-gradient-to-r ${color}`} style={{ width: `${(v / max) * 100}%` }} />
        ))}
      </div>
    </div>
  );
}