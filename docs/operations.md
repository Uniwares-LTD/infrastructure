# Staging bootstrap and operations runbook

Start here to take the [implementation plan](implementation-plan.md) from the
[dated inventory](inventory/srv1.md) to an accepted Unibase staging deployment.
Architectural rationale stays in [architecture](architecture.md); application
behavior and workflow details stay in the
[Unibase deployment guide](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md).

Execution model: the operator establishes protected administrative access once;
the agent then performs discovery and explicitly authorized setup. Routine releases
eventually use `uniwares-deploy-user`. This runbook's publication executes nothing.
Commands below are instructional, checked against their interfaces, not evidence of
execution on srv1. Stop at **implementation required** until reviewed tooling exists.

## Configuration and progress

Complete this single checklist during discovery. Resolve available facts from
existing access and provider APIs first; ask the operator for remaining non-secret
inputs together. Keep secret values in protected stores, never in this checklist.

| Input | Record before use |
| --- | --- |
| Target and access | srv1 identity; confirmed SSH route/port or Access profile; admin key reference; pinned host-key fingerprint; usable privilege path |
| Revisions | Reviewed infrastructure, Unibase and any tunnel-owner commits; corresponding PRs |
| Staging identity | Canonical HTTPS hostname; DNS zone and tunnel owner/integration |
| Providers | Shared staging Firebase project, web app and domain registration; provisioner/OIDC references if retained; Atlas project/cluster, app DB/user and exact egress allowlist |
| Networking | Selected gateway listener, application network/subnet and aliases; Docker plus host/VPN overlap checks |
| Redis | Confirmed non-Dify instance, connection reference, available database count and assigned staging DB |
| Image | Public GHCR package, reviewed source SHA and immutable release digest |
| Secrets | Secret names, protected source references and consumers; separate admin/deploy/recovery credentials |
| Recovery | Private off-host destination, encryption-key recovery reference, retention, tested permissions and disposable restore target |

Use the table below as the latest checkpoint state, not an incident log. Update only
after checking actual state. A command starting or a workflow being queued is not a pass.
Status values: pending, in progress, blocked, verified. Verification entries contain
sanitized results and workflow/commit/backup identifiers, never secret-bearing output.

| Checkpoint | Status | Reviewed revision | Verification | Next action |
| --- | --- | --- | --- | --- |
| 1 Access | Pending | Not selected | Not performed | Operator access handoff |
| 2 Discovery | Pending | Not selected | October 22 baseline only | Complete targeted checks |
| 3 Tooling | Pending | Not selected | Implementation required | Implement and review both repos |
| 4 Host bootstrap | Pending | Not selected | Implementation required | Wait for 1-3 |
| 5 Staging resources | Pending | Not selected | Implementation required | Bind reviewed resources |
| 6 Deployment | Pending | Not selected | Not performed | Run reviewed app workflow |
| 7 Recovery | Pending | Not selected | Implementation required | Rehearse rollback/restore |
| 8 Handoff | Pending | Not selected | Not performed | Verify routine operation |

## 1. Establish operator access

**Owner/location:** operator on the local workstation and existing trusted root VPS
session; agent prepares instructions. Keep that root session open until a second
connection and administrative privilege check succeed. Do not change root login,
SSH daemon policy or firewall rules during this handoff.

**Prerequisites/action:** confirm the existing working SSH transport; the published
Access hostname is not proof that a direct SSH connection or local ProxyCommand
is configured. On Windows PowerShell, generate a new admin key only if its path
does not exist. Use a passphrase and protected password-manager recovery storage.

```powershell
$opsKeyPath = Join-Path $env:USERPROFILE '.ssh/uniwares-ops-admin'
if ((Test-Path -LiteralPath $opsKeyPath) -or (Test-Path -LiteralPath "$opsKeyPath.pub")) {
    throw 'Key path already exists; inspect and reuse it instead of overwriting.'
}
New-Item -ItemType Directory -Force -Path (Split-Path $opsKeyPath) | Out-Null
ssh-keygen -t ed25519 -a 64 -f $opsKeyPath -C 'uniwares-ops-admin'
if ($LASTEXITCODE -ne 0) { throw 'Key generation failed.' }
ssh-keygen -lf "$opsKeyPath.pub"
```

Transfer only the `.pub` contents to the trusted root session. First inspect
`getent passwd uniwares-ops-admin` and `id uniwares-ops-admin`. If absent, the
operator creates it with `adduser uniwares-ops-admin` (interactive password kept
private), then `usermod -aG sudo uniwares-ops-admin`. If already present, inspect
its home, groups and existing access instead of recreating or resetting it.

