# arc42 Structure (Reference)

Reference notes on the arc42 template, used as the skeleton for the
[Technical Design Document](../technical-design-document.md). Source:
arc42.org.

## Big Idea

Architecture documentation usually fails for one of two reasons: it's
unstructured (important concerns get forgotten) or it's over-templated
(teams give up because it's too heavy). arc42 solves this by being a
**fixed but lightweight checklist of concerns** — 12 sections that force you
to address requirements, context, decisions, runtime behavior, deployment,
and risk, without prescribing exactly *how* to write each one. It's a
skeleton, not a straitjacket: sections can be shallow or deep depending on
what the project actually needs, but none of them get skipped.

## Structure

arc42 defines **12 sections**. Each is listed below with its official
sub-sections (where arc42 defines them).

## 1. Introduction and Goals
- 1.1 Requirements Overview — essential functional requirements/goals
- 1.2 Quality Goals — top 3-5 quality goals, prioritized (commonly mapped to
  ISO/IEC 25010 quality characteristics)
- 1.3 Stakeholders — table of stakeholders and their expectations

## 2. Architecture Constraints
- Technical constraints, organizational constraints, conventions/standards
  that limit design freedom (no official sub-sections; usually one table).

## 3. System Scope and Context
- 3.1 Business Context — external communication partners from a
  domain/business perspective (who/what the system talks to, and why)
- 3.2 Technical Context — the same, but from a technical/protocol
  perspective (interfaces, channels)

## 4. Solution Strategy
- High-level summary of the fundamental decisions and solution approaches
  that shape the architecture (technology choices, top-level decomposition,
  approach to achieving top quality goals). No official sub-sections — acts
  as a bridge between Section 1 (goals) and the detailed views that follow.

## 5. Building Block View
- 5.1 Whitebox Overall System — level 1 decomposition (maps well to C4
  Container diagram)
- 5.2 Level 2 — zoom into individual building blocks (maps to C4 Component
  diagram)
- 5.3 Level 3 — further zoom if needed
(Repeatable/nested per building block — go only as deep as necessary.)

## 6. Runtime View
- A handful of concrete runtime scenarios (sequence/activity diagrams)
  showing how building blocks collaborate for important use cases.

## 7. Deployment View
- 7.1 Infrastructure Level 1 — overall deployment structure (nodes,
  environments)
- 7.2 Infrastructure Level 2 — detail per node if needed

## 8. Cross-cutting Concepts
- Concepts that apply across multiple building blocks: domain models,
  architecture/design patterns, security, communication protocols, error
  handling, logging/observability, etc. Usually organized as a set of
  sub-topics chosen per project (no fixed official sub-list).

## 9. Architecture Decisions
- Important, expensive, large-scale, or risky architecture decisions,
  including rationale. This is where ADRs (Architecture Decision Records)
  live — one ADR per significant decision, typically: Decision / Context /
  Alternatives Considered / Rationale.

## 10. Quality Requirements
- 10.1 Quality Tree — quality goals from Section 1.2 broken down into a
  tree of more specific quality attributes
- 10.2 Quality Scenarios — concrete, testable scenarios for each quality
  attribute (stimulus → response), used to validate whether the goal is met.

## 11. Risks and Technical Debt
- List of identified risks and/or known technical debt, with their
  potential consequences and mitigation.

## 12. Glossary
- Table of domain and technical terms used throughout the document, with
  definitions — keeps the document self-contained for any reader.

---

## Subsection summary (which sections are fixed vs. flexible)

| Section | Fixed sub-sections? | Detail |
|---|---|---|
| 1. Introduction and Goals | Yes (3, fixed) | 1.1 Requirements Overview, 1.2 Quality Goals, 1.3 Stakeholders |
| 2. Architecture Constraints | No | Single list/table, not split |
| 3. System Scope and Context | Yes (2, fixed) | 3.1 Business Context, 3.2 Technical Context |
| 4. Solution Strategy | No | Prose/list, not split |
| 5. Building Block View | Yes, but open-ended (nested) | 5.1 Whitebox Overall System, 5.2 Level 2, 5.3 Level 3 — depth depends on system complexity |
| 6. Runtime View | No fixed count | One sub-section per important runtime scenario, count varies |
| 7. Deployment View | Yes (2, extendable) | 7.1 Infrastructure Level 1, 7.2 Infrastructure Level 2 |
| 8. Cross-cutting Concepts | No fixed list | Split into project-chosen topics (e.g. security, persistence, communication) |
| 9. Architecture Decisions | No fixed count | One entry per ADR, count varies |
| 10. Quality Requirements | Yes (2, fixed) | 10.1 Quality Tree, 10.2 Quality Scenarios |
| 11. Risks and Technical Debt | No | Single list, not split |
| 12. Glossary | No | Single table, not split |

Only Sections **1, 3, 7, 10** have official fixed sub-sections. Sections **5,
6, 8, 9** are split dynamically (however many sub-items the project needs).
Sections **2, 4, 11, 12** are not split at all — content goes directly under
the section heading.

## Notes for this project

- Sections 1–3 define *what* and *why*; Sections 4–9 define *how*; 10–12 are
  validation/support material.
- C4 Model diagrams slot into Section 5 (Building Block View): Context
  diagram before/around Section 3, Container diagram in 5.1, Component
  diagram in 5.2.
- Not every project needs all 12 sections at full depth — arc42 is meant to
  be adapted. For this project, keep every section but scale depth to what's
  actually needed to explain the design.
