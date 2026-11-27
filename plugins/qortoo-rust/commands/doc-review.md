---
description: Review Qortoo Rust API documentation and repository docs for completeness and accuracy.
---

Use the `qortoo-rust:documentation-reviewer` agent to review the requested scope.
Use the current diff to locate affected API and repository docs when no scope is
specified. If there is no diff and no scope is specified, review the public
Rustdoc and the repository's concept docs.

If the agent is unavailable, follow
`qortoo-harness/policies/technical-writing.md` directly and report prioritized
findings with file and line, the impact on the reader, and a concrete correction.
