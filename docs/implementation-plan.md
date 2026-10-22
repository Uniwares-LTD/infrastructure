# Shared infrastructure implementation plan

Documentation initialized on 2026-10-22. No executable setup, live provisioning,
service transfer or deployment is completed by this documentation pass.
See [architecture](architecture.md), [operations](operations.md) and
[inventory](inventory/srv1.md). Application work remains in
[Unibase's implementation plan](https://github.com/Uniwares-LTD/unibase/blob/main/docs/implementation-plan.md).

## Delivery sequence

1. **Complete targeted discovery.** Inspect host/VPN routes, effective ingress
   filtering, cron/external schedules, gateway usage, DNS/tunnel authority, external
   Redis availability and off-host backup options. Keep findings dated.
2. **Resolve bootstrap interfaces.** Specify restricted dispatcher actions,
   root-owned configuration, shared account/key provisioning, unique app identities,
   network allocation and Redis logical database assignments. Review against the
   trusted-app threat model without granting general Docker/root access.
3. **Verify Compose upgrade.** Select the latest compatible candidate after package
   and disposable-stack checks; preserve rollback. Keep Engine and legacy gateway
   migrations separate. Passing the version guard is insufficient.
4. **Add new shared services.** Provision application Redis separately from Dify,
   and the shared gateway behind an owner-managed tunnel integration. Register the
   exact hostname/listener through the existing owner; do not replace its route list
   from Unibase. Keep legacy Nginx and Booklet/Dify unchanged.
5. **Integrate Unibase staging.** Adapt its public images, repository secrets,
   shared Firebase/Redis, proxy handling, job endpoints/timers and `prod` naming.
   Validate its independent build, deploy, readiness, rollback and recovery.
6. **Prove recovery and retention.** Establish off-host storage and minimum backup
   permissions; rehearse backup/restore and document image retention before cleanup.
7. **Evaluate later migrations.** Inventory legacy routes fully before moving to
   public Caddy. Transfer Dify/tunnel/other services only through explicit ownership,
   state, credential and rollback plans.

All seven steps remain pending. Documentation approval does not authorize their
live execution. Shared-system operations require explicit scope and acceptance.

## Acceptance for future implementation

- Existing Booklet, Dify and legacy routes remain functional; access is preserved.
- Selected networks do not overlap Docker, host or VPN routes; service aliases and
  Redis database assignments are unique for each application/environment.
- Routine deployment uses the shared restricted account without general sudo or
  Docker-group membership; privileged credentials are absent from app workflows.
- Anonymous digest pulls, credential-free builds and retained configuration rollback
  work from each application's own workflow.
- Timed requests are authenticated, bounded and observable; crashes/retries do not
  duplicate payments, notifications, AI submissions or result applications.
- A verified backup restores to a disposable database, including GridFS data;
  failure never reports success or automatically resumes unhealthy writers.

## Open decisions

Replacement network/listener allocation; tested Compose version; exact gateway and
tunnel integration; confirmed app Redis location/database count; off-host backup
destination, retention, encryption-key recovery and required recovery permissions;
production recovery objectives; legacy service ownership and migration timing.
Record these decisions with supporting evidence before their implementation.
