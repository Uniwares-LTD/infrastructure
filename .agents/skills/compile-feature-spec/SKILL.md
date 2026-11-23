---
name: compile-feature-spec
description: "Produces bounded specs, PRDs and implementation plans without implementing the change. Use when consequential requirements are unclear, a medium or large task needs planning, or the user asks to scope, spec or plan work; not for obvious small changes or casual questions."
---

Use the task's existing Handbook path and full revision. Only if no baseline is
recorded, run `npm run handbook:check` (or `node scripts/handbook.mjs check`).
Read `docs/bootstrap.md`, `docs/work-policy.md` and
`.agents/skills/compile-feature-spec/SKILL.md` with `git -C PATH show REVISION:FILE`.
Read this project's guidance, source map and preferences declared in `handbook.json`.
Resolve all shared references at that same revision; use `resources --revision SHA`
through the launcher for filesystem assets. Never substitute the mutable checkout.
Retain path/revision in handoffs and resume summaries. If lost, recover from context
first; otherwise establish a new baseline and report the discontinuity.
If unavailable, continue under local guidance and pause only dependent decisions.
<!-- handbook-managed:a8cc5bd0167dab1e34c07f7a12cdf2e8fb5ccfecda5d47b2714b27a7e0bd6605 -->
