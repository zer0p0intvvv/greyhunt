"use client";

import { AlertTriangle, Shield, Users, Zap, ExternalLink, Eye } from "lucide-react";
import Link from "next/link";
import { Section } from "@/components/landing/section";
import { Button } from "@/components/ui/button";

const highlights = [
  {
    icon: AlertTriangle,
    title: "头号超级团伙",
    value: "18个团伙 · 579人",
    desc: "Dou+代投 × 带货权限 · 跨业务线联合作案 · 一波人做多业务的教科书级案例",
    badge: "🔴 高危",
    badgeColor: "bg-red-500/10 text-red-400 border-red-500/20",
  },
  {
    icon: Shield,
    title: "业务线覆盖",
    value: "20条字节产品线",
    desc: "抖音/TikTok/头条/西瓜/飞书/剪映/番茄/懂车帝/皮皮虾/图虫/轻颜/火山/即梦/豆包/星图/千川/穿山甲/巨量",
    badge: "📊 广度",
    badgeColor: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  },
  {
    icon: Users,
    title: "核心团伙",
    value: "514个",
    desc: "话术模板指纹聚类 · 不做BFS链式膨胀 · 每个团伙业务纯净 · 可审计可解释 · 312→383→514持续增长",
    badge: "🎯 精准",
    badgeColor: "bg-green-500/10 text-green-400 border-green-500/20",
  },
  {
    icon: Zap,
    title: "飞轮增长",
    value: "3轮 · +176人",
    desc: "每轮新数据→新黑话→新词→回灌爬虫·头号超级团伙403→565→572→579人持续扩张",
    badge: "🔄 增长",
    badgeColor: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  },
];

export function GangSection({ className }: { className?: string }) {
  return (
    <Section
      className={className}
      title="团伙挖掘亮点"
      subtitle="两层团伙模型 · 超级团伙网络 · 3轮飞轮持续扩展"
    >
      <div className="container-md mt-10 px-4">
        <div className="mx-auto max-w-3xl rounded-2xl border border-white/10 bg-gradient-to-br from-red-950/20 to-black/40 p-8 backdrop-blur-sm">
          <div className="mb-6 text-center">
            <span className="rounded-full border border-red-500/30 bg-red-500/10 px-3 py-1 text-xs text-red-400">
              超级团伙网络 TOP 3
            </span>
          </div>

          <div className="flex flex-col items-center gap-6">
            <div className="flex flex-wrap items-center justify-center gap-4">
              <div className="rounded-2xl border-2 border-red-500/40 bg-red-500/10 px-8 py-4 text-center">
                <div className="text-3xl font-bold text-red-400">18团</div>
                <div className="text-lg font-semibold text-white">579人</div>
                <div className="mt-1 text-xs text-red-300/70">Dou+ · 带货</div>
              </div>
              <div className="rounded-2xl border-2 border-purple-500/30 bg-purple-500/10 px-6 py-3 text-center">
                <div className="text-2xl font-bold text-purple-400">16团</div>
                <div className="text-base font-semibold text-white">199人</div>
                <div className="mt-1 text-xs text-purple-300/70">代拍 · 剪映</div>
              </div>
              <div className="rounded-2xl border-2 border-blue-500/30 bg-blue-500/10 px-6 py-3 text-center">
                <div className="text-2xl font-bold text-blue-400">4团</div>
                <div className="text-base font-semibold text-white">123人</div>
                <div className="mt-1 text-xs text-blue-300/70">数据 · 曝光</div>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap justify-center gap-3">
              {[
                { gangs: 8, people: 92, biz: "充值" },
                { gangs: 5, people: 36, biz: "会员服务" },
                { gangs: 4, people: 46, biz: "数据 · 千川" },
                { gangs: 4, people: 24, biz: "会员 · 剪映" },
                { gangs: 3, people: 28, biz: "推广" },
                { gangs: 3, people: 30, biz: "会员" },
              ].map((g, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-center"
                >
                  <div className="font-bold text-white">
                    {g.gangs}团/{g.people}人
                  </div>
                  <div className="text-xs text-white/40">{g.biz}</div>
                </div>
              ))}
            </div>

            <p className="max-w-lg text-center text-sm text-white/40 leading-relaxed">
              通过共享卖家 + 同图 + 同话术模板交叉关联，
              把多个表面独立的业务团伙连成一张"一波人做多业务"的超级网络
            </p>
          </div>
        </div>

        <div className="mt-8 flex justify-center">
          <Link href="/gang-viz.html" target="_blank">
            <Button variant="outline" size="lg" className="gap-2 border-white/20 text-white/80 hover:bg-white/10">
              <Eye className="size-4" />
              查看完整交互式团伙图谱 (514团伙·1464节点·1373连线)
              <ExternalLink className="size-3" />
            </Button>
          </Link>
        </div>

        <div className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {highlights.map((h) => (
            <div
              key={h.title}
              className="group rounded-xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm transition-all hover:border-white/20 hover:bg-white/8"
            >
              <div className="flex items-center justify-between">
                <div className="rounded-lg bg-white/5 p-2">
                  <h.icon className="size-4 text-white/60" />
                </div>
                <span
                  className={`rounded-full border px-2 py-0.5 text-[10px] ${h.badgeColor}`}
                >
                  {h.badge}
                </span>
              </div>
              <h4 className="mt-3 text-sm font-semibold text-white">
                {h.title}
              </h4>
              <p className="mt-1 text-lg font-bold text-white/80">{h.value}</p>
              <p className="mt-1 text-[11px] leading-relaxed text-white/40">
                {h.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}