For a newly created account with the default `/home/uniwares-ops-admin` home,
create `.ssh` owned by that account with mode 700. Append the exact public key as
one line to `.ssh/authorized_keys`, preserving existing keys; set the file owner
to that account and mode 600. Use the existing root session's editor. On resume,
check existing public-key fingerprints before appending; do not duplicate the key.
Confirm the home path through `getent` before touching any existing account's files.

Read the server fingerprint through the trusted root session:

```bash
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

Use the corresponding public host key to establish the local known-hosts entry for
the actual hostname/port. Compare through the trusted session before trusting a new
key; a network scan alone is insufficient. Never disable host-key checking.
Create a local SSH profile named `uniwares-srv1-admin` using the confirmed transport,
`User uniwares-ops-admin`, the protected key, `IdentitiesOnly yes` and
`StrictHostKeyChecking yes`. Preserve any required Access transport configuration.
Keep access-token values outside the profile and repository. Unlock the private key
locally; give the agent the profile/key reference, not its contents or passphrase.

**Expected result:** a second connection via `ssh uniwares-srv1-admin` reaches the
expected host; `id`, `hostname`, `sudo -v` and `sudo -l` establish the admin identity
and permitted actions. The operator handles any password prompt privately. Test the
agent's actual execution channel too: `sudo -n true` probes general noninteractive
sudo, not command-specific permissions. Record the result and verify the exact
reviewed privileged command before checkpoint 4; interactive success alone is
insufficient. Checkpoint 3 must define that privilege path. Do not compensate by
adding general passwordless sudo or sending a password through command arguments.

**Failure/resume:** retain the original root session. Inspect the confirmed route,
host-key match, account home, file permissions and authorized public-key fingerprint.
Reuse an existing valid key/account; do not reset credentials or relax SSH checks.
Read-only discovery may proceed without unattended sudo; privileged setup may not.

## 2. Complete discovery in one pass

**Owner/location:** agent through the established VPS profile and existing read-only
GitHub/provider connections. Prerequisite: verified host identity at checkpoint 1.

**Action:** gather remaining host/VPN routes, effective host/provider firewall rules,
cron/external schedules, gateway upstreams and consumers, package compatibility,
DNS/tunnel authority, Redis availability and off-host backup options. Inspect private
configuration locally and report allowlisted facts; do not dump environment files,
full Compose renders, crontab secrets or raw provider responses into chat/Git.
Reuse October 22 observations unless a decision requires refreshing them.

**Expected result:** updated dated inventory and the configuration checklist above,
with unresolved inputs collected from the operator in one batch. Network allocation
must avoid Dify's `172.29.0.0/16` and all host/VPN routes. No resource is assumed to
exist just because a configuration field names it.

**Failure/resume:** mark inaccessible checks unresolved and continue independent
reads. Stop only dependent provisioning; do not create replacement resources to
work around missing discovery credentials.

## 3. Prepare and review tooling

**Owner/location:** agent in Infrastructure and Unibase development checkouts;
normal PR review. **Implementation required.** Checkpoint 2 supplies allocations
and ownership; independent code preparation can proceed while other inputs settle.

**Action:** Infrastructure implements bootstrap, restricted dispatcher, shared
gateway/Redis definitions and timer templates. Unibase implements the documented
secret, public-image, provider, proxy, job and recovery adaptations. Provide a
reviewed build/publish preflight that can produce a public candidate without host
deployment, so checkpoint 5 can verify anonymous pulls before first activation.
Define the actual administrative execution path and narrow dispatcher actions;
password-based sudo access alone is not unattended automation. Specify root-owned
privileged entrypoints without user-writable script/config escapes; their live
installation belongs to checkpoint 4.

**Expected result:** reviewed revisions, focused checks and exact preview/apply,
verification and recovery commands added here by their implementation change.
Check malformed/unauthorized dispatch, arbitrary mounts/commands, repeat setup,
partial failure, provider retry semantics and first-release recovery. Existing app
workflow names alone are not proof of compatibility with the target architecture.

**Failure/resume:** continue work on the same reviewed change branches; do not use
one-off host commands to bypass missing interfaces or tests. Re-review changed
behavior before advancing. This checkpoint does not authorize live execution.

## 4. Bootstrap the host

**Owner/location:** agent through the authorized admin path on the VPS, after
checkpoints 1-3. **Implementation required:** use the reviewed bootstrap entrypoint;
no such command is shipped in this documentation-only repository yet.

**Action:** preview existing state, then apply within the authorized maintenance
scope. Establish the shared deploy user/key and dispatcher, verify the selected
Compose upgrade, and create the chosen application network, Redis and gateway.
Keep legacy Nginx on port 80 and preserve Booklet/Dify routes. Upgrade Engine or
migrate legacy services only in separate work. Generate the deploy credential
separately from the admin credential and store copies as described below.

**Expected result:** app Redis is private and separate from Dify; network/aliases
are conflict-free; the deploy account can perform allowed operations and rejects
arbitrary shell/root/Docker access. Verify existing service health against the
baseline, not only new-container startup.

**Failure/resume:** inspect created accounts, resources and installed revision;
rerun the same preview and apply only missing compatible steps. Keep working shared
services/data. Use the reviewed package rollback if an upgrade fails; never globally
prune Docker or tear down another Compose project to recover.

## 5. Bind staging resources

**Owner/location:** agent via reviewed application workflows/provider APIs and the
existing tunnel owner's process. **Implementation required:** checkpoint 3 must
adapt current Unibase provisioning before these target bindings can be applied.

**Action:** follow the application guide for shared staging Firebase registration,
app-scoped MongoDB, public GHCR and repository-secret configuration. Record the Redis
logical DB allocation. Keep Dify/payments/other optional providers disabled initially.
Coordinate the exact hostname/gateway listener through
[agentic-poc's runbook](https://github.com/karpishe-experiments/agentic-poc/blob/master/docs/deployment/runbook.md);
do not create a competing tunnel route controller. Confirm credentials without
printing them and keep the privileged admin key out of application repositories.

**Expected result:** required input/connection checks pass; secret names and owners
are recorded; a public candidate image can be pulled anonymously by digest. Confirm
DNS/tunnel/gateway target selection here; full application response is checked after
checkpoint 6 starts the app. An image publication or DNS record alone is not readiness.

**Failure/resume:** rerun discovery/preview and repair only missing bindings. Preserve
existing Firebase keys/users, databases and working route entries. Do not reset shared
staging identities or replace an owner's complete tunnel configuration.

## 6. Deploy and verify staging

**Owner/location:** agent through Unibase GitHub Actions using the restricted deploy
account. **Implementation required:** target-compatible workflows, endpoints and
timers must pass checkpoint 3; resource/host checks must pass checkpoints 4-5.

**Action:** follow the application guide's execution/acceptance section. Publish one
reviewed `_staging` revision and run its independent deployment workflow. Avoid both
pushing and manually dispatching the same release. Record the workflow, source SHA,
image digest and runtime-configuration identity. Enable reviewed timers with job
authentication; keep optional live providers disabled until separately configured.

**Expected result:** web readiness, authentication, private Redis and authenticated
job progress pass; unauthorized job calls fail. Check public routing, headers,
streaming and the unchanged health of Booklet/Dify/legacy services.

**Failure/resume:** inspect candidate and prior-release state before retry. On the
first deployment there is no previous release: stop only the unhealthy candidate
and its timers, retain diagnosis/config/data, and fix/redeploy a reviewed revision.
Do not invent an image rollback or restore the DB. For later releases, use the
application's verified prior image/config rollback. Do not restart shared services.

## 7. Prove rollback and recovery

**Owner/location:** agent through reviewed application workflows, using workflow-only
recovery credentials. **Implementation required:** backup/restore tooling and the
approved off-host destination/permissions must exist first.

**Action:** follow the minimum policy below. First deployment establishes one healthy
release; exercise image rollback only after a second compatible release provides
a real predecessor. Backup the staging DB/GridFS and restore into a separate,
explicitly named disposable database. Verify records and file bytes without posting
their contents. For an empty disposable target, record that there is no prior data
to back up; any nonempty target requires its pre-restore backup. Do not target shared
Firebase or Dify data.

**Expected result:** previous image/config runs successfully; backup bytes are
verified off-host; the disposable restore has correct data/files. Record digests,
backup ID and sanitized verification. Production remains out of scope.

**Failure/resume:** leave failed restores isolated; do not mark partial archives
complete or resume unhealthy writers automatically. Identify the failed checkpoint
before retrying the selected backup. Retain the source and pre-restore backup; any
cleanup must name only disposable resources created for this rehearsal.

## 8. Handoff

**Owner/location:** agent updates canonical repository docs after live checks;
operator confirms the access/recovery handoff.

**Action:** record verified workflow entrypoints, ownership, secret-store references,
release/recovery identifiers and remaining work. Update the checkpoint table and
inventory as current facts, not a chronological log. Keep key material private.

**Expected result:** routine app deployment/check/rollback uses the restricted
account; privileged maintenance has a separate documented path. Another operator
can identify the current release and the next recovery action from these records.

**Failure/resume:** leave unverified checkpoints open and point to their exact
dependency. Do not declare staging accepted based solely on a green build.

Legacy Nginx migration, Dify/tunnel ownership transfer, production activation,
Docker Engine upgrades and broad disk cleanup are outside this initial path.

## Credentials and access

GitHub Free does not expose organization secrets to private repositories, and
private-repository environment secrets require a paid plan. Use repository secrets:
one deployment key stored authoritatively in a password manager, copied as
`DEPLOY_SSH_PRIVATE_KEY` to each trusted application repository. Document the
consumer list when configured; no synchronization service or per-project key
rotation infrastructure is required. Retain a separately verified SSH host-key pin.

| Credential metadata | Intended storage / consumer |
| --- | --- |
| Shared deployment private key | Password manager and each trusted repo's Actions secret; routine restricted dispatch |
| SSH host-key pin | Repository configuration/secret as required by workflow; public trust material verified through root/operator access |
| Privileged operator key | Password manager/local protected store; infrastructure repo secret only if an explicitly privileged workflow requires it |
| Shared staging Firebase credentials | Protected authoritative store, selected repo secret copies and private runtime files; never build inputs |
| Application/environment secrets | Repo secrets with `STAGING_` / `PROD_` prefixes where values differ; private runtime snapshots |
| Recovery credentials | Workflow-only protected storage; never application's runtime environment |

This table establishes target storage, not evidence that secrets/accounts exist.
The [application guide](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md)
owns concrete runtime names and current compatibility gaps. Existing Booklet
credentials retain their [current inventory](https://github.com/karpishe-experiments/agentic-poc/blob/master/docs/deployment/contracts.md).
Reusable workflows do not bypass private-repository secret availability limits.

Bootstrap uses existing root access to establish the shared accounts and restricted
dispatcher. Routine deployment must not grant arbitrary root commands, arbitrary
Compose mounts or Docker-socket access. Review allowed actions and root-owned
configuration before implementation; a dispatcher label alone is not a privilege
boundary. Do not place the deploy user in the Docker group.

## Coordination and upgrade procedure

Use a non-cancelling Actions concurrency group per repository for conflicting
deployment, restore and administrative actions. Before shared gateway, Redis,
Docker or tunnel maintenance, announce the maintenance window through the team's
normal channel and ensure affected workflows/writers are stopped or drained.
Do not add a host-wide journal/orchestrator. Existing agentic-poc locks remain
unchanged. Database leases and idempotency are application correctness controls.

Compose 5.6.1 is the observed package candidate, not validated compatibility.
Inspect package changes and release compatibility, retain the old package/version,
and validate existing Compose definitions without publishing rendered secrets.
Test create/start/check/rollback with disposable resources before any affected
service recreation. Verify Booklet/Dify and legacy apps afterward. Treat an Engine
upgrade as separate maintenance; do not combine it with initial gateway cutover.

For published services, check both host and provider firewall behavior. UFW alone
does not reliably restrict Docker-published ports. Prefer private application/Redis
listeners and gateway-only ingress. Avoid changing legacy exposure without mapping
its consumers and preserving operator access.

## Image retention

The inventory reports 69.34 GB of reclaimable images. First identify each app's
active and retained rollback digests and whether they can be pulled again. Remove
only explicitly selected obsolete images; record a small retention policy when
implemented. Do not blanket-prune images/volumes across all projects. The current
57 GiB free disk does not require emergency deletion to begin staging work.

## Minimum staging backup and recovery

Target one manual application workflow with `backup` and `restore` actions.
Back up before migrations or destructive operations, rather than every image
deployment. A manual policy accepts loss since the last successful backup;
production recovery expectations remain a separate decision.

- Include the app MongoDB database and GridFS bytes; verify a private encrypted
  off-host archive, manifest and checksum before declaring success.
- Pause/drain writers and timers for a consistent backup/restore. Require an exact
  backup ID and target confirmation for restore, and take a pre-restore backup.
- Verify restoration in a disposable database before relying on recovery.
- Preserve runtime secret recovery separately. Redis counters do not need backup.
  Shared Firebase identities and Dify infrastructure are outside an app DB restore.
- Retain image/configuration rollback independently; do not automatically restore
  data after an image deployment failure. Extend coverage before enabling S3 media.

Off-host destination, encryption-key recovery, retention and exact database roles
remain open. `dbAdmin` alone must not be assumed sufficient for dumping/restoring
data; verify the required actions with dedicated workflow credentials. MinIO on the
same VPS alone does not protect against VPS loss. Do not reuse Booklet/Dify backup
buckets or credentials without a reviewed ownership/access decision.

## References

- [OpenSSH key generation and fingerprints](https://man.openbsd.org/man1/ssh-keygen.1)
- [OpenSSH host-key verification](https://man.openbsd.org/ssh)

- [GitHub Actions secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [GitHub environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [Docker firewall behavior](https://docs.docker.com/engine/network/packet-filtering-firewalls/)
- [Docker image pruning](https://docs.docker.com/reference/cli/docker/image/prune/)
- [Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https)
- [Redis logical databases](https://redis.io/docs/latest/commands/select/)
- [systemd timers](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)
