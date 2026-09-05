---
description: Create a new concept document under ./docs/ for a Qortoo architectural concept.
---

$ARGUMENTS contains the concept name (e.g., "connectivity", "error-handling", "handler-system").

## Purpose and authority

Concept docs are the single source of truth for intended behavior and contracts.
Write for developers learning the system and AI agents implementing or verifying it:
explain the model in plain language and state its rules precisely.

- Define each rule in one canonical document; link to it elsewhere instead of duplicating it.
- Code implements the contract, and tests verify it. Source links do not replace the contract's explanation.
- Keep canonical docs, implementation, and tests aligned when behavior changes.
- Surface conflicts between docs and code; do not silently reconcile them or present inferred intent as fact.

## Steps

1. Ask the user which concept to document if $ARGUMENTS is empty.
2. Find existing concept docs, relevant source files, and tests; identify where related rules are already defined.
3. Read them to compare documented contracts with actual behavior, types, and relationships. Report discrepancies and unresolved intent to the user rather than inventing a contract or changing code as part of documentation work.
4. Create `docs/<concept-name>.md` using the coverage requirements and adapting the suggested structure below.
5. Add a reference to the new file in `docs/architecture.md` if appropriate.
6. Review required rules for clarity and consistency with their canonical definitions, implementation, and tests; report any remaining gaps.

## Document structure

Every concept doc must explain its definition and scope, core rules and boundaries,
intended behavior, and implementation evidence. Explain the rationale for non-obvious
rules and choices where it is supported by the code or existing documentation.

Choose headings and their order to fit the concept. The following is a starting
point, not a required set of sections: rename, merge, or omit sections while
preserving the required coverage. Introduce the model before implementation details;
type inventories and diagrams are optional and should help understanding or navigation.

```markdown
# <Concept Name>

Brief one-paragraph definition of what this concept means, why it exists, and where it applies.

## Model

Define the terms, responsibilities, relationships, and boundaries needed to understand the system.
Add a diagram when it clarifies those relationships.

## Rules and Guarantees

State verifiable rules: the applicable conditions, responsible component, required outcome,
and relevant exceptions. Include invariants and limits on guarantees.

## Behavior

Show how the rules apply in representative scenarios, with inputs, outcomes, and state changes.
Use flows, state transitions, or examples as appropriate, including failure behavior when relevant.

## Rationale

Why the non-obvious rules and boundaries exist, including current tradeoffs.
Describe principles, not development history.

## Code Map

Link to the main code locations that implement the rules and existing tests that verify them.
Include responsibilities and actual types where useful; avoid exhaustive inventories.

## Related Concepts

Links to other `./docs/` files that are closely related.
```

Examples of topic-specific organization:

| Concept | Useful organization |
| --- | --- |
| Processing flows, such as connectivity or synchronization | Components → lifecycle → normal flow → failure and recovery |
| Policies, such as error handling | Classification model → propagation and conversion rules → handling examples → rationale |
| Constraints, such as ownership or consistency | Model → invariants → allowed and forbidden behavior → enforcement points in code |

## Conventions

- All content must be in **English**.
- Introduce definitions and context before detailed rules; use concrete examples to aid understanding.
- Use consistent terminology across docs and code, and distinguish requirements, recommendations, and illustrative examples.
- Diagrams should use Mermaid (`graph TD`, `sequenceDiagram`, etc.) so they render on GitHub.
- Reference source files by path relative to the repo root (e.g., `src/path/to/file.rs`, `internal/path/to/file.go`).
- Explain the "why" behind design decisions, not just the "what".
- Keep explanations grounded in code while prioritizing readability. Use clear conceptual
  terms in prose; introduce exact code identifiers when first mapping a concept to its
  implementation or when precision requires them. Put detailed identifier mappings in
  the Code Map rather than repeating them throughout the text.
- **Write principles, not history.** Describe current behavior, rules, and rationale in
  the present tense; omit development chronology and abandoned approaches.
  Label measurements and version-specific facts with their relevant conditions
  (date, machine, toolchain, version).
