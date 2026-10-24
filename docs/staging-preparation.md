# Unibase staging preparation — 2026-10-24

Phase 1 preparation is complete; this review package is not evidence of deployment. Start with the
[operations runbook](operations.md). Provider credentials remain in the protected
[local handoff](provider-access.md); this document contains only public bindings.

The checklist below is the Phase 1 snapshot. Phase 2 has since added the provider
bindings and live tunnel/DNS route; current execution status is canonical in the
[runbook progress table](operations.md#configuration-and-progress) and
[dated inventory](inventory/srv1.md#live-follow-up--2026-10-24). Host bootstrap and
the first application release are still pending.

## Configuration checklist

| Input | Selected value / evidence |
| --- | --- |
| Host/access | Verified `vps-ae0a9d01.vps.ovh.net:22`, operator `uniwares-ops-admin`, key reference `srv1-ops-admin`; pinned host key in inventory |
| Routine account | `uniwares-deploy-user`; separate shared key still to generate/install during authorized bootstrap |
| Hostname | `unibase-staging.uniwares.co.uk`, accepted by operator; route and DNS absent in live Cloudflare |
| Firebase | `uniwares-base`, number `870391561828`; existing web app `1:870391561828:web:bcb7e017845ae626882971`; credentials authenticated and saved web configuration matched live |
| Firebase Auth | Initialized; email/password and Google sign-in enabled. Authorized domains currently Firebase defaults and localhost; staging domain must be added |
| Atlas | Project `6a869d84e65675f845fa22eb`, cluster `kids-booklet`, MongoDB 8.0, IDLE; proposed database/user `unibase_staging`; user read returned 404 |
| Atlas access | Exact VPS IPv4 `/32` exists, but existing `0.0.0.0/0` also permits broad ingress. Do not remove shared entries without owner review |
| Tunnel | Existing healthy `kids-booklet-vps`, ID `3d383dc7-335b-4989-b0f2-d1f32a7092f2`; live route list matches owner declaration |
| Listener/network | Proposed `127.0.0.1:35101`, `172.30.241.0/24`; no listener or Docker/host-route overlap observed. Operator reports no reserved VPN ranges; recheck before apply |
| Redis | Existing application Compose Redis, DB 0; generate password once and retain privately; no Dify Redis changes |
| Images | `ghcr.io/uniwares-ltd/unibase`; public visibility and anonymous digest pull checked in Release. Redis 7-alpine, Nginx stable-alpine and Node 24.16.0-bookworm-slim digests resolved from Docker Hub and pinned in Unibase staging JSON |
| Compose | 5.6.1 candidate checksum verified; current Unibase definition parses with synthetic files. Host still runs 2.28.1. Apt simulation additionally upgrades Buildx 0.15.1 to 0.38.1; no Engine upgrade/removals proposed |
| Backup | Atlas backup flag false; OVH snapshots/automated backup disabled. Off-host app backup destination deferred; no recovery claim |

Provider reads were performed with the supplied local credentials. Cloudflare's
user-token verification endpoint returned 401 while the required tunnel/DNS reads
succeeded; successful resource reads are the relevant permission evidence. Do not
rotate a working account token merely to satisfy a user-token endpoint.

## Reviewed installation boundary

The new scripts are prepared for review; installation and privileged acceptance
remain Phase 2. `scripts/build-control-bundle.py` archives an explicit reviewed
Unibase Git commit and reports its SHA-256. `scripts/bootstrap-deploy.py` previews
by default and requires a trusted root session, the archive/hash and one plain
Ed25519 deployment public key. It rejects changed existing installations, unsafe
paths, archive links and checksum mismatches. Identical partial setup resumes;
changed control versions require an explicit operator update, not routine dispatch.

The installer creates a shared system user with a root-owned home and forced SSH
command. It grants only `/usr/local/sbin/uniwares-deploy` with **no arguments**.
The dispatcher accepts bounded JSON for registered staging deploy/check/rollback,
checks installed configuration identity and image repository, and runs only a
root-owned reviewed control bundle. It does not accept uploaded code, arbitrary
shell commands, sudo commands, Compose mounts, paths or provider credentials.
The account gets neither Docker-group membership nor general sudo.

Build locally from the reviewed implementation commit, not a branch that may advance:

```powershell
python output/infrastructure/scripts/build-control-bundle.py . 6edc411e3561d6e986990471d4d3c112b7c989ec output/unibase-control.tar
```

The agent stages the archive, deployment public key and reviewed Infrastructure
scripts in the operator home via existing pinned SSH. The trusted root operator
copies those inputs into a fresh root-only directory, compares their checksums
with the reviewed local manifest, then runs:

```bash
python3 -I bootstrap-deploy.py --bundle unibase-control.tar --sha256 0c97001724c813b1902c5d1ca7afb742efd13277158869a42bf4fc6d41981545 --public-key deploy.pub
# Only after reviewing the preview and authorizing Phase 2:
python3 -I bootstrap-deploy.py --bundle unibase-control.tar --sha256 0c97001724c813b1902c5d1ca7afb742efd13277158869a42bf4fc6d41981545 --public-key deploy.pub --apply
```

The reviewed control revision is Unibase `6edc411e3561d6e986990471d4d3c112b7c989ec`;
its archive SHA-256 is `0c97001724c813b1902c5d1ca7afb742efd13277158869a42bf4fc6d41981545`.
Infrastructure tooling revision is `bb041e4710cb07f55db3f249c690d0eb7b432355`.
The bootstrap script SHA-256 is `2d266ab04c4a3dab40cd45b59c08df13becba2ec80ee0433f45d45cb74cedf80`;
dispatcher SHA-256 is `07e4bb081a69260af4103d412f1531aaff92ba156657f325bd30e2e12c4b2007`.
The actual archive passed extraction checks (355 files). Regenerate/review these
identities if code changes; do not silently substitute a later branch tip. These
commands require files copied into that root-owned directory; never execute the
installer directly from the shared user's writable home. Current operator sudo
permits only discovery. The one-time root installation is still a manual action
for Phase 2, not a reason to grant unattended unrestricted sudo during Phase 1.

Use Unibase's [application procedures](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md)
for private runtime preparation and indexes after provider binding. Verify allowed
dispatch and rejection of shell/SFTP/port-forwarding/unknown actions before release.
Keep the existing root session until access checks finish. Never install the
operator's admin private key in application repository secrets.

## Concrete Phase 2 scope

1. Wait for the existing Booklet staging operation to finish and establish a healthy
   baseline. Latest discovery saw the normal staging container stopped and an
   unhealthy temporary operation container; this work did not cause or modify it.
2. Review the Compose plus Buildx package plan. Retain old packages for rollback;
   parse existing owner definitions privately and run a disposable compatibility
   check before recreating any application. Candidate parsing alone is not runtime
   compatibility. Preserve Engine and existing services.
3. Install the reviewed shared deploy account/dispatcher and app control bundle.
   Create only missing private Unibase configuration and additive indexes. Recheck
   routes/listener/subnet and retain credentials on interruption.
4. Add the staging Firebase authorized domain and verify Google OAuth redirect
   authorization for `https://unibase-staging.uniwares.co.uk/__/auth/handler` through
   the Google client owner. Create only the app-scoped Atlas `readWrite` user in
   the existing cluster. No shared Firebase identity/key replacement or broad
   Atlas access-list cleanup.
5. The existing tunnel owner reviews/applies its optional Unibase route and proxied
   DNS record. Its Terraform remains authoritative; use its existing state and
   runbook. Inspect the complete plan for unrelated drift before applying.
6. Store repository deployment key, host pin and Cloudflare read token. Publish
   through Unibase's reviewed `_staging` workflow. If first publication is private,
   the owner changes package visibility to public and reruns; no separate image
   workflow or pull credential is introduced.

Phase 3 checks login, readiness, workers, Redis and unchanged existing services.
First-deployment failure retains configuration/data and stops only its candidate;
there is no predecessor to restore. Recovery rehearsal and consolidation stay
explicit follow-ups. OVH edge filtering remains unverified; no new public app
port or firewall change is proposed.

## Validation and review

Ten Infrastructure protocol/archive/discovery tests passed. Unibase's
[CI run 40106982074](https://github.com/Uniwares-LTD/unibase/actions/runs/40106982074)
at `6edc411` passed all 47 deployment tests in an isolated Linux container, including
first-release cleanup, retained rollback, anonymous-pull rejection and branch guards.
The local Windows run passed 27 and skipped 20 platform-specific checks; CI closes
that coverage gap. Shell syntax, local Actionlint, application documentation and
skill-integrity checks passed. Owner Terraform validation and three mock-provider
tests passed without a backend or real provider calls. Cross-repository link
validation passed. Supplied private credential values were absent from changed
files. A separate read-only review checked the final interfaces and failure paths.

CI also passed environment, skill/docs, TypeScript, lint, formatting, application
and account tests, and ShellCheck. It reported advisory warnings for stale client
translation sections, dependency audit findings and Actionlint unavailable in that
runner; the separately downloaded/checksummed local Actionlint passed. No UI or
runtime application source changed. None of these checks proves live readiness. Preserve the
Phase 2 disposable compatibility, privilege-boundary and service-health checks.
