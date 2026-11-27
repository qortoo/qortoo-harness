# Technical writing

Use this guide for public API documentation and shared repository documentation.
Follow the target repository's conventions for placement, formatting, and checks.

## Audience and evidence

- Identify the reader and what they need to do or understand. Use a tutorial to
  teach, a how-to guide to complete a task, a reference to look up a contract, and
  an explanation to describe a model and its rationale.
- Check the current implementation, exported APIs, tests, and relevant concept
  docs before stating a guarantee. Check feature gates and supported versions
  where they affect the reader. Surface disagreements about the intended contract
  with specific evidence so maintainers can resolve them.
- Write in English. Use the same terms across APIs, examples, and guides. Define
  unfamiliar terms where readers first need them and use exact identifiers where
  they help readers find the implementation.
- Define shared concepts and intended behavior in the relevant concept doc.
  Link to that contract from related pages and API docs, and explain the
  information needed at each point of use.
- Describe current behavior and the rationale for non-obvious rules. Keep
  development chronology in plans or change records. Label measurements and
  version-specific statements with the applicable conditions.

## Public API reference

- Start with a short summary of what the API does. For Rust, use `///` for
  exported items, `//!` for useful crate or module overviews, and intra-doc links
  for related items. Follow re-exports and feature gates to see what callers can use.
- Explain what callers cannot infer from the signature. Cover relevant input
  constraints, defaults, return values, absent data, side effects, and state
  after failure. Use Rustdoc's `# Errors`, `# Panics`, or `# Safety` sections when
  their contracts apply. Use other headings when they improve navigation.
- Give comparable operations comparable coverage. For example, when a mutation
  can return a previous value, explain when that value is present and what
  happens when the operation fails.
- Show non-trivial usage with a minimal, executable example. Use a doctest for
  Rust examples where practical. Link to a representative type-level or workflow
  example when it already shows the same operation.

## Repository guides and concept docs

- Put concept docs under `docs/` using the target repository's naming and index
  conventions. Explain the concept and its scope, then describe its components,
  responsibilities, rules, limits, and representative behavior. Include failure
  or recovery cases where they help readers apply the rules.
- Explain why non-obvious rules hold. Link to the main implementation and tests
  as evidence. Use a Mermaid diagram when it clarifies a relationship or flow.
- Give task guides the prerequisites, actions, and expected outcome. Keep
  architecture in the repository's architecture or concept docs. Use `AGENTS.md`
  for repository instructions and links to their sources.

## Verification

Use the checks available in the target repository. For qortoo-rs, check Markdown
links with `make check-docs` and changed diagrams with `make check-mermaid`. For
Rust API changes, use the repository's rustdoc build and doctest commands with
the relevant feature combinations. Use CI's broken intra-doc link check when
verifying links. Report what ran and any material gaps in verification.

## References

- [Rust API Guidelines on documentation](https://rust-lang.github.io/api-guidelines/documentation.html)
- [Rustdoc Book on writing documentation](https://doc.rust-lang.org/rustdoc/how-to-write-documentation.html)
- [Google developer documentation style guide](https://developers.google.com/style)
- [Diátaxis documentation framework](https://diataxis.fr/)
