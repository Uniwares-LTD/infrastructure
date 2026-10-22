# Infrastructure guidance

- Read [the inventory](docs/inventory/srv1.md), [architecture](docs/architecture.md),
  [operations](docs/operations.md) and [implementation plan](docs/implementation-plan.md)
  before infrastructure work. Revalidate time-sensitive observations before applying changes.
- Follow the operations runbook checkpoint order. Record execution location, owner,
  reviewed revision, verification and next action. Stop dependent live steps at
  `implementation required`; never invent a command for tooling that does not exist.
  Reuse verified discovery, collect missing inputs together and resume partial setup
  after inspecting state. Do not blindly repeat successful mutations.
- Label observed state, accepted preferences, recommendations and unresolved checks.
  A package candidate, passing local check or published document is not live acceptance.
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
- Update canonical docs with verified changes and link to application guidance.
  Run relevant checks and perform a separate read-only review before publication.
- `main` is this repository's default branch. Application release branches and
  environment names belong to their own contracts; do not copy Booklet's `master`
  convention into Unibase.
