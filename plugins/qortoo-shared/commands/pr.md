---
description: Create a pull request for the current branch, optimized for squash-merge workflows.
---

## Steps

### Step 1 — Gather branch information

Run the following commands:
```
git log main..HEAD --format="%H %s"   # list commits ahead of main (subject only)
git log main..HEAD --format="%B"      # full commit messages with bodies
git status --short                    # check for uncommitted changes
```

If there are uncommitted changes, warn the user and stop.
If there are no commits ahead of main, stop and inform the user.

### Step 2 — Determine PR title and body

Because this repository uses **squash-merge**, the PR title and body become the final commit message on main. Structure them accordingly:

**Title**: The subject line of the single most significant commit among those ahead of main.
- "Most significant" means the one introducing the primary new capability or the largest behavior change.
- Use the same `<emoji><type>(<scope>): <description>` format as the commit convention.
- If there is only one commit, use its subject line directly.

**Body**: A bullet list built from all commits ahead of main:
- Start with the body of the most significant commit (the one used as title), if it has one.
- Then add one bullet per remaining commit using its subject line.
- Label the section clearly so reviewers understand the commit breakdown.

Example body structure:
```
<body of the primary commit, if any>

## Commits included
- <subject of commit 2>
- <subject of commit 3>
- ...
```

If there is only one commit, omit the "Commits included" section and use only its body.

### Step 3 — Push and create the PR

1. Check if the current branch has a remote tracking branch. If not, push it first:
   ```
   git push -u origin HEAD
   ```

2. Create the PR:
   ```
   gh pr create --title "<title>" --body "<body>"
   ```

3. Print the PR URL on success.

## Notes

- Target branch is always `main`.
- All content (title and body) must be in **English**.
- Do not push or create the PR until the user confirms the proposed title and body.
