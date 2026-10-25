# Staging bootstrap and operations runbook

Use three phases to reach a working Unibase staging deployment. Keep the existing
application workers, application Redis and private Nginx for the first release.
Shared gateway/Redis and app-hosted job endpoints remain the target, but are later
consolidation work. See [architecture](architecture.md) and the
[delivery plan](implementation-plan.md) for that distinction.

The operator establishes protected administrative access once. The agent completes
discovery and reviewed implementation, then performs setup within the explicitly
authorized live scope. Routine releases use the restricted deploy account.
This runbook's publication executes nothing. Commands are instructions checked
against their interfaces, not evidence of execution on srv1. Steps marked
**implementation required** cannot be run with the current tooling unchanged.

## Configuration and progress

Use the [Phase 1 preparation package](staging-preparation.md) and
[protected provider handoff](provider-access.md). Use [the dated inventory](inventory/srv1.md); refresh only facts needed for the
next decision. Discover available values first and request remaining non-secret
inputs together. Record secret names and protected-store references, never values.

| Input | Needed for first deployment |
| --- | --- |
| Access | Host identity, working SSH transport/profile, key reference, host-key pin and usable privilege path |
| Revisions | Reviewed infrastructure, Unibase and tunnel-owner revisions |
| Staging | HTTPS hostname, DNS/tunnel authority and owner-managed route to the app's private Nginx listener |
| Providers | Existing shared staging Firebase project/credentials, app registration/domains; Atlas cluster, app database/user and exact egress allowlist |
| Network | Free loopback port and application subnet checked against Docker and host/VPN routes |
| Runtime | Existing app Redis at database 0, private password reference; current worker/Nginx configuration |
| Release | Public GHCR package and reviewed source SHA; record immutable image digest when the release workflow builds it |
| Deferred recovery | Track destination, encryption-key recovery, retention and restore permissions as follow-up; not a first-startup prerequisite |

Use this table for current status, not a chronological log. Status values are
pending, in progress, blocked and verified. Retain only sanitized verification
and non-secret workflow/release identifiers.

| Phase | Status | Reviewed revision | Verification | Next action |
| --- | --- | --- | --- | --- |
| 1 Connect and prepare | Verified (preparation only) | Infrastructure `bb041e4`, Unibase `6edc411`, owner `c182b64` | October 24: provider reads, inventory, 47 Linux deployment tests, 10 Infrastructure tests and 3 Terraform mock tests; separate read-only review | Complete; subsequent live acceptance is recorded in Phase 2 |
| 2 Bootstrap and deploy | Verified | Runtime `edcc21d`; Infrastructure installer `90ed66a`; owner route `50536f0` | October 25: plugins/account/control and runtime/index preparation complete; Release `40168299056` attempt 3 and independent Check `40168997418` passed, including anonymous pull, local/public readiness and both workers. Booklet staging returned healthy after its separate owner operation; production/Dify/legacy baseline retained | Proceed to Phase 3 user acceptance; do not repeat bootstrap or deployment |
| 3 Verify and hand off | Pending user acceptance | Runtime `edcc21d` | Account page loads with email/Google controls enabled; no user sign-in or recovery rehearsal claimed | Verify real login and complete operator handoff; track recovery/consolidation separately |

### Current Unibase release — 2026-10-25

- Staging: <https://unibase-staging.uniwares.co.uk/account>, branch `_staging`.
- Source: `edcc21de9a501b21f63e353da9a75cdf5efb5e65`.
- Image: `ghcr.io/uniwares-ltd/unibase@sha256:2e4e1ffac7ba401b924c657fe1b9d155cf926dd75d35a47aca0c2ca6fcd7ac1b`.
- Installed control bundle: `15bc84b1691eb42fd6053c36a4363aa0c18b5ba51e210521e41e9209d7ea18f2`.
- Tracked staging configuration SHA-256: `5b1eb3cbc4658f1a0de990484b0744fed313a6473585cc107a284d4aa6478582`.
  Private runtime snapshots remain under `/opt/unibase/staging/releases/`; the
  `current` symlink selects the serving configuration. Never copy their contents to Git.
