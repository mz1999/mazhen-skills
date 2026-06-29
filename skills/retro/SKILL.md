---
name: retro
disable-model-invocation: true
description: Retrospective after a feature — distills lessons from the conversation and the git trail into docs/solutions/, so the next session starts on prior hard-won knowledge instead of rediscovering it.
argument-hint: "[optional: brief context about what was completed]"
---

# retro

A conversation evaporates the moment its context resets. This skill **distills** the durable lessons out of a finished task into `docs/solutions/` — turning volatile experience into a retrievable asset, so the next agent (or you, next session) starts from what was learned rather than re-stepping the same traps.

A lesson worth keeping is a **rule** — a concrete behavior that changes a future action ("before touching X, check Y"), not a maxim ("be careful with X"). State it as a rule, or it isn't ready to keep.

## Steps

1. **Search before creating.** Look in `docs/solutions/` for an existing entry on the same problem. *Done:* you've either found one to update, or confirmed the shelf is empty.

2. **Triangulate two sources.**
   - *Subjective* — the conversation: decisions, dead ends, surprises, the *why* behind choices.
   - *Objective* — `git log --oneline` and `git diff --stat`: what actually changed, and how big.
   Keep only what survives both. Git with no narrative is data without wisdom; narrative with no git is self-flattery. *Done:* every kept lesson is grounded in both what was said and what shipped.

3. **Sort into two registers, each as a rule.**
   - *What worked* — decisions that paid off, patterns worth repeating.
   - *What didn't* — dead ends, rework, surprises.
   *Done:* zero lessons read like a maxim; each names a concrete future action.

4. **Write the entry** to `docs/solutions/<category>/<slug>.md`. Frontmatter: `title`, `date` (YYYY-MM-DD), `problem_type`, `module`, `severity`, `tags`. Body by type:
   - bug/problem → What Didn't Work · Solution · Lessons Learned · Related
   - knowledge/practice → Context · Guidance · When to Apply
   Match the format of an existing sibling if one exists. *Done:* file written and conforms to a sibling where one exists.

5. **Close the retrieval loop.** Written but unfindable equals unwritten. If the project's `AGENTS.md` / `CLAUDE.md` doesn't point at `docs/solutions/`, suggest a one-line pointer so future agents know to search it. *Done:* a path exists from "new session" to "this knowledge".
