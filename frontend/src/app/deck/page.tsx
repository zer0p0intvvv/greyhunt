"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  ChevronLeft, ChevronRight, ShieldAlert, Target, Network, Zap,
  Database, Filter, Cpu, RefreshCw, Bolt, TrendingUp, Eye,
  Search, GitCompare, Brain, FileText, Radar, Hash, Layers,
  ArrowRight, ArrowUpRight, Globe, Server, Terminal, BarChart3,
} from "lucide-react";
import dynamic from "next/dynamic";
import { AuroraText } from "@/components/ui/aurora-text";
import { NumberTicker } from "@/components/ui/number-ticker";

const Galaxy = dynamic(() => import("@/components/ui/galaxy"), { ssr: false });

const TOTAL = 12;

export default function DeckPage() {
  const [slide, setSlide] = useState(0);
  const next = useCallback(() => setSlide((s) => Math.min(s + 1, TOTAL - 1)), []);
  const prev = useCallback(() => setSlide((s) => Math.max(s - 1, 0)), []);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " ") next();
      if (e.key === "ArrowLeft") prev();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [next, prev]);

  return (
    <div className="relative h-screen w-full overflow-hidden bg-[#070709] text-white font-sans">
      <div className="absolute inset-0 z-0 opacity-50">
        <Galaxy mouseRepulsion={false} starSpeed={0.08} density={0.45} glowIntensity={0.35} twinkleIntensity={0.25} speed={0.35} saturation={0.12} />
      </div>
      <div ref={containerRef} className="relative z-10 flex h-full w-full items-center justify-center px-8 py-16 md:px-24">
        <div key={slide} className="animate-fade-in-up flex w-full max-w-6xl flex-col items-center justify-center">{slides[slide]}</div>
      </div>
      <div className="absolute bottom-6 right-6 z-20 flex items-center gap-4">
        <span className="font-mono text-sm tabular-nums text-white/30 tracking-wider">
          {String(slide + 1).padStart(2, "0")} / {String(TOTAL).padStart(2, "0")}
        </span>
        <button onClick={prev} disabled={slide === 0}
          className="flex size-10 items-center justify-center rounded-full border border-white/10 bg-white/5 backdrop-blur-md transition-all hover:bg-white/15 disabled:opacity-20">
          <ChevronLeft className="size-4" />
        </button>
        <button onClick={next} disabled={slide === TOTAL - 1}
          className="flex size-10 items-center justify-center rounded-full border border-red-500/20 bg-red-500/10 backdrop-blur-md transition-all hover:bg-red-500/25 disabled:opacity-20">
          <ChevronRight className="size-4" />
        </button>
      </div>
      <div className="absolute bottom-7 left-6 z-20 flex gap-1.5">
        {Array.from({ length: TOTAL }).map((_, i) => (
          <button key={i} onClick={() => setSlide(i)}
            className={`h-1.5 rounded-full transition-all duration-300 ${i === slide ? "w-6 bg-red-500" : "w-1.5 bg-white/20 hover:bg-white/40"}`} />
        ))}
      </div>
    </div>
  );
}

