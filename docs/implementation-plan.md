# Shared infrastructure implementation plan

Use the [three-phase runbook](operations.md) for execution and its single
configuration/progress table. This plan separates first deployment from later
consolidation. Phase 1 preparation is complete; live setup and application deployment
remain unverified. [Inventory](inventory/srv1.md) records the dated baseline.

Access progress, 2026-10-22: operator key login and the trusted-root host fingerprint
are verified. Shared-key distribution uses the [operator handoff](operations.md#shared-operator-key-handoff).
Agent-side strict-host-key SSH and non-privileged discovery are also verified.
Reviewed privileged setup operations remain pending; this is not bootstrap or deployment
acceptance. See the inventory for current routes, listeners and access limitations.

Scoped discovery tooling is installed: fixed no-argument helper and hash-verified
root installer. Local boundary tests, VPS syntax/non-root refusal checks, operator
installation and agent-side scoped-sudo positive/negative checks pass. The inventory
records the observed Docker state and remaining discovery limits. This does not implement
the later deployment dispatcher or grant setup privileges.

The [October 24 preparation package](staging-preparation.md) records provider read
results, the proposed non-overlapping subnet, prepared dispatcher and concrete live
change scope. Local preparation does not install accounts or change services.

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
3. **Verify and hand off.** Check login, readiness, existing workers and unchanged host
   services. Record release identity, routine workflow instructions and deferred work.
   A failed first release stops only its candidate/workers and any candidate timers;
   preserve data/configuration. No imaginary prior-release or DB rollback.

[Unibase's plan](https://github.com/Uniwares-LTD/unibase/blob/main/docs/implementation-plan.md)
owns application changes. These phases remain pending live acceptance. Authorization
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
- [ ] Define image retention before selective cleanup. Evaluate legacy public gateway,
  Dify/tunnel ownership transfers, Engine upgrades and production separately.

## Remaining decisions

First-deployment preparation has selected the dispatcher, existing provider bindings,
hostname, private listener and candidate subnet/Compose versions; see the preparation
package. Remaining execution checks belong to Phase 2: one-time root installation,
Compose/Buildx runtime compatibility, provider writes and live route/privilege checks.

For later work: shared network/gateway design, shared Redis location/database allocation,
job endpoint/timer interfaces, off-host destination/retention/encryption recovery and
required restore actions, production recovery objectives and migration ownership.
Do not resolve later decisions by blocking unrelated first-release work.
