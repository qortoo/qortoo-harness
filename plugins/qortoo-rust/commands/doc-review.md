---
description: Review documentation completeness and accuracy for the Qortoo project.
---

This skill runs a two-part documentation review:

## Part 1: ./docs/ concept documents

Run `ls ./docs/` to discover all documentation files. For each file found:
1. Read the document to identify which source files it describes
2. Read the corresponding source files to verify accuracy
3. Report stale sections, missing diagrams, or inconsistencies

Focus verification on:
- Struct, trait, and method names and signatures
- Channel types and capacities
- State machine transitions and lifecycle flows
- Error handling paths and action mappings

Also flag **history that should be a principle**. A concept doc describes the system as it
is now and the rule that keeps it that way; it is not a changelog. Report passages that
narrate what was tried, removed, renamed, or discovered — "X existed and was removed",
"originally we used Y", "learned the hard way", "one run showed" — and propose the
timeless rewrite that keeps the rationale and drops the chronology. Measurements are the
exception when their conditions (date, machine, toolchain) are labelled.

## Part 2: Inline Rust doc comments

Scan `src/` for:
- Public items (`pub fn`, `pub struct`, `pub trait`, `pub enum`) missing `///` doc comments
- Korean comments that should be converted to English (per project convention: all comments must be in English)
- `//!` module-level docs missing from `mod.rs` or `lib.rs` files

## Output format

Report findings grouped by severity:
- **Critical** — stale facts or missing docs on core public APIs
- **Important** — significant gaps in `./docs/` concept files
- **Minor** — missing module-level comments or minor wording issues

Always provide the exact file path and line number, and include proposed replacement text where possible.
