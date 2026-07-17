---
name: retro
disable-model-invocation: true
description: |
  Run a retrospective after finishing work and distill durable lessons into
  docs/solutions/ as concrete rules the next session can act on.
argument-hint: "[optional: one-line context about what just shipped]"
---

# retro

A conversation evaporates when context resets. This skill **distills** the durable lessons out of a finished task into `docs/solutions/` — turning volatile experience into a retrievable **rule**, so the next agent starts from what was learned instead of re-stepping the same traps.

A lesson worth keeping is a **rule**: a concrete behavior that changes a future action.

Good: "Before touching the auth middleware, run `scripts/auth-check.sh`."
Not a rule: "Be careful with auth."

## Steps

1. **Prepare the shelf.**
   Ensure `docs/solutions/` exists; create the directory structure if it does not. Search it for an existing entry on the same problem or module.
   *Done:* you have either found a sibling entry to match format, or confirmed the shelf is empty.

2. **Triangulate two sources.**
   - *Subjective* — the conversation: decisions, dead ends, surprises, the *why* behind choices.
   - *Objective* — `git log --oneline` and `git diff --stat`: what actually changed, and how big.
   Keep only what survives both. Git with no narrative is data without wisdom; narrative with no git is self-flattery.
   *Done:* every kept lesson is grounded in both what was said and what shipped.

3. **Distill into rules.**
   For each lesson, state it as a **rule** — a future action, not a maxim. Sort into two registers:
   - *What worked* — decisions that paid off, patterns worth repeating.
   - *What didn't* — dead ends, rework, surprises.
   *Done:* zero lessons read like advice; each names a concrete next action.

4. **Write the entry.**
   Save to `docs/solutions/<category>/<slug>.md`. Pick `<category>` from an existing sibling when possible; otherwise use the module or problem domain (e.g., `auth`, `performance`, `frontend`, `process`).

   Frontmatter:
   ```yaml
   ---
   title: <short sentence>
   date: YYYY-MM-DD
   problem_type: bug | knowledge | practice | decision
   module: <affected area>
   severity: low | medium | high
   tags: [<topic>, <topic>]
   ---
   ```

   Body by type:
   - `bug`/`problem` → What Didn't Work · Solution · Lessons Learned · Related
   - `knowledge`/`practice` → Context · Guidance · When to Apply

   Match the format of an existing sibling if one exists.
   *Done:* file written and conforms to a sibling where one exists.

5. **Close the retrieval loop.**
   Written but unfindable equals unwritten. If `AGENTS.md` or `CLAUDE.md` does not already point at `docs/solutions/`, add a one-line pointer telling future agents to search it first.
   *Done:* a path exists from a new session to this knowledge.
