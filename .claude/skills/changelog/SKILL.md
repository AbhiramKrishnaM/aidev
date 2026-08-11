---
name: changelog
description: Appends a short, timestamped entry to CHANGELOG.md summarizing recent repo changes (uncommitted diff, or the latest commits if the working tree is clean). Use when the user asks to update the changelog, log/record/track changes, or says something like "add this to the changelog" or "log what we just did".
---

# Changelog

Record what changed — briefly. A timestamp plus a few one-line bullets, never a narrative.

## Steps

1. Get an accurate timestamp — run it, don't guess:
   ```
   date "+%Y-%m-%d %H:%M"
   ```

2. Figure out what actually changed:
   - Uncommitted work present → `git status --short` and `git diff` (+ `git diff --cached`) to see it.
   - Working tree clean → summarize the most recent commit(s) not yet reflected in the changelog
     via `git log --oneline` (compare against the last entry's timestamp/commit to know where to
     stop).

3. Write **1–5 bullets max**, each a single short line, plain past tense ("Removed X", "Added Y",
   "Fixed Z"). No sub-bullets, no code blocks, no restating the full diff, no editorializing.

4. Open `CHANGELOG.md` at the repo root. If it doesn't exist, create it with just `# Changelog` as
   the first line.

5. Insert the new entry directly below the top-level heading (newest entries first):

   ```markdown
   ## 2026-08-11 14:32
   - Removed the Ollama-only implementation; provider registry is now empty pending the pivot
   - Rewrote README/docs to describe cloud-provider setup instead of Ollama
   ```

6. Do not commit the change — leave staging/committing to the user unless they explicitly ask.

## When not to add an entry

If nothing has changed since the last entry (clean tree, no new commits), say so instead of
inventing a filler entry.
