---
description: Run all checks that must pass before committing, mirroring the CI pipeline and make lint.
---

## Steps

Run the following checks in order. Stop and report immediately if a step fails — do not proceed to the next step.

### Step 1 — Format check
```
cargo +nightly fmt --all --check
```
If this fails, ask the user whether to auto-fix with `cargo +nightly fmt --all` before continuing.

### Step 2 — Build check
```
cargo check --all-features --tests
```

### Step 3 — Clippy (warnings as errors)
```
cargo clippy --workspace --all-targets --tests --all-features -- -D warnings
```

### Step 4 — Tests
```
cargo test
```

## Output format

For each step, report:
- **PASS** — one line confirming it passed
- **FAIL** — the exact error output, the file and line number, and a concrete fix suggestion

At the end, print a summary:

```
Results: N/4 passed
```

If all 4 pass, confirm the branch is ready to commit.
If any fail, list only the failing steps with their fix suggestions.
