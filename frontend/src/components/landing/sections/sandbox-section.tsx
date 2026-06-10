"use client";

import {
  AnimatedSpan,
  Terminal,
  TypingAnimation,
} from "@/components/ui/terminal";

import { Section } from "../section";

export function SandboxSection({ className }: { className?: string }) {
  return (
    <Section
      className={className}
      title="Crawler Runtime Environment"
      subtitle={
        <p>
          GrayHunt runs crawlers, parsers, and analyzers inside an isolated
          workspace built for long-running intelligence jobs.
        </p>
      }
    >
      <div className="mt-8 flex w-full max-w-6xl flex-col items-center gap-12 lg:flex-row lg:gap-16">
        {/* Left: Terminal */}
        <div className="w-full flex-1">
          <Terminal className="h-[360px] w-full">
            {/* Scene 1: Crawl sources */}
            <TypingAnimation>$ grayhunt crawl --platform xhs</TypingAnimation>
            <AnimatedSpan delay={800} className="text-zinc-400">
              Loaded 18 seed keywords and 42 watch targets
            </AnimatedSpan>

            <TypingAnimation delay={1200}>
              $ grayhunt crawl --platform telegram
            </TypingAnimation>
            <AnimatedSpan delay={2000} className="text-green-500">
              ✔ 1,284 raw samples collected
            </AnimatedSpan>

            <TypingAnimation delay={2400}>
              $ grayhunt extract --entities
            </TypingAnimation>
            <AnimatedSpan delay={3200} className="text-blue-500">
              ✔ 392 accounts, links, domains, and contacts extracted
            </AnimatedSpan>

            <TypingAnimation delay={3600}>
              $ grayhunt analyze --risk black-gray
            </TypingAnimation>
            <AnimatedSpan delay={4200} className="text-green-500">
              ✔ 47 high-risk clusters identified
            </AnimatedSpan>
            <AnimatedSpan delay={4500} className="text-green-500">
              ✔ Cross-platform duplicate evidence merged
            </AnimatedSpan>
            <AnimatedSpan delay={4800} className="text-green-500">
              ✔ Report ready: grayhunt_intel_report.md
            </AnimatedSpan>

            <TypingAnimation delay={5400}>
              $ sqlite3 risk_evidence.sqlite &quot;.tables&quot;
            </TypingAnimation>
            <AnimatedSpan delay={6200} className="text-zinc-400">
              samples entities clusters trends reports
            </AnimatedSpan>
          </Terminal>
        </div>

        {/* Right: Description */}
        <div className="w-full flex-1 space-y-6">
          <div className="space-y-4">
            <p className="text-sm font-medium tracking-wider text-purple-400 uppercase">
              Isolated analysis
            </p>
            <h2 className="text-4xl font-bold tracking-tight lg:text-5xl">
              <a
                href="https://github.com/agent-infra/sandbox"
                target="_blank"
                rel="noopener noreferrer"
              >
                AIO Sandbox
              </a>
            </h2>
          </div>

          <div className="space-y-4 text-lg text-zinc-400">
            <p>
              GrayHunt can run inside{" "}
              <a
                href="https://github.com/agent-infra/sandbox"
                className="underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                All-in-One Sandbox
              </a>{" "}
              with browser automation, shell execution, file storage, and MCP
              integrations in a single Docker container.
            </p>
          </div>

          {/* Feature Tags */}
          <div className="flex flex-wrap gap-3 pt-4">
            <span className="rounded-full border border-zinc-800 bg-zinc-900 px-4 py-2 text-sm text-zinc-300">
              Isolated
            </span>
            <span className="rounded-full border border-zinc-800 bg-zinc-900 px-4 py-2 text-sm text-zinc-300">
              Safe
            </span>
            <span className="rounded-full border border-zinc-800 bg-zinc-900 px-4 py-2 text-sm text-zinc-300">
              Persistent
            </span>
            <span className="rounded-full border border-zinc-800 bg-zinc-900 px-4 py-2 text-sm text-zinc-300">
              Mountable FS
            </span>
            <span className="rounded-full border border-zinc-800 bg-zinc-900 px-4 py-2 text-sm text-zinc-300">
              Long-running
            </span>
          </div>
        </div>
      </div>
    </Section>
  );
}
