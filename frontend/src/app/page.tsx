import { Footer } from "@/components/landing/footer";
import { Header } from "@/components/landing/header";
import { Hero } from "@/components/landing/hero";
import { AgentDemoSection } from "@/components/landing/sections/agent-demo-section";
import { GangGraphSection } from "@/components/landing/sections/gang-graph-section";
import { IntelligenceDashboardSection } from "@/components/landing/sections/intelligence-dashboard-section";
import { SandboxSection } from "@/components/landing/sections/sandbox-section";
import { SkillsSection } from "@/components/landing/sections/skills-section";

export default function LandingPage() {
  return (
    <div className="min-h-screen w-full bg-[#0a0a0a]">
      <Header />
      <main className="flex w-full flex-col">
        <Hero />
        <AgentDemoSection />
        <IntelligenceDashboardSection />
        <GangGraphSection />
        <SkillsSection />
        <SandboxSection />
      </main>
      <Footer />
    </div>
  );
}
