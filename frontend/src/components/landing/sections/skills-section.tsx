"use client";

import { cn } from "@/lib/utils";

import ProgressiveSkillsAnimation from "../progressive-skills-animation";
import { Section } from "../section";

export function SkillsSection({ className }: { className?: string }) {
  return (
    <Section
      className={cn("h-[calc(100vh-64px)] w-full bg-white/2", className)}
      title="GrayHunt Intelligence Flow"
      subtitle={
        <div>
          GrayHunt loads the right crawler and analysis skills as the case
          unfolds — from platform discovery to evidence collection.
          <br />
          Raw posts, accounts, domains, and invite links become structured
          black/gray market intelligence reports.
        </div>
      }
    >
      <div className="relative overflow-hidden">
        <ProgressiveSkillsAnimation />
      </div>
    </Section>
  );
}
