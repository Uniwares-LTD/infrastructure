# Shared infrastructure implementation plan

Use the [three-phase runbook](operations.md) for execution and its single
configuration/progress table. This plan separates first deployment from later
consolidation. Phase 1 preparation is complete. October 25 operator output confirms
plugin upgrades, restricted deployment account/control installation, the reviewed
null-IPAM preflight repair, private runtime preparation and additive index setup.
The first staging release and independent restricted check passed; final discovery
found Booklet staging/production, Dify and legacy services at their expected baseline.
Phase 3 staging acceptance and handoff are now verified: Google admin/session/profile
and logout/re-login checks, operator-reported incognito email login/logout, workstation
Actions/pinned SSH access and fresh runtime checks passed. The Cloudflare HTML
rewriting/CSP hydration defect was corrected by Unibase's no-transform response,
deployed and verified on fresh account/admin loads. Current release identity and
evidence belong in operations; app details belong in its acceptance record.
The optional AI runtime/control update is now installed and its staging release passed.
Application-level Dify/MCP/Persona acceptance remains open in Unibase; a healthy
release does not complete that milestone. Guided initialization has synthetic
coverage, with fresh derived provider-write acceptance still outstanding.
Do not repeat completed bootstrap operations. The [operations status table](operations.md#configuration-and-progress)
records current evidence. [Inventory](inventory/srv1.md) records the dated baseline.

Completed bootstrap procedures are [historical references](history/completed-bootstrap-2026-10-25.md),
not a pending checklist. The [preparation package](staging-preparation.md) preserves
the reviewed Phase 1 scope; live status belongs in operations. Application acceptance
belongs in Unibase's deployment guide. Avoid duplicating release IDs and test logs here.

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
- [ ] Define image retention before selective cleanup. Evaluate legacy public gateway,
  Dify/tunnel ownership transfers, Engine upgrades and production separately.

## Remaining decisions

First-deployment preparation has selected the dispatcher, existing provider bindings,
hostname, private listener and candidate subnet/Compose versions; see the preparation
package. Root installation, Compose/Buildx compatibility, provider writes and the
owner route are verified. Application release/acceptance evidence belongs to the
operations progress table; do not infer live health from successful preparation.

For later work: shared network/gateway design, shared Redis location/database allocation,
job endpoint/timer interfaces, off-host destination/retention/encryption recovery and
required restore actions, production recovery objectives and migration ownership.
Do not resolve later decisions by blocking unrelated first-release work.
