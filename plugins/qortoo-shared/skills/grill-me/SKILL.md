---
name: grill-me
description: Guide a user through code changes with one evidence-based question at a time to clarify their understanding and intended behavior.
---

# Grill Me

Adapted from [Matt Pocock's grill-me and grilling skills](https://github.com/mattpocock/skills/tree/main/skills/productivity). This version focuses on understanding code changes together.

- Inspect the requested changes and relevant surrounding code first, including uncommitted changes when requested. Resolve factual questions from the code instead of asking the user to guess.
- Present a short, relevant code or diff excerpt with a clickable file and line link. Explain its apparent behavior and ask one concrete question about its meaning or intended behavior. Define ambiguous terms and distinguish observed behavior from assumptions.
- Wait for the answer, incorporate it, and follow up on dependent decisions one at a time. Do not silently treat an interpretation as an agreed decision.
- When the questions are resolved, summarize the agreed understanding and any open points. Do not change the code unless the user requests it.
