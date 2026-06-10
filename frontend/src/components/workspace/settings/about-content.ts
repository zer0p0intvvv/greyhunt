/**
 * About GrayHunt markdown content. Inlined to avoid raw-loader dependency
 * (Turbopack cannot resolve raw-loader for .md imports).
 */
export const aboutMarkdown = `# About GrayHunt

> **Crawler-driven intelligence for black and gray market risk.**

GrayHunt is an intelligence agent that crawls major platforms, collects black/gray market signals, extracts risky entities, and produces structured analysis reports.

---

## Core Features

* **Crawler Skills**: Add platform-specific collectors for forums, social platforms, channels, and other OSINT sources.
* **Entity Extraction**: Pull out accounts, phone numbers, domains, handles, invite links, prices, and tool names.
* **Risk Analysis**: Cluster samples by risk type, source, entity, time, and campaign pattern.
* **Evidence Workspace**: Store raw samples, filtered entities, SQLite evidence tables, and generated reports.
* **Long-Running Runtime**: Run crawlers and analyzers in an isolated workspace for durable intelligence jobs.

---

## Intelligence Workflow

1. Seed collection targets and platform keywords.
2. Crawl source posts, channels, profiles, and linked resources.
3. Normalize raw samples and extract entities.
4. Score black/gray market indicators and cluster related evidence.
5. Generate a report with trends, top entities, high-risk groups, and recommended follow-up.

## License

GrayHunt is distributed under the **MIT License**.

---

## Acknowledgments

GrayHunt builds on open-source agent, frontend, and sandbox infrastructure.

### Core Frameworks
- **[LangChain](https://github.com/langchain-ai/langchain)**: A phenomenal framework that powers our LLM interactions and chains.
- **[LangGraph](https://github.com/langchain-ai/langgraph)**: Enabling sophisticated multi-agent orchestration.
- **[Next.js](https://nextjs.org/)**: A cutting-edge framework for building web applications.

### UI Libraries
- **[Shadcn](https://ui.shadcn.com/)**: Minimalistic components that power our UI.
- **[SToneX](https://github.com/stonexer)**: For his invaluable contribution to token-by-token visual effects.
`;
