---
description: Run make doc to generate Rust API documentation and report warnings or errors.
---

1. Run `make doc` in the project root.
2. Report whether it succeeded and list warnings or errors with file and line
   when available. If it failed, identify the cause and suggest a fix.
3. Use `qortoo-harness/policies/technical-writing.md` to check the generated public
   API for missing documentation. Follow re-exports and feature gates so the
   report reflects the public surface for the build.
