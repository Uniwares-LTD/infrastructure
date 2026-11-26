# Infrastructure guidance

<!-- handbook-session-contract:start -->

## Session contract

Apply before the first action of every request. The full rules are the Handbook's
`docs/guidance/communication.md` at the task revision.

- Start: run the Handbook check, then read every file it lists in `mustRead`.
- Workflow: choose the skill for each request and load it in this session before its
  first action. Choose again when a lookup turns into writing, creating, issue changes
  or publishing. Naming a skill without loading it does not count. Routes: guide or
  runbook → maintain-docs; issue create, update or comment → manage-issues; implement,
  commit or PR → work-on-task; plan or spec → compile-feature-spec; review →
  review-change. Casual questions and read-only lookups need no skill.
- Replies: a brief or decision for a person leads with the outcome, then the applicable
  headings in this order: Information, Decisions made, Verification, ⛔ Blockers,
  ❓ Questions for you, ✋ Approval needed, Suggested next actions, Where to look.
  A single question or approval opens with that heading. Casual answers and agent
  handoffs need no headings.
- Authority: pushes, PRs, merges, releases, deployments, new issues and access or
  project configuration changes need explicit approval for that action; commits follow
  the repository adapter.

<!-- handbook-session-contract:end 0fdd1f99e0a6638388946f611075cd41a139139f5aaa17f3dc4e2b50f5335f5f -->

- Guided application initialization is documented in Unibase's deployment guide;
  follow its current automation/manual boundaries. Review a concrete immutable
  operator batch before installation. Provider operation markers represent uncertain
  outcomes until readback; never retry a create blindly or replace generated keys.

- For new deployment handoff, prompt the user to retrieve files from the secure
  **Credentials** channel and supply a protected local directory reference. Follow
  [the exact filename/reuse map](docs/provider-access.md); validate structure without
  displaying values, collect missing access references together, and keep public
  host/provider configuration in docs or app JSON rather than secret handoff files.

- Every publication PR states `Operator intervention: none` or lists actions, owner,
  execution location, ordering, verification and failure/resume. Distinguish image
  releases from host/control/provider changes.
- Use [the named credential inventory](docs/provider-access.md) for new deployments.
  Collect missing protected references together, read only necessary exports and
  never print values. Public app settings use tracked JSON, not Actions variables.
  Preserve existing names; distinguish installed behavior from proposed automation.

- Read [the inventory](docs/inventory/srv1.md), [architecture](docs/architecture.md),
  [operations](docs/operations.md) and [implementation plan](docs/implementation-plan.md)
  before infrastructure work. Revalidate time-sensitive observations before applying changes.
- Choose the operations runbook's existing-installation or new-installation path. Record execution location, owner,
  reviewed revision, verification and next action. Stop dependent live steps at
  `implementation required`; never invent a command for tooling that does not exist.
  Reuse verified discovery, collect missing inputs together and resume partial setup
  after inspecting state. Do not blindly repeat successful mutations. Keep existing
  app workers/Redis/Nginx for initial staging; shared services and job refactors are
  later milestones, not implicit first-release prerequisites.
- Label observed state, accepted preferences, recommendations and unresolved checks.
  A package candidate, passing local check or published document is not live acceptance.
- Generate operator instructions from repository configuration, canonical inventory,
  owner-repository contracts and verified session evidence first. Use known non-secret
  hosts, users and paths in complete commands for the stated shell/location, citing
  their source. Ask for missing consequential inputs together, not values already
  recorded. Distinguish configuration from live verification; never guess credentials,
  host fingerprints, transport authorization or network allocations.
- For new operator devices, follow the shared-key handoff in operations.md. Reuse
  the installed admin key named `srv1-ops-admin` through the owner's secure channel.
  Windows recipients save it as `$env:USERPROFILE\.ssh\uniwares-ops-admin` and use
  the runbook's complete connection command; the key name is not an SSH profile.
  Never request private
  key contents in chat or Git. Verify the documented host fingerprint on each device.
  Shared admin login does not establish unattended sudo or routine deploy authority.
- Preserve existing services and their owners. Tunnel/Dify/Booklet ownership remains
  with agentic-poc until a separately reviewed transfer. Do not apply competing
  Terraform configurations or replace a complete tunnel route list from an app repo.
- Use the user's authorized scope. Documentation work does not authorize provisioning,
  deployment, service restarts, data deletion, credential rotation or spending.
- Never commit credentials, private runtime files, Terraform state/plans, raw logs,
  database dumps or raw operator transcripts. Record credential metadata only.
- Prefer logical application boundaries, standard Compose and reusable templates.
  Use repository Actions concurrency and documented coordination for shared changes;
  avoid creating a cross-repository orchestration system without a demonstrated need.
- Keep initial privileged administration separate from routine deployment. The target
  restricted deploy user has neither general sudo nor Docker-group membership.
- Preserve application leases, idempotency and financial records when simplifying
  scheduling. Host coordination does not replace application correctness mechanisms.
- Keep current shared progress in operations.md and application acceptance in its
  deployment guide. Link instead of copying changing facts. Completed bootstrap
  procedures/history are reference material, not commands to rerun. Reuse prior
  unaffected-service evidence unless a new shared-host change warrants checking it.
- Update canonical docs with verified changes and link to application guidance.
  Run relevant checks and perform a separate read-only review before publication.
- `main` is this repository's default branch. Application release branches and
  environment names belong to their own contracts; do not copy Booklet's `master`
  convention into Unibase.

## Shared Handbook

Run `npm run handbook:check` (or `node scripts/handbook.mjs check`) at task start.
Read the returned committed bootstrap/work policy and relevant skills with git show.
Use [.agents/repository-adapter.md](.agents/repository-adapter.md),
[docs/source-map.md](docs/source-map.md), preferences and selected skills in handbook.json.
Follow shared GitHub access routing: plain Git, working capable MCP, then gh.
Run Git/gh and helpers that invoke them outside the sandbox from the first attempt.
Cached guidance is usable; preserve non-main or dirty Handbook checkouts. No version
pin or scheduler is installed. Carry the task baseline through handoffs.
After skill/routing changes explicitly run handbook:sync and handbook:entrypoints;
preserve custom instructions. Use project-owned permissive templates in .github and
docs/templates. Adoption never authorizes publication or live host changes.
