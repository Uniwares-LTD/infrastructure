# Shared infrastructure implementation plan

Use [host operations](operations.md) for the appropriate routine, first-installation,
protected-update or recovery procedure. [Inventory](inventory/srv1.md) owns installed
host identities and dated capacity; [Unibase's deployment guide](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md#current-staging-release)
owns serving release identities and application acceptance.

October 31 controller/maintenance installation, configuration correction and routine
staging release/check are verified. Earlier October 25 account and Dify/MCP/Persona
acceptance is historical evidence, not a fresh check of the current release. Dify
functional acceptance for the corrected permissions remains pending. Guided initialization
has synthetic coverage; fresh derived-provider write acceptance and secure-channel
credential-storage confirmation remain outstanding.

Completed bootstrap procedures are [historical references](history/completed-bootstrap-2026-10-25.md),
not a checklist to repeat. The [preparation package](staging-preparation.md) preserves
the reviewed first-installation scope. Avoid duplicating release IDs and test logs here.

## First deployment

1. **Connect and prepare.** Establish protected admin access, complete only required
   discovery and collect missing inputs together. Prepare reviewed restricted deploy
   operations, GitHub Free repository secrets, public image pulls, shared staging
   Firebase bindings, Compose compatibility and non-overlapping app networking.
2. **Bootstrap and deploy.** Preview/apply the authorized shared-account and app setup.
   Add a reviewed owner-side tunnel route to the app's existing private Nginx.
   Adapt route verification without building a generic registration platform.
   One release workflow builds, publishes, verifies anonymous digest pull, deploys
   and checks health. Keep existing workers and app Redis.
3. **Verify and hand off.** Complete app login/session acceptance, readiness and current worker checks.
   Reuse the completed shared-host baseline unless new changes affect it. Record release identity, routine workflow instructions and deferred work.
   A failed first release stops only its candidate/workers and any candidate timers;
   preserve data/configuration. No imaginary prior-release or DB rollback.

[Unibase's plan](https://github.com/Uniwares-LTD/unibase/blob/main/docs/implementation-plan.md)
owns application changes. Phase 3 and later recovery retain separate acceptance. Authorization
covers a concrete reviewed scope; unexpected destructive changes require reassessment.

## First-release acceptance

- Working staging hostname/login and current web/dependency/worker health, with
  optional Dify, Stripe and MCP disabled.
- Existing Booklet, Dify and legacy services unaffected; app subnet/port do not
  conflict with Docker, host or VPN routes.
- Restricted deployment user can perform allowed operations without general sudo,
  Docker-group membership or arbitrary root-owned configuration/script execution.
- Public image is pulled anonymously by immutable digest before candidate activation;
  builds exclude runtime secrets and retained configuration matches the release.
- Existing app Redis remains private and separate from Dify. Workers retain durable
  retry, lease, accounting and duplicate-prevention behavior.
- Recovery limitations are explicit. Initial success does not claim off-host recovery
  or rollback rehearsal that has not occurred.

## Later consolidation and recovery

- [ ] Automate derived setup and restricted runtime-secret restoration using the
  [credential inventory](provider-access.md). Require destination identity validation,
  bounded root-owned installation, secret-safe preview/output, atomic missing-file
  restoration, conflict refusal and interruption/resume checks. Define proposed
  Actions secret names with implementation; current runtime files are host-installed.

- [ ] Introduce the shared gateway with equivalent Firebase helper, streaming and
  trusted-proxy handling; remove per-app ingress/subnet requirements afterward.
- [ ] Introduce shared application Redis with allocated logical databases; keep Dify's
  Redis separate and adapt app validation/readiness before switching.
- [ ] Extract authenticated bounded AI/events/maintenance endpoints and systemd timers;
  preserve existing job safeguards and replace worker health before removing containers.
- [ ] Complete production-to-prod naming compatibility before production activation,
  preserving retained release snapshots and framework NODE_ENV=production.
- [ ] Implement minimum manual backup/restore with verified off-host encryption,
  retention and workflow-only permissions. Rehearse MongoDB/GridFS restoration before
  treating staging data as recoverable; backup before destructive changes/migrations.
- [ ] Rehearse image/config rollback when a real compatible previous release exists;
  do not create a release solely to satisfy a runbook checkpoint.
- [x] Implement Unibase image retention and verify the authorized initial cleanup.
- [ ] Activate automatic policy/timer only after the separate acceptance and authorization.
- [ ] Evaluate legacy public gateway, Dify/tunnel ownership transfers, Engine upgrades and production separately.

## Remaining decisions

First-deployment preparation has selected the dispatcher, existing provider bindings,
hostname, private listener and candidate subnet/Compose versions; see the preparation
package. Root installation, Compose/Buildx compatibility, provider writes and the
owner route are verified. Application release/acceptance evidence belongs to the
application deployment guide; do not infer live health from successful preparation.

For later work: shared network/gateway design, shared Redis location/database allocation,
job endpoint/timer interfaces, off-host destination/retention/encryption recovery and
required restore actions, production recovery objectives and migration ownership.
Do not resolve later decisions by blocking unrelated first-release work.

## Accepted deployment reliability and Handbook adoption

The accepted change separates three outcomes: Infrastructure Handbook adoption,
Infrastructure read-only preflight/safe diagnostics, and Unibase release integration.
Local adoption preserves this accepted milestone queue; no historical issues are
created. Issue-ready titles are "Adopt Handbook in Infrastructure", "Expose read-only
deployment compatibility and safe rejection codes", and (in Unibase) "Check host
compatibility before publishing releases". Link eventual issues with Related to;
issue creation and project enrollment remain pending human approval/access verification.

Handbook adoption records English, main integration, no deployment branches and
Uniwares project #2. Project identity/fields/association/access remain unverified due
to missing read:project scope. No team, project or permission changes are included.
The existing Handbook checkout remains on its work branch; task resource reads use
reviewed revision 68114406d21c7f811281503970f7982d73239c0c without changing that branch.

Preflight code and synthetic checks do not certify installed host behavior. Follow
[deployment preflight](operations.md#deployment-preflight) for compatibility rollout
and the protected readback. Controller installation, permission-profile update and
staging release/check are verified on October 31. Dify functional and approved-plan
OIDC acceptance remain pending; see the host inventory and application release record.

## Accepted repeatable deployment implementation

Local source implements projected bundles, v2 locked execution, durable plans and
one-use OIDC approvals, fixed configuration/controller/recovery operations and pinned
workflow routing. Unibase clients now request v2; host installation must precede their
promotion. Production mapping and manual encrypted recovery are implemented but not
activated. Admin enrollment uses the selected existing team's numeric IDs. No issues,
project access or organization permissions were changed.

Linux synthetic integration covers archive/updater/dispatcher, contention, approvals
and recovery boundaries. Controller installation and routine staging release/check are verified. Actual emitted
GitHub OIDC claims, off-host restore rehearsal and protected-plan live acceptance remain
rollout checks, not source-test claims. See operations.md for ordered procedures.

## Accepted image retention and disk protection ? 2026-10-31

The accepted implementation adds explicit Unibase enrollment, three-release/fourteen-day protection, a 20 GiB pre-pull minimum, 30 GiB cleanup target and 80% usage warnings. Verification and separate read-only review precede publication. Privileged readback, the authorized one-time cleanup, installation and staging release/check are verified. Automatic policy/timer activation remains pending and separately authorized. See [the canonical procedure](operations.md#image-retention). Issue-ready outcomes: Infrastructure retention/controller tooling; related Unibase release and initializer integration. No issues created or tracking permissions changed.


## Documentation reconciliation — 2026-10-31

Installed host identities and capacity are canonical in [inventory](inventory/srv1.md#installed-control-and-capacity--2026-10-31); application release/check identities and acceptance are in [Unibase](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md#current-staging-release). Controller/maintenance installation, configuration correction and routine staging release/check are complete. Remaining: real OIDC approval-path acceptance, recovery configuration/rehearsal, automatic policy/timer activation, production activation and read:project verification. Documentation publication requires no host action.
