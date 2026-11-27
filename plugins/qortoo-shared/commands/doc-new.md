---
description: Create a new concept document under ./docs/ for a Qortoo architectural concept.
---

1. Use `$ARGUMENTS` as the concept name. Ask the user for the name if it is missing.
2. Read `qortoo-harness/policies/technical-writing.md` and inspect the repository's
   existing concept docs, implementation, and tests. Identify the canonical
   location of related rules and surface discrepancies in the intended behavior.
3. Create `docs/<concept-name>.md` following the repository conventions. Shape
   the document around the reader's needs and cover the concept doc content in
   the shared guide.
4. Link to the doc from the repository's existing documentation index or
   architecture overview where appropriate. Run the relevant docs checks and
   report any unresolved issues.
