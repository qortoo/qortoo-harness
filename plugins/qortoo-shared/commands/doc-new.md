---
description: Create a new concept document under ./docs/ for a Qortoo architectural concept.
---

$ARGUMENTS contains the concept name (e.g., "connectivity", "error-handling", "handler-system").

## Steps

1. Ask the user which concept to document if $ARGUMENTS is empty.
2. Identify all relevant source files for the concept by searching the source tree.
3. Read those files to extract the actual behavior, types, and relationships.
4. Create `docs/<concept-name>.md` following the structure below.
5. Add a reference to the new file in `docs/architecture.md` if appropriate.

## Document structure

Every concept doc must follow this template:

```markdown
# <Concept Name>

Brief one-paragraph overview of what this concept is and why it exists.

## Overview

High-level description with a Mermaid diagram showing the main components and their relationships.

\`\`\`mermaid
graph TD
  ...
\`\`\`

## Core Types

Table or list of the key structs/traits/enums involved, each with a one-line purpose.

## How It Works

Step-by-step walkthrough of the main flow, referencing actual source file paths.

## Key Design Decisions

Bullet list of non-obvious design choices and the reasons behind them (the "why").

## Related Concepts

Links to other `./docs/` files that are closely related.
```

## Conventions

- All content must be in **English**.
- Diagrams should use Mermaid (`graph TD`, `sequenceDiagram`, etc.) so they render on GitHub.
- Reference source files by path relative to the repo root (e.g., `src/path/to/file.rs`, `internal/path/to/file.go`).
- Explain the "why" behind design decisions, not just the "what".
- Keep it code-grounded: quote actual type names, method names, and field names from the source.
- **Write principles, not history.** Describe the system as it is now and the rule that
  holds it in place. Leave out what was tried before, what was removed, what a past
  measurement happened to show, or what was "learned the hard way" — git history and the
  plan documents already carry that, and in a concept doc it ages into noise.
  - Rationale is a principle and belongs here; chronology is not.
    - Yes: "Transports live in the core because a Go-implemented one is the riskiest
      FFI surface (per-sync callbacks, cross-allocator ownership)."
    - No: "A Go transport path existed and was removed as speculative in Phase 6."
  - Prefer the present tense and a timeless subject. If a sentence only makes sense to
    someone who watched the work happen, rewrite it.
  - Measurements and version-specific facts are the exception: keep them, but label the
    conditions (date, machine, toolchain) so a reader can tell when they went stale.
