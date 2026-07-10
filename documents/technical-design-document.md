# Nova — Technical Design Document

Architecture and design documentation for Nova, MCN Group's internal AI
assistant. Structured using [arc42](https://arc42.org), with
[C4 Model](https://c4model.com) diagrams and
[ADRs](https://adr.github.io/) for architecture decisions.

Each of these three frameworks was picked to solve a different documentation
failure mode. arc42 is a fixed but lightweight checklist of architectural
concerns — it makes sure nothing important (requirements, context,
decisions, runtime behavior, deployment, risk) gets forgotten, without
forcing every section to be exhaustive. C4 addresses a different problem:
architecture diagrams usually fail because they mix zoom levels into one
unreadable picture, so C4 fixes a small set of zoom levels (Context →
Container → Component → Code), each answering one question at one altitude.
ADRs address a third problem — the *reasoning* behind a decision goes stale
faster than the code itself, so each significant decision is captured once,
at the moment it's made, as a standalone record that's never silently
edited (only superseded). See [reference/](reference/) for the full notes
on each framework.

Status: **Draft — work in progress.**

---

## 1. Introduction and Goals

### 1.1 Requirements Overview

Nova is an internal AI assistant for MCN Group that helps employees get
answers quickly by combining three sources of knowledge: the company's
internal documentation, structured company data, and the public web.

**Functional goals:**

1. As an employee, I want to ask questions about company SOPs/documentation
   in natural language, so that I don't have to manually search through
   documents.
2. As an employee, I want to ask questions about company data (viewership,
   subscribers, engagement, etc.), so that I can get quick insights without
   writing SQL myself.
3. As an employee, I want the assistant to search the web when the answer
   isn't in internal knowledge, so that I still get an answer instead of a
   dead end.
4. As an employee, I want a single chat interface for all of the above, so
   that I don't need to switch between different tools depending on the
   question type.

**Non-goals:**

- Not a replacement for BI dashboards — Nova surfaces answers
  conversationally, it does not aim to replace dedicated analytics tooling.
- Not a document editor — Nova reads/retrieves from the knowledge base, it
  does not manage document authoring/versioning.
- No multi-tenant / external-facing use — Nova is for internal MCN Group
  employees only.

### 1.2 Quality Goals

Quality goals are defined using [ISO/IEC 25010](reference/iso-25010.md)
rather than freeform adjectives. "Good quality" means different things to
different people, and without a shared vocabulary, quality goals collapse
into vague terms ("robust", "scalable") nobody can prioritize against each
other. ISO 25010 fixes this with a named set of 9 quality characteristics,
so trade-offs (e.g. optimizing Reliability over Flexibility) can be made
explicit instead of accidental.

All 9 characteristics are assessed below for relevance to Nova and ranked
accordingly. The **top 5** are set as this project's quality goals (arc42
recommends limiting to 3-5 so the goals stay actionable and drive real
trade-offs, rather than trying to satisfy all 9 equally).

| Rank | ISO 25010 Characteristic | Relevance | Set as Goal? | Motivation |
|---|---|---|---|---|
| 1 | Functional Suitability (Groundedness / Accuracy) | High | ✅ | Answers must be based on real sources (KB/data/web), not hallucinated — critical for trust, especially when used for decision-making from company data. |
| 2 | Performance Efficiency (Response Latency) | High | ✅ | Queries pass through multiple stages (retrieval, LLM, SQL/web search) — must still feel responsive, especially with streaming. |
| 3 | Reliability | High | ✅ | Depends on multiple external dependencies (LLM provider, web search API, DB) — must degrade gracefully rather than fail completely. |
| 4 | Security | High | ✅ | Internal data (SOPs, company analytics) is sensitive — must have access boundaries and not leak via web search or other exposure. |
| 5 | Maintainability | Medium | ✅ | 4 business units with continuously growing data — new KB documents and data sources must be addable without major redesign. |
| 6 | Usability | Medium | ❌ | Chat interfaces are now a familiar UX pattern (ChatGPT, Claude, etc.) — low design risk, doesn't need to be a driving goal. |
| 7 | Flexibility *(portability/scalability)* | Low–Medium | ❌ | No large-scale usage requirement in current scope; containerization already gives reasonable headroom without making it a dedicated goal. |
| 8 | Compatibility | Low | ❌ | No requirement yet to interoperate with other internal systems (e.g. Slack/Teams); single standalone chat interface for now. |
| 9 | Safety | Not applicable | ❌ | Concerns physical/safety-critical harm (e.g. medical, automotive) — not relevant to an internal chatbot. |

### 1.3 Stakeholders

Stakeholders are identified using the
[Rozanski & Woods stakeholder framework](reference/rozanski-woods-stakeholders.md)
rather than an open brainstorm. Architects instinctively think about
"users," but a system is shaped by far more people than whoever uses it
directly — the people who fund it, own the data it draws from, and are
legally accountable for it all have architectural concerns too. The
framework provides a fixed set of 11 stakeholder roles so none of them get
forgotten by default. For this project, several of the 11 roles collapse
onto the
same small team and were consolidated; one role (Data/Content Owners) was
added outside the original 11 because it's specifically relevant to a
RAG-based system. The full role-by-role mapping is in the reference notes
linked above — the table below is the applied result.

| Stakeholder | Description | Expectations |
|---|---|---|
| **Users** | Employees across MCN TV, MCN+, MCN+ Shorts, MCN News, and Group Functions | Fast, accurate answers without needing to search manually or write SQL themselves |
| **Data/Content Owners** | Business units that own the SOPs, documents, and data Nova retrieves from | Their content is represented accurately; sensitive data isn't exposed beyond its intended audience |
| **Platform/Engineering Team** | Builds, deploys, maintains, tests, and supports Nova (consolidates Developers, Maintainers, Production Engineers, Support Staff, System Administrators, Testers, and Communicators) | System stays maintainable and extensible as KB documents and data sources grow; observable enough to debug issues quickly |
| **External Providers** *(LLM provider, web search API, hosting/cloud infrastructure)* | External parties Nova depends on to function | *Not an expectation on the architecture — the reverse: the architecture must account for their limitations (rate limits, downtime, latency) as an external dependency.* |
| **Legal & Compliance** | Oversees data governance and regulatory conformance | Internal/sensitive data must not leak externally (e.g. via web search calls); access is auditable |
| **Group Management / Leadership** | Sponsors and funds Nova | Clear return on investment, high adoption, and no added security/legal risk from the investment |

---

## 2. Architecture Constraints

*(TODO)*

## 3. System Scope and Context

### 3.1 Business Context
*(TODO — C4 Context Diagram)*

### 3.2 Technical Context
*(TODO)*

## 4. Solution Strategy

*(TODO)*

## 5. Building Block View

### 5.1 Whitebox Overall System
*(TODO — C4 Container Diagram)*

### 5.2 Level 2
*(TODO — C4 Component Diagram, per container as needed)*

## 6. Runtime View

*(TODO — key scenarios: KB question, data analytics question, web search
fallback)*

## 7. Deployment View

### 7.1 Infrastructure Level 1
*(TODO — docker-compose topology)*

## 8. Cross-cutting Concepts

*(TODO — communication protocols, auth, caching strategy, observability,
MCP as the tool-calling layer)*

## 9. Architecture Decisions

*(TODO — one ADR per significant decision: backend, frontend, database,
cache, async worker/queue, MCP server, LLM provider, web search)*

## 10. Quality Requirements

### 10.1 Quality Tree
*(TODO — breakdown of Section 1.2 goals)*

### 10.2 Quality Scenarios
*(TODO)*

## 11. Risks and Technical Debt

*(TODO)*

## 12. Glossary

*(TODO)*

## 13. References

Not an official arc42 section — added to this document so every framework,
standard, and external source used while writing it is traceable in one
place.

- [arc42](https://arc42.org) — overall document structure/template
  ([full notes](reference/arc42.md))
- [C4 Model](https://c4model.com) — architecture diagramming (Context,
  Container, Component, Code) ([full notes](reference/c4-model.md))
- [ADR / Architecture Decision Records](https://adr.github.io/) — format for
  Section 9 decisions (Nygard template, adapted) ([full notes](reference/adr.md))
- [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) — quality
  characteristics used in Section 1.2 / Section 10
  ([full notes](reference/iso-25010.md))
- Rozanski, N. & Woods, E., *Software Systems Architecture: Working With
  Stakeholders Using Viewpoints and Perspectives* — stakeholder role
  categories used in Section 1.3
  ([full notes](reference/rozanski-woods-stakeholders.md))
