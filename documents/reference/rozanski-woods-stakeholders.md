# Rozanski & Woods — Stakeholder Framework (Reference)

Reference notes on the stakeholder categorization from Nick Rozanski and
Eoin Woods' book *Software Systems Architecture: Working With Stakeholders
Using Viewpoints and Perspectives*, used for
[Section 1.3](../technical-design-document.md) (Stakeholders) of the
Technical Design Document.

## Big Idea

Architects instinctively think about "users," but a system affects and is
shaped by far more people than whoever clicks the buttons — the people who
fund it, deploy it, support it, and are legally accountable for it all have
architectural concerns too, and those concerns often conflict. Rozanski &
Woods' core idea is that architecture description should be organized
around **stakeholder viewpoints** rather than one monolithic diagram, and
that you can't know which viewpoints matter until you've deliberately
enumerated who the stakeholders actually are — using a fixed set of roles
so nobody gets forgotten by default (e.g. security officers, support staff,
or whoever pays for the system, roles that are easy to overlook next to
"the user").

This stakeholder list is one piece of their larger **Viewpoints and
Perspectives** methodology:
- **Viewpoints** — ways of describing the architecture tailored to a
  specific stakeholder group's concerns (parallels arc42 Section 1.3).
- **Perspectives** — cross-cutting quality concerns like performance,
  security, availability that apply across all viewpoints (parallels
  ISO 25010 / arc42 Section 1.2).

## The 11 stakeholder roles

| Role | Concerned with |
|---|---|
| Acquirers | Overseeing procurement/funding of the system |
| Assessors | Overseeing conformance to standards and legal regulation |
| Communicators | Explaining the system via documentation and training |
| Developers | Constructing and deploying the system |
| Maintainers | Managing the system's evolution once operational |
| Production Engineers | Designing/deploying/managing the build, test, and run environments |
| Suppliers | Building/supplying the hardware, software, or infrastructure the system runs on |
| Support Staff | Supporting users once the system is running |
| System Administrators | Running the system once deployed |
| Testers | Testing the system for suitability |
| Users | Defining functionality and ultimately using the system |

## How it's meant to be used

The source material gives two guiding principles rather than a rigid
procedure:
1. **Comprehensive representation** — make sure both non-technical
   stakeholders (acquirers, users) and technical ones are represented, not
   just whoever is easiest to talk to.
2. **Conflict management** — when stakeholder needs conflict, the architect
   must consciously balance and prioritize them, not let the loudest voice
   win by default.

No official step-by-step method is prescribed for smaller teams. For this
project, the roles were applied as: go through all 11, decide per role
whether it's applicable, and if applicable, whether it maps to an existing
team/role or needs its own row — consolidating roles that collapse onto the
same people on a small team (see TDD Section 1.3 for the applied result).

## Notes for this project

- Used in TDD Section 1.3 (Stakeholders). Not every role maps to a distinct
  person/team on a project this size — several roles were consolidated into
  one "Platform/Engineering Team" stakeholder.
- One role outside the original 11 was added for this project:
  **Data/Content Owners** (the business units that own the SOPs/documents
  and data Nova retrieves) — relevant here specifically because Nova is a
  RAG-based system, and its "Groundedness" quality goal (Section 1.2)
  directly depends on the quality of that source content.

Sources:
- [Software Systems Architecture — Stakeholders](https://www.viewpoints-and-perspectives.info/home/stakeholders/)
