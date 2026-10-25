# Infrastructure guidance

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
- Follow the operations runbook's three-phase order. Record execution location, owner,
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