- [Release attempt 3](https://github.com/Uniwares-LTD/unibase/actions/runs/40168299056/attempts/3)
  and [independent check](https://github.com/Uniwares-LTD/unibase/actions/runs/40168997418)
  passed. Earlier attempts stopped before host activation; no failed candidate needed restoration.

Routine operations use Unibase's own workflows on `_staging`:

```powershell
gh workflow run check-deployment.yml --repo Uniwares-LTD/unibase --ref _staging -f environment=staging
```

A reviewed push to `_staging` triggers Release automatically. Do not also dispatch
the same commit. Use Rollback only when a real compatible healthy predecessor is
retained; this first release has none. Secret references are repository Actions
secrets `DEPLOY_SSH_PRIVATE_KEY`, `DEPLOY_SSH_HOST_KEY`, `CLOUDFLARE_READ_TOKEN` and
the protected provider handoff, not values in this document.

Post-deploy discovery found Unibase app and both workers healthy, app Redis private,
and only Nginx published at `127.0.0.1:35101`. Booklet production, Dify and legacy
services retained their prior statuses. Booklet staging was temporarily stopped by concurrent
owner deployment [40168742098](https://github.com/karpishe-experiments/agentic-poc/actions/runs/40168742098),
with its own operation container. Its client wait expired without stopping that
host operation. A later scoped discovery confirmed Booklet staging healthy again.
No Booklet stop, replay or restoration was performed through Unibase.

The goal is one access handoff, one consolidated input request and one authorization
for concrete live changes. Provider consent/authentication may still need operator
input. Honor existing scope authorization; stop for unexpected destructive changes.

## 1. Connect and prepare

### Establish access

**Owner/location:** operator on the local workstation and existing trusted root VPS
session; agent prepares instructions. Keep that root session open until a second
connection and administrative privilege check succeed. Do not change root login,
SSH daemon policy or firewall rules during this handoff.

**Prerequisites/action:** confirm the existing working SSH transport; the published
Access hostname is not proof that a direct SSH connection or local ProxyCommand
is configured. On Windows PowerShell, generate a new admin key only if its path
does not exist. Use a passphrase and protected password-manager recovery storage.

Resolve command values from repository evidence before requesting operator input.
The owner's [VPS configuration](https://github.com/karpishe-experiments/agentic-poc/blob/master/infra/config/vps.json)
records host `vps-ae0a9d01.vps.ovh.net` and Access endpoint
`srv1-deploy.uniwares.co.uk`; the inventory observes SSH listening on port 22.
These values do not verify external reachability or the new account's login.
After installing the public key and obtaining the host fingerprint through the
trusted root session, test direct SSH from Windows PowerShell:

```powershell
ssh -p 22 -i "$env:USERPROFILE\.ssh\uniwares-ops-admin" -o IdentitiesOnly=yes -o StrictHostKeyChecking=ask uniwares-ops-admin@vps-ae0a9d01.vps.ovh.net
```

Compare any first-connection fingerprint prompt with the trusted-session fingerprint
before accepting; stop on a mismatch. If direct SSH is unavailable, preserve the
working transport rather than opening firewall ports. The owner's deployment script
uses `ProxyCommand=cloudflared access ssh --hostname %h` with the Access endpoint;
that path requires an installed client and authorized Access authentication.
Do not assume those prerequisites from the hostname. Once trust is established,
use the pinned profile with strict checking described below.

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
reviewed privileged command before phase 2; interactive success alone is
insufficient. Prepare that privilege path during phase 1. Do not compensate by
adding general passwordless sudo or sending a password through command arguments.

**Failure/resume:** retain the original root session. Inspect the confirmed route,
host-key match, account home, file permissions and authorized public-key fingerprint.
Reuse an existing valid key/account; do not reset credentials or relax SSH checks.
Read-only discovery may proceed without unattended sudo; privileged setup may not.

### Complete targeted discovery and required implementation

For additional operators, use the [shared key handoff](#shared-operator-key-handoff)
instead of creating another account or regenerating the installed key.

#### Scoped privileged discovery

The [discovery helper](../scripts/srv1-discovery.py) and
[one-time installer](../scripts/install-discovery.sh) were installed and verified
on October 22; see the [acceptance evidence](inventory/srv1.md#scoped-discovery-installation-and-acceptance--2026-10-22).
They cover container names/images/status/ports, Docker IPAM, UFW status and cron
filenames only. They do not disclose container environment, command lines, logs,
cron contents or credentials. Provider firewall and effective packet filtering
remain separate checks. This helper cannot bootstrap or deploy an application.

The agent staged both files in `/home/uniwares-ops-admin/` on October 22. The
operator runs this block in the existing trusted **root VPS session**. Copying the
installer into a fresh root-only directory before checking it prevents the shared
account from changing the verified installer while it executes:

```bash
(
  set -e
  work=$(mktemp -d /root/uniwares-install.XXXXXXXX)
  trap 'rm -rf -- "$work"' EXIT
  cp /home/uniwares-ops-admin/install-discovery.sh "$work/install.sh"
  printf '%s  %s\n' 8914e01c19340674ea1fe3f6de35fc8f6d29bae989b97f630ac0aae44163981c "$work/install.sh" | sha256sum --check
  bash "$work/install.sh"
)
```

The installer verifies the helper hash, trusted parent directories and sudoers
syntax. It installs root-owned `/usr/local/sbin/uniwares-discovery` and one sudoers
rule for that exact command with no arguments. Existing destinations cause it to
stop for inspection. On partial failure, inspect both destinations and sudoers;
do not overwrite an existing installation blindly. To revoke this new grant,
root removes only `/etc/sudoers.d/uniwares-discovery` and validates with `visudo -c`.

After installation the agent runs `sudo -n /usr/local/sbin/uniwares-discovery`.
Verify that arguments are denied and `sudo -n true` still fails. The deploy account,
general sudo, Docker-group membership, services and firewall rules remain unchanged.
Local tests, VPS non-root refusal/syntax checks, root installation, positive
privileged execution and argument/unrelated-command denial checks passed. The
installation block is retained for reference; do not repeat it on the verified host.

**Owner/location:** agent through established read-only VPS/provider access and
development checkouts. Gather host/VPN routes, effective ingress rules, selected
port/subnet, Compose compatibility, tunnel/DNS authority and staging provider
bindings in one pass. Inspect private configuration locally; publish only allowlisted
facts, not full Compose renders, environment files or secret-bearing cron entries.
Full legacy gateway migration, external Redis selection and backup-storage selection
do not block this initial route through the existing tunnel.

The Phase 1 review package provides the first-release adaptations and upgrade plan:
repository secrets for GitHub Free, public GHCR and anonymous pulls, shared staging
Firebase credentials, reviewed restricted root-owned deploy operations, a compatible
Compose upgrade, non-overlapping app networking and supported owner-side routing.
Reuse existing Firebase/Atlas resources; do not build a generic resource-provisioning
platform. Resolve indispensable provider enrollment/permissions in the input batch.
Keep app Redis, worker containers, their health checks, Nginx, leases and idempotency.

Use a reviewed route change in the existing owner's configuration for the first
hostname. Adapt Unibase's verification to check the owned hostname/target before
deployment; do not merely skip route checks or require a generic registration
workflow to exist. Keep the owner's complete route list intact.

**Expected result:** required configuration, reviewed revisions, focused validation
and exact supported preview/apply/recovery commands. The release workflow will
build, publish, verify an anonymous digest pull, deploy and check health in one run;
do not add a separate image-publication workflow or demand a digest before building.

**Failure/resume:** record inaccessible facts and continue independent preparation.
Missing interfaces stay implementation work, not ad hoc host commands. A valid
interactive admin login alone does not prove an unattended privileged execution
path. Preserve existing credentials/resources rather than replacing them to bypass
missing access. Return only unresolved, consequential inputs to the operator.

## 2. Bootstrap and deploy

**Owner/location:** agent through the reviewed administrative entrypoint, provider
interfaces, tunnel owner's process and then Unibase GitHub Actions. Use the reviewed
Phase 1 tooling and concrete scope in [staging preparation](staging-preparation.md).
The status table records completed operations; further live changes require an
authorized scope and current state checks.

**Action:** preview host/provider state and apply missing compatible setup. Establish
the shared restricted deploy account/key, select and verify the Compose upgrade,
and configure a non-overlapping app network/loopback listener. Preserve legacy Nginx
on port 80, Dify Redis and existing Booklet/Dify services. The app's existing Compose
stack creates its own Redis, Nginx and workers; no shared gateway/Redis is installed
for this first release. Keep deployment credentials separate from administrator keys.

Configure the verified Firebase registration/domains, app MongoDB/runtime readWrite
access, repository secrets and tracked staging settings. Keep Dify, Stripe and MCP
disabled. Add the exact hostname-to-private-Nginx route through
[agentic-poc's runbook](https://github.com/karpishe-experiments/agentic-poc/blob/master/docs/deployment/runbook.md).
Unibase retains its own release workflow and paths; it does not deploy through Booklet.

Run one reviewed staging release: build -> publish public image -> verify anonymous
digest pull -> deploy exact digest -> check web/dependencies/current workers.
An anonymous-pull failure stops before candidate activation. A release-branch push
already triggers deployment; do not also dispatch it manually. Record the workflow,
source SHA, image digest and retained configuration identity. See
[Unibase's application procedures](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md).

First GHCR publication can create a private package even when public deployment is
the intended convention. Check the owner's organization package-publishing policy
and the individual package visibility. Enabling public package creation permits
members to publish public packages; it does not automatically publish existing
packages or repositories. Uniwares-LTD's policy and Unibase's package were explicitly
approved and set public on October 25. Retry the same failed release only after
the package is public; anonymous digest verification still runs before host access.

**Expected result:** allowed deploy operations work and arbitrary shell/root/Docker
operations are denied; new app ports/Redis stay private; one healthy candidate runs
under the correct application identity. Existing host services remain healthy.

**Failure/resume:** inspect actual installed revision, accounts, resources and
candidate/prior-release state. Rerun preview and apply only missing compatible steps,
preserving data and credentials. Use the reviewed package rollback for a failed
Compose upgrade; never globally prune Docker or tear down another app. If a first
release fails, stop only its unhealthy candidate, including its workers, and any
candidate timers if present; retain configuration/data and fix/redeploy. There is
no previous release to roll back to. Do not restore the DB or restart shared services.

For compatibility parsing, use each owner's actual Compose interpolation inputs.
Booklet uses the retained release's `runtime.env`; Dify uses
`/etc/kids-booklet/dify/runtime.env`. Honor recorded Compose environment-file labels
when present. Container runtime variables do not reproduce all interpolation values
(for example, the deployment image or published port), and process variables override
`--env-file`. A failed parser invocation without the saved bindings is not evidence
that the candidate Compose version is incompatible. Preserve private diagnostics
under the root-only batch directory; report variable names and checkpoint results,
not rendered configuration or credential-bearing error bodies.

## 3. Verify and hand off

**Owner/location:** agent through application check workflows and public/private
read-only checks; operator completes user-facing authentication only where needed.
Prerequisite: phase 2's actual successful deployment, not a queued workflow.

**Action:** verify login/Firebase helper behavior, web liveness/dependency readiness,
current maintenance and AI-worker health (including disabled-AI status), app Redis,
proxy headers/streaming and the unchanged Booklet/Dify/legacy service health.
Preserve existing lease/retry/accounting behavior; validate it with isolated fixtures,
not real charges or paid provider calls. Do not require future job endpoints/timers.

**Expected result:** record source/digest/config identity, successful checks, routine
deploy/check/rollback entrypoints and protected secret-store references. Routine
operations use the restricted user. Mark initial deployment verified separately
from pending data recovery and consolidation; the operator can identify the current
release and next failure action without reading this conversation.

**Failure/resume:** failed acceptance remains open. Diagnose and use phase 2's
first-release handling, or the verified image/config rollback when a real healthy
predecessor exists. Do not manufacture a second release solely to rehearse rollback.
Keep failed restores isolated and do not resume unhealthy writers automatically.

## After first deployment

Track these explicitly in the [implementation plan](implementation-plan.md):
shared gateway, shared application Redis/logical DBs, app-hosted jobs/timers,
production environment naming and recovery rehearsal. Consolidate in reviewed
increments after first staging works; never silently turn temporary choices into
the permanent architecture.

Manual backup remains required before destructive operations or data migrations.
First startup with fresh staging data does not require a complete backup system;
if a proposed operation affects existing data and backup is unavailable, stop that
operation. Select off-host storage and rehearse DB/GridFS restoration into a named
disposable database before treating staging data as recoverable. Verify a target
is empty or take a pre-restore backup. Shared Firebase identities/Dify are excluded.
Exercise image/config rollback when a real compatible predecessor exists.

Legacy gateway migration, Dify/tunnel ownership transfer, production activation,
Engine upgrades and broad disk cleanup are outside the initial staging path.

## Credentials and access

### Shared operator key handoff

The stable reference name for this key is **`srv1-ops-admin`**. Use that name in
handoffs, credential references and the shared vault item title. It identifies the
existing key, not a new key or SSH profile; no file rename or key rotation is needed.

| Reference | Value |
| --- | --- |
| Key name / suggested vault item title | `srv1-ops-admin` |
| VPS account | `uniwares-ops-admin` |
| Recipient's Windows private-key path | `$env:USERPROFILE\.ssh\uniwares-ops-admin` |
| Optional SSH connection profile (separate from the key name) | `uniwares-srv1-admin` |

Trusted operators use the same `uniwares-ops-admin` account and admin key. The
owner distributes the existing private key through a shared password-manager vault
or another authenticated encrypted channel, limited to authorized operators.
Keep an authoritative protected copy and a recipient list in that store. Shared
keys do not identify individual operators in SSH logs; reliably revoking one
recipient's access requires rotating the shared key for everyone. No per-project key
management system is required.

Share the following:

- Private key file `uniwares-ops-admin` (no extension), through the protected channel.
- Its passphrase, if one was set, as a protected vault field or separate secure message.
  Do not assume that a disabled VPS account password means the key has no passphrase.
- Optional public key file `uniwares-ops-admin.pub`; this alone cannot authenticate.
- Non-secret connection details: host `vps-ae0a9d01.vps.ovh.net`, port `22`, user
  `uniwares-ops-admin`, and verified ED25519 host fingerprint
  `SHA256:Jk5pHbF36TXs3PZ+50CuaX074dLjCd4/Gs7uIrU6vyc`.

On the original Windows workstation, locate the existing key without printing its
contents. Select the private file in Explorer and upload that file directly to the
protected store; do not paste it into chat, logs, Git or a GitHub issue:

```powershell
$opsKeyPath = Join-Path $env:USERPROFILE '.ssh\uniwares-ops-admin'
if (!(Test-Path -LiteralPath $opsKeyPath -PathType Leaf)) {
    throw 'Existing key not found. Locate it; do not generate a replacement.'
}
explorer.exe /select,$opsKeyPath
```

Each Windows recipient obtains **`srv1-ops-admin`** through the owner's secure
channel and saves its private key file as
`$env:USERPROFILE\.ssh\uniwares-ops-admin` in their own protected user profile.
Create `.ssh` if absent; inspect any existing destination before copying and never
overwrite another key. Restrict file access to the recipient; if OpenSSH reports
unsafe permissions, correct the file ACL rather than disabling checks. Keep the
private key outside repository directories and do not add it to repository secrets
merely to make it downloadable. GitHub Actions secrets are workflow inputs, not a
device key-distribution service.

Connect from Windows PowerShell:

```powershell
ssh -p 22 -i "$env:USERPROFILE\.ssh\uniwares-ops-admin" -o IdentitiesOnly=yes -o StrictHostKeyChecking=ask uniwares-ops-admin@vps-ae0a9d01.vps.ovh.net
```

On first connection, compare the ED25519 fingerprint with the verified value above
before accepting. Stop on a mismatch or changed-host warning; never delete pins to
bypass it. Subsequent automation uses `StrictHostKeyChecking=yes`. Once logged in,
run `whoami`, `hostname` and `sudo -n true`. Expected identities are the account and
host above. A sudo password-required result remains expected until reviewed scoped
privileged operations exist; sharing this key does not enable unattended sudo.
Report only results and the local key/profile reference, never the private key or
passphrase. Each device's successful connection must be verified separately.

This admin key is separate from the future restricted deployment key below. Do not
put it into routine application deployment workflows.

### Workflow credentials

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

The October 24 inventory reports 84.23 GB of reclaimable images. First identify each app's
active and retained rollback digests and whether they can be pulled again. Remove
only explicitly selected obsolete images; record a small retention policy when
implemented. Do not blanket-prune images/volumes across all projects. The last observed
41 GiB free disk does not require emergency deletion to begin staging work.

## Minimum staging backup and recovery

Target one manual application workflow with `backup` and `restore` actions.
Back up before migrations or destructive operations, rather than every image
deployment. A manual policy accepts loss since the last successful backup;
production recovery expectations remain a separate decision.

- Include the app MongoDB database and GridFS bytes; verify a private encrypted
  off-host archive, manifest and checksum before declaring success.
- Pause/drain app and worker writers (and timers after their introduction) for a consistent backup/restore. Require an exact
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
