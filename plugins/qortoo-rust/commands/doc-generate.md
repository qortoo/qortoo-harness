---
description: Run make doc to generate Rust API documentation and report all warnings or errors.
---

Steps:
1. Run `make doc` in the project root.
2. If it succeeds, report the success and mention that documentation is available via `cargo doc --open`.
3. If there are warnings, list each one with the file and line number so they can be fixed.
4. If it fails, diagnose the root cause and suggest fixes.

After running, also check for any public items that are missing doc comments by searching for `pub fn`, `pub struct`, `pub trait`, `pub enum` without a preceding `///` comment in `src/`. Report any undocumented public items found.
