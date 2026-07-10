# C4 Model (Reference)

Reference notes on the C4 model, used for the architecture diagrams in the
[Technical Design Document](../technical-design-document.md). Source:
c4model.com.

## Big Idea

Most architecture diagrams fail because they mix zoom levels — a single
diagram trying to show both "what talks to what across the org" and "which
class calls which method" ends up unreadable and stale within a week. C4's
core idea is borrowed from mapping: like Google Maps lets you zoom from
country → city → street → building, C4 defines a **fixed set of zoom
levels** for software architecture, each with its own vocabulary and
audience, so every diagram answers exactly one question at exactly one
altitude. You never mix levels in a single diagram, and you never need more
notation than boxes, lines, and labels.

## What it is

C4 is **not** a document template like arc42 — it's a lightweight, hierarchical
set of **diagram types** for visualizing software architecture at different
zoom levels. "C4" = **C**ontext, **C**ontainer, **C**omponent, **C**ode. Each
level zooms further into the previous one, for different audiences.

## The 4 levels

### Level 1 — System Context Diagram
The zoomed-out view: the system as a single box, plus the people (users) and
other software systems it interacts with. No internal detail. Audience:
anyone (technical or non-technical) who needs the big picture.

### Level 2 — Container Diagram
Zooms into the system to show its **containers** — separately
deployable/runnable units (e.g. web app, API service, database, message
queue, mobile app). Shows how containers communicate (protocols,
interfaces). Audience: technical people (devs, ops) who need to understand
overall shape and technology choices.

### Level 3 — Component Diagram
Zooms into a single container to show its internal **components** (e.g.
controllers, services, repositories) and how they interact. Audience:
developers working within that container.

### Level 4 — Code Diagram
Zooms into a single component to show classes/objects (e.g. a UML class
diagram). Rarely produced by hand — usually generated from code via IDE
tooling if needed at all. Most projects stop at Level 3.

## Supplementary diagrams

C4 also allows optional supplementary diagrams when useful:
- **System Landscape** — even more zoomed out than Context, showing multiple
  systems across an organization.
- **Dynamic Diagram** — shows a specific runtime scenario/collaboration
  (similar role to arc42's Runtime View).
- **Deployment Diagram** — maps containers onto infrastructure (similar role
  to arc42's Deployment View).

## Notes for this project

- C4 diagrams are the visualization layer that fills in arc42's structural
  sections — see [arc42.md](arc42.md):
  - Context Diagram → arc42 Section 3 (System Scope and Context)
  - Container Diagram → arc42 Section 5.1 (Building Block View, level 1)
  - Component Diagram → arc42 Section 5.2 (Building Block View, level 2)
  - Dynamic Diagram → arc42 Section 6 (Runtime View), if a diagram is needed
    alongside the scenario description
  - Deployment Diagram → arc42 Section 7 (Deployment View)
- For this project, Code Diagram (Level 4) is very unlikely to be needed —
  the system isn't complex enough at the class level to warrant it.
- Diagrams should always be annotated/explained in prose, not left to speak
  for themselves — a diagram without explanation doesn't satisfy the test's
  requirement to explain design decisions explicitly.

Sources:
- [Home | C4 model](https://c4model.com/)
- [What Is the C4 Model for Visualizing Software Architecture? | Baeldung](https://www.baeldung.com/cs/c4-model-abstraction-levels)