const slides = [
  <div className="flex flex-col items-center text-center">
    <div className="mb-8 flex items-center gap-2 rounded-full border border-red-500/20 bg-red-500/10 px-5 py-2 text-sm font-medium text-red-400 tracking-wide">
      <Radar className="size-4" /> 寻找黑灰产 · 比赛作品
    </div>
    <h1 className="text-6xl font-black leading-none tracking-tight md:text-8xl">
      <AuroraText colors={["#ff3b3b", "#ff8a3b", "#ffd23b"]}>灰黑产挖掘</AuroraText>
    </h1>
    <h2 className="mt-3 text-4xl font-black tracking-tight md:text-6xl">Agent</h2>
    <p className="mt-10 max-w-2xl text-xl leading-relaxed text-white/50">
      全流程自治智能体<br />
      <span className="text-white/70 mt-2 block">对话爬取 → 团伙挖掘 → 知识图谱 → 飞轮回流 → 硬核报告</span>
    </p>
    <div className="mt-12 flex flex-wrap items-center justify-center gap-3 text-sm">
      <span className="rounded-full border border-white/10 bg-white/5 px-4 py-2 backdrop-blur-sm text-white/40">DeerFlow SuperAgent</span>
      <span className="rounded-full border border-white/10 bg-white/5 px-4 py-2 backdrop-blur-sm text-white/40">闲鱼 · 字节系</span>
      <span className="rounded-full border border-white/10 bg-white/5 px-4 py-2 backdrop-blur-sm text-white/40">138K+ 数据</span>
      <span className="rounded-full border border-white/10 bg-white/5 px-4 py-2 backdrop-blur-sm text-white/40">514 团伙</span>
    </div>
  </div>,

  <div className="flex flex-col items-center text-center">
    <SlideTitle icon={ShieldAlert} kicker="背景" title="黑灰产藏在哪？" />
    <div className="mt-12 grid grid-cols-1 gap-5 md:grid-cols-3">
      <CardBox emoji="🕵️" title="马甲伪装" desc="同一团伙开几十个小号，话术模板一模一样，单看商品根本认不出是同一拨人" color="red" />
      <CardBox emoji="🔤" title="黑话暗语" desc="抖币→DB→💎，Dou+→豆荚→抖➕，同音/拆字/emoji 持续变体规避审核" color="amber" />
      <CardBox emoji="🕸️" title="跨业务联动" desc="一波人做代充+代投+带货+刷量，表面独立实则同一超级团伙，一损俱损" color="purple" />
    </div>
    <p className="mt-12 text-lg text-white/40">
      传统人工排查：<span className="text-red-400 font-bold line-through">慢、漏、不可规模化</span>
    </p>
  </div>,

  <div className="flex flex-col items-center text-center">
    <SlideTitle icon={GitCompare} kicker="方案" title="全流程自治 Agent" />
    <div className="mt-12 flex flex-wrap items-center justify-center gap-2 md:gap-3">
      {[
        { icon: Search, t: "对话爬取", sub: "Playwright", c: "text-blue-400", bg: "bg-blue-500/8" },
        { icon: Filter, t: "三层漏斗", sub: "规则+LLM", c: "text-amber-400", bg: "bg-amber-500/8" },
        { icon: GitCompare, t: "两层团伙", sub: "指纹+union", c: "text-red-400", bg: "bg-red-500/8" },
        { icon: Brain, t: "黑话挖掘", sub: "LLM扩展", c: "text-purple-400", bg: "bg-purple-500/8" },
        { icon: Network, t: "知识图谱", sub: "D3力导向", c: "text-cyan-400", bg: "bg-cyan-500/8" },
        { icon: FileText, t: "硬核报告", sub: "Markdown", c: "text-green-400", bg: "bg-green-500/8" },
      ].map((s, i, arr) => (
        <div key={s.t} className="flex items-center gap-2 md:gap-3">
          <div className={`flex w-28 flex-col items-center gap-2 rounded-2xl border border-white/8 ${s.bg} p-4 backdrop-blur-sm md:w-32`}>
            <s.icon className={`size-7 ${s.c}`} />
            <span className="text-sm font-semibold">{s.t}</span>
            <span className="text-[10px] text-white/30">{s.sub}</span>
          </div>
          {i < arr.length - 1 && <ChevronRight className="size-4 shrink-0 text-white/20" />}
        </div>
      ))}
    </div>
    <div className="mt-10 flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-5 py-2.5 text-sm font-medium text-amber-400">
      <RefreshCw className="size-4" /> 飞轮回流：新黑话 → 新关键词 → 自动回灌爬虫 → 更多团伙
    </div>
  </div>,

  <div className="flex flex-col items-center text-center">
    <SlideTitle icon={TrendingUp} kicker="成果" title="数据规模" />
    <div className="mt-12 grid grid-cols-2 gap-10 md:grid-cols-4">
      <BigStat value={138051} label="原始数据" suffix="+" color="text-blue-400" sub="375个文件" />
      <BigStat value={514} label="核心团伙" color="text-red-400" sub="话术指纹聚类" />
      <BigStat value={20} label="超级团伙" color="text-purple-400" sub="union-find" />
      <BigStat value={579} label="头号团伙" color="text-amber-400" sub="Dou+×带货" />
    </div>
    <div className="mt-12 flex flex-wrap items-center justify-center gap-4 text-base text-white/40">
      <span className="rounded-full border border-white/8 bg-white/5 px-4 py-1.5">20 条字节产品线</span>
      <span className="rounded-full border border-white/8 bg-white/5 px-4 py-1.5">446 关键词</span>
      <span className="rounded-full border border-white/8 bg-white/5 px-4 py-1.5">89 黑话变体</span>
      <span className="rounded-full border border-white/8 bg-white/5 px-4 py-1.5">71.8K 高质量数据</span>
    </div>
  </div>,

  <div className="flex flex-col items-center text-center">
    <SlideTitle icon={Network} kicker="核心算法" title="两层团伙模型" />
    <div className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-2">
      <div className="rounded-3xl border border-red-500/20 bg-gradient-to-br from-red-950/20 to-transparent p-10 text-left">
        <div className="mb-1 text-xs font-bold tracking-widest text-red-400 uppercase">第一层</div>
        <div className="text-3xl font-black">核心团伙</div>
        <div className="mt-1 text-sm font-semibold text-red-300/70">话术模板指纹聚类</div>
        <p className="mt-5 text-sm leading-relaxed text-white/50">
          相同话术模板 = 同一团伙的马甲号（sock-puppets）。
          不做 BFS 链式膨胀，每个团伙业务纯净、可审计、可解释。
        </p>
        <div className="mt-6 flex items-center gap-3">
          <span className="text-5xl font-black text-red-400">514</span>
          <span className="text-sm text-red-300/60">个核心团伙</span>
        </div>
      </div>
      <div className="rounded-3xl border border-purple-500/20 bg-gradient-to-br from-purple-950/20 to-transparent p-10 text-left">
        <div className="mb-1 text-xs font-bold tracking-widest text-purple-400 uppercase">第二层</div>
        <div className="text-3xl font-black">超级团伙</div>
        <div className="mt-1 text-sm font-semibold text-purple-300/70">union-find 交叉关联</div>
        <p className="mt-5 text-sm leading-relaxed text-white/50">
          共享卖家 + 同图 + 同话术，把多个表面独立的业务团伙
          连成"一波人做多业务"的超级网络。
        </p>
        <div className="mt-6 flex items-center gap-3">
          <span className="text-5xl font-black text-purple-400">20</span>
          <span className="text-sm text-purple-300/60">个超级网络</span>
        </div>
      </div>
    </div>
  </div>,

  <div className="flex flex-col items-center text-center">
    <SlideTitle icon={ShieldAlert} kicker="头号目标" title="最大超级团伙网络" />
    <div className="mt-10 w-full max-w-3xl rounded-3xl border-2 border-red-500/30 bg-gradient-to-br from-red-950/30 to-black/40 px-10 py-10 backdrop-blur-sm">
      <div className="flex items-baseline justify-center gap-4">
        <span className="text-7xl font-black text-red-400">18<span className="text-3xl">团</span></span>
        <span className="text-6xl font-black text-white/30">·</span>
        <span className="text-7xl font-black text-red-400">579<span className="text-3xl">人</span></span>
      </div>
      <div className="mt-4 text-xl font-medium text-red-300/70">Dou+ 代投 × 带货权限 · 跨业务联合作案</div>
      <div className="mt-2 text-sm text-red-300/40">一波人做多业务，从代投折扣到账号共享，全链路覆盖</div>
    </div>
    <div className="mt-8 flex flex-wrap justify-center gap-3">
      {[
        { g: 16, p: 199, b: "代拍·剪映" }, { g: 4, p: 123, b: "数据·曝光" },
        { g: 6, p: 92, b: "充值" }, { g: 7, p: 62, b: "账号升级" },
        { g: 5, p: 36, b: "会员" }, { g: 4, p: 46, b: "千川" },
      ].map((x, i) => (
        <div key={i} className="rounded-xl border border-white/8 bg-white/5 px-5 py-3 backdrop-blur-sm">
          <div className="text-lg font-bold">{x.g}团/{x.p}人</div>
          <div className="text-xs text-white/35">{x.b}</div>
        </div>
      ))}
    </div>
  </div>,

  <div className="flex flex-col items-center text-center">
    <SlideTitle icon={RefreshCw} kicker="飞轮" title="4 轮自我强化" />
    <div className="mt-10 w-full max-w-4xl">
      <div className="grid grid-cols-4 gap-3">
        {[
          { r: "初始", raw: "55K", gang: 312, top: "11团/403人" },
          { r: "飞轮 1", raw: "76K", gang: 314, top: "18团/565人" },
          { r: "飞轮 2", raw: "87K", gang: 391, top: "18团/571人" },
          { r: "飞轮 3", raw: "138K", gang: 514, top: "18团/579人" },
        ].map((x, i) => (
          <div key={x.r} className={`rounded-2xl border p-5 backdrop-blur-sm ${i === 3 ? "border-white/20 bg-white/8 shadow-lg shadow-white/5" : "border-white/8 bg-white/5"}`}>
            <div className="mb-3 text-xs font-bold text-white/40">{x.r}</div>
            <div className="text-2xl font-black text-white">{x.raw}</div>
            <div className="mt-1 text-sm text-white/50">{x.gang} 团伙</div>
            <div className="mt-2 rounded-lg bg-white/5 py-1.5 text-xs font-semibold text-red-400">{x.top}</div>
          </div>
        ))}
      </div>
      <div className="mt-6 rounded-xl border border-white/8 bg-black/20 p-5 backdrop-blur-sm">
        <div className="flex items-center justify-center gap-2 text-sm text-white/40">
          <TrendingUp className="size-4" />
          核心团伙: 312 → 314 → 391 → <span className="text-white font-bold">514</span>
          <span className="mx-2 text-white/20">|</span>
          超级团伙: 11 → 11 → 15 → <span className="text-white font-bold">20</span>
          <span className="mx-2 text-white/20">|</span>
          头号: 403 → 565 → 571 → <span className="text-red-400 font-bold">579</span>
        </div>
      </div>
    </div>
  </div>,

  <div className="flex flex-col items-center text-center">
    <SlideTitle icon={Hash} kicker="覆盖" title="关键词集群" />
    <div className="mt-10 grid grid-cols-2 gap-4 md:grid-cols-3 max-w-4xl mx-auto">
      {[
        { cat: "代充系", words: "抖币·钻石·DB·抖B·dy充值·音浪·💎·CapCut会员·剪映VIP", color: "border-blue-500/20 bg-blue-500/5" },
        { cat: "投流系", words: "Dou+·豆荚·抖加·D+投放·千川·巨量引擎·穿山甲·星图", color: "border-red-500/20 bg-red-500/5" },
        { cat: "数据工具", words: "蝉妈妈·灰豚·考古加·飞瓜·kaogujia·chanmama·灰🐬·kgj", color: "border-purple-500/20 bg-purple-500/5" },
        { cat: "直播/工会", words: "直播人气·挂铁·弹幕·TK公会·TikTok MCN·无人直播·数字人", color: "border-amber-500/20 bg-amber-500/5" },
        { cat: "账号/解封", words: "号交易·白号·实名·改实名·申诉·限流·蓝V·企业号·MCN", color: "border-cyan-500/20 bg-cyan-500/5" },
        { cat: "新业务线", words: "飞书·即梦AI·穿山甲·西瓜视频·番茄小说·懂车帝·火山引擎", color: "border-green-500/20 bg-green-500/5" },
      ].map((k) => (
        <div key={k.cat} className={`rounded-2xl border p-5 text-left backdrop-blur-sm ${k.color}`}>
          <div className="mb-2 text-xs font-bold text-white/60">{k.cat}</div>
          <div className="text-sm leading-relaxed text-white/40">{k.words}</div>
        </div>
      ))}
    </div>
    <p className="mt-8 text-sm text-white/30">446 关键词 · 覆盖 20 条字节产品线 · 飞轮自动扩展</p>
  </div>,

  <div className="flex flex-col items-center text-center">
    <SlideTitle icon={Cpu} kicker="工程" title="又快又省" />
    <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3 max-w-4xl mx-auto">
      <EngCard icon={Filter} title="三层漏斗" big="99%+" desc="75%数据零Token规则层判定，LLM调用压缩99.8%，成本<$0.30" detail="若逐条LLM判定需$15-30" color="emerald" />
      <EngCard icon={RefreshCw} title="增量加载" big="98%" desc="checkpoint缓存83MB，375文件→0-5新文件，IO减少98%，秒级加载" detail="首次全量·后续增量" color="purple" />
      <EngCard icon={Bolt} title="飞轮自动回流" big="全自动" desc="slang_expand --auto-append，新黑话自动追加词库，无人介入" detail="备份·去重·增量写入" color="amber" />
    </div>
    <div className="mt-10 rounded-2xl border border-white/8 bg-black/20 p-5 backdrop-blur-sm max-w-3xl">
      <div className="flex items-center justify-center gap-4 text-sm text-white/40">
        <span className="flex items-center gap-1"><Cpu className="size-3" /> 总Token成本</span>
        <ArrowRight className="size-3 text-white/20" />
        <span className="text-lg font-bold text-emerald-400">&lt;$0.30</span>
        <span className="text-white/20">|</span>
        <span>单次分析全流程</span>
        <ArrowRight className="size-3 text-white/20" />
        <span className="text-lg font-bold text-purple-400">&lt;3 min</span>
      </div>
    </div>
  </div>,

  <div className="flex flex-col items-center text-center">
    <SlideTitle icon={Server} kicker="架构" title="Agent 技术栈" />
    <div className="mt-10 grid grid-cols-2 gap-4 md:grid-cols-4 max-w-4xl mx-auto">
      {[
        { icon: Terminal, title: "DeerFlow", desc: "SuperAgent 框架·对话编排·子代理调度" },
        { icon: Globe, title: "Playwright", desc: "浏览器自动化·闲鱼MTOP API·扫码登录" },
        { icon: Cpu, title: "豆包 LLM", desc: "火山方舟 Ark·黑话扩展·团伙定性·相关性判定" },
        { icon: Brain, title: "Python 算法", desc: "话术模板指纹·union-find·N-gram·D3.js" },
      ].map((t) => (
        <div key={t.title} className="rounded-2xl border border-white/8 bg-white/5 p-5 text-left backdrop-blur-sm">
          <div className="rounded-lg bg-white/5 w-fit p-2.5 mb-3">
            <t.icon className="size-5 text-white/60" />
          </div>
          <h3 className="text-sm font-bold text-white">{t.title}</h3>
          <p className="mt-2 text-xs text-white/40 leading-relaxed">{t.desc}</p>
        </div>
      ))}
    </div>
    <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
      {["Python", "Playwright", "豆包 Ark", "D3.js", "union-find", "N-gram", "三层漏斗", "DeerFlow", "Next.js", "Tailwind"].map((t) => (
        <span key={t} className="rounded-full border border-white/8 bg-white/5 px-3 py-1 text-xs text-white/35">{t}</span>
      ))}
    </div>
  </div>,

  <div className="flex flex-col items-center text-center">
    <SlideTitle icon={Globe} kicker="数据流" title="从零到报告" />
    <div className="mt-10 w-full max-w-4xl">
      <div className="flex flex-col items-center gap-3 md:flex-row md:justify-center md:gap-4">
        {[
          { icon: Search, label: "闲鱼爬取", sub: "Playwright", color: "border-blue-500/20 bg-blue-500/5" },
          { icon: Filter, label: "数据清洗", sub: "去重+漏斗", color: "border-amber-500/20 bg-amber-500/5" },
          { icon: GitCompare, label: "团伙检测", sub: "514团", color: "border-red-500/20 bg-red-500/5" },
          { icon: Brain, label: "黑话挖掘", sub: "89变体", color: "border-purple-500/20 bg-purple-500/5" },
          { icon: FileText, label: "报告输出", sub: "Markdown", color: "border-green-500/20 bg-green-500/5" },
        ].map((s, i, arr) => (
          <div key={s.label} className="flex items-center gap-2">
            <div className={`flex flex-col items-center gap-2 rounded-2xl border px-5 py-4 backdrop-blur-sm ${s.color}`}>
              <s.icon className="size-6 text-white/60" />
              <span className="text-sm font-semibold">{s.label}</span>
              <span className="text-[10px] text-white/30">{s.sub}</span>
            </div>
            {i < arr.length - 1 && <ArrowRight className="size-4 shrink-0 text-white/20" />}
          </div>
        ))}
      </div>
      <div className="mt-6 flex justify-center">
        <div className="flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-4 py-2 text-xs text-amber-400">
          <RefreshCw className="size-3" /> 飞轮回灌：新黑话 → 关键词库 → 重新爬取 → 更多团伙
        </div>
      </div>
    </div>
  </div>,

  <div className="flex flex-col items-center text-center">
    <div className="text-6xl font-black md:text-7xl leading-none">
      <AuroraText colors={["#ff3b3b", "#ff8a3b", "#ffd23b"]}>一句话，全搞定</AuroraText>
    </div>
    <p className="mt-10 max-w-3xl text-2xl leading-relaxed text-white/50">
      对 Agent 说<br />
      <span className="mt-3 block rounded-2xl border border-white/10 bg-white/5 px-8 py-4 font-mono text-lg text-white/70 backdrop-blur-sm">
        「爬一下抖音代充并出团伙报告」
      </span>
    </p>
    <p className="mt-6 text-lg text-white/40">
      它自己完成 <span className="font-bold text-white">爬取 → 分析 → 图谱 → 飞轮 → 报告</span>
    </p>
    <div className="mt-12 flex flex-wrap justify-center gap-4">
      <a href="/" className="rounded-full border border-white/10 bg-white/5 px-8 py-3 text-base backdrop-blur-sm transition-all hover:bg-white/15 hover:border-white/20">返回首页</a>
      <a href="/gang-viz.html" target="_blank" className="flex items-center gap-2 rounded-full border border-red-500/20 bg-red-500/10 px-8 py-3 text-base backdrop-blur-sm transition-all hover:bg-red-500/30">
        <Eye className="size-5" /> 交互式团伙图谱
      </a>
      <a href="/workspace" className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-8 py-3 text-base backdrop-blur-sm transition-all hover:bg-white/15">
        <Terminal className="size-5" /> 启动 Agent
      </a>
    </div>
  </div>,
];

