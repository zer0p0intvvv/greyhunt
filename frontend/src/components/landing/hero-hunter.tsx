"use client";

import { ChevronRightIcon, ShieldAlert, Target, Network, Radar } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { FlickeringGrid } from "@/components/ui/flickering-grid";
import Galaxy from "@/components/ui/galaxy";
import { WordRotate } from "@/components/ui/word-rotate";
import { cn } from "@/lib/utils";

export function HeroHunter({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "flex size-full flex-col items-center justify-center",
        className,
      )}
    >
      <div className="absolute inset-0 z-0 bg-black/50">
        <Galaxy
          mouseRepulsion
          starSpeed={0.15}
          density={0.5}
          glowIntensity={0.4}
          twinkleIntensity={0.35}
          speed={0.6}
          saturation={0.12}
        />
      </div>
      <FlickeringGrid
        className="absolute inset-0 z-0 translate-y-4 mask-[url(/images/gmh.svg)] mask-size-[100vw] mask-center mask-no-repeat md:mask-size-[80vh]"
        squareSize={4}
        gridGap={4}
        color="white"
        maxOpacity={0.3}
        flickerChance={0.22}
      />
      <div className="container-md relative z-10 mx-auto flex h-screen flex-col items-center justify-center px-4">
        <div className="mb-6 flex items-center gap-2 rounded-full border border-red-500/30 bg-red-500/10 px-4 py-1.5 text-sm text-red-400">
          <Radar className="size-3.5" />
          灰黑产挖掘 Agent · 全流程自治 · 对话即分析
        </div>

        <h1 className="flex flex-wrap items-center justify-center gap-3 text-4xl font-bold leading-tight md:text-6xl">
          <WordRotate
            words={[
              "挖掘黑灰产团伙",
              "识别隐蔽马甲群",
              "追踪超级团伙网络",
              "揭示一波人多业务",
              "破解黑话暗语变体",
              "构建攻击链图谱",
              "飞轮自主拓展",
            ]}
          />
        </h1>

        <p className="text-muted-foreground mt-8 max-w-2xl text-center text-xl text-shadow-sm leading-relaxed">
          全流程自治Agent：对话爬取 → 去重去噪 → 两层团伙 → 黑话飞轮 → 知识图谱 → 硬核报告
          <br />
          <span className="text-white/60 text-lg">
            基于 DeerFlow SuperAgent 架构 · 从零爬取到知识图谱 · 全流程自主编排
          </span>
        </p>

        <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-4 md:gap-8">
          <StatBadge icon={ShieldAlert} value="138K+" label="原始数据" />
          <StatBadge icon={Target} value="514" label="核心团伙" />
          <StatBadge icon={Network} value="20" label="超级团伙" />
          <StatBadge icon={Radar} value="飞轮闭环" label="增量+回流" color="amber" />
        </div>

        <Link href="/workspace">
          <Button className="mt-10 scale-110" size="lg">
            <span className="text-md">启动灰黑产挖掘 Agent</span>
            <ChevronRightIcon className="size-4" />
          </Button>
        </Link>
        <Link href="/deck" className="mt-4 text-sm text-white/40 underline-offset-4 transition-colors hover:text-white/80 hover:underline">
          ▶ 进入演示模式（评委 PPT）
        </Link>
      </div>
    </div>
  );
}

function StatBadge({
  icon: Icon,
  value,
  label,
  color = "red",
}: {
  icon: React.ComponentType<{ className?: string }>;
  value: string;
  label: string;
  color?: string;
}) {
  const colorMap: Record<string, string> = {
    red: "border-red-500/20 bg-red-500/5 text-red-400",
    amber: "border-amber-500/20 bg-amber-500/5 text-amber-400",
    blue: "border-blue-500/20 bg-blue-500/5 text-blue-400",
    green: "border-green-500/20 bg-green-500/5 text-green-400",
  };
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-1 rounded-xl border px-6 py-3 backdrop-blur-sm",
        colorMap[color] || colorMap.red,
      )}
    >
      <Icon className="size-4 opacity-70" />
      <span className="text-2xl font-bold tabular-nums">{value}</span>
      <span className="text-xs opacity-60">{label}</span>
    </div>
  );
}