function SlideTitle({ icon: Icon, kicker, title }: { icon: React.ComponentType<{ className?: string }>; kicker: string; title: string }) {
  return (
    <div className="flex flex-col items-center">
      <div className="mb-4 flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium text-white/40 tracking-wide">
        <Icon className="size-3" /> {kicker}
      </div>
      <h2 className="text-5xl font-black tracking-tight md:text-6xl">{title}</h2>
    </div>
  );
}

function CardBox({ emoji, title, desc, color }: { emoji: string; title: string; desc: string; color: string }) {
  const c: Record<string, string> = { red: "border-red-500/20 bg-red-500/5", amber: "border-amber-500/20 bg-amber-500/5", purple: "border-purple-500/20 bg-purple-500/5" };
  return (
    <div className={`rounded-2xl border p-7 text-left backdrop-blur-sm ${c[color]}`}>
      <div className="text-4xl">{emoji}</div>
      <h3 className="mt-4 text-xl font-bold">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-white/45">{desc}</p>
    </div>
  );
}

function BigStat({ value, label, suffix, color, sub }: { value: number; label: string; suffix?: string; color: string; sub: string }) {
  return (
    <div className="flex flex-col items-center">
      <span className={`text-5xl font-black tabular-nums md:text-6xl ${color}`}>
        <NumberTicker value={value} className="text-inherit" />{suffix}
      </span>
      <span className="mt-2 text-base font-semibold text-white/70">{label}</span>
      <span className="mt-1 text-xs text-white/30">{sub}</span>
    </div>
  );
}

function EngCard({ icon: Icon, title, big, desc, detail, color }: { icon: React.ComponentType<{ className?: string }>; title: string; big: string; desc: string; detail: string; color: string }) {
  const c: Record<string, string> = { emerald: "text-emerald-400 border-emerald-500/15 bg-emerald-500/5", purple: "text-purple-400 border-purple-500/15 bg-purple-500/5", amber: "text-amber-400 border-amber-500/15 bg-amber-500/5" };
  return (
    <div className={`rounded-2xl border p-7 text-left backdrop-blur-sm ${c[color]}`}>
      <Icon className="size-7 mb-1" />
      <div className="mt-2 text-4xl font-black">{big}</div>
      <h3 className="mt-1 text-lg font-bold text-white">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-white/45">{desc}</p>
      <div className="mt-3 rounded-lg bg-white/5 px-3 py-1.5 text-xs text-white/30">{detail}</div>
    </div>
  );
}