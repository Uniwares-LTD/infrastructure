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
| 3 Verify and hand off | In progress | Runtime `edcc21d` | October 25: Google admin login user-confirmed; session/profile persistence, admin access, logout/re-login and fresh Check `40170666438` verified. Detailed authentication results live in Unibase | Incognito login/logout reported complete; resolve Cloudflare rewriting/CSP hydration errors before Phase 3 acceptance |

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

Post-deploy shared-host baseline verification is complete; its dated evidence is
in the [inventory](inventory/srv1.md). Reuse it unless a new shared-host change
could affect existing services. Routine Unibase acceptance checks its own app.

The goal is one access handoff, one consolidated input request and one authorization
for concrete live changes. Provider consent/authentication may still need operator
input. Honor existing scope authorization; stop for unexpected destructive changes.

## 1. Connect and prepare

Completed for srv1. See the [reviewed bootstrap procedure](history/completed-bootstrap-2026-10-25.md#1-connect-and-prepare). Do not rerun completed setup.

### Establish access

Completed for srv1. See the [reviewed bootstrap procedure](history/completed-bootstrap-2026-10-25.md#establish-access). Do not rerun completed setup.

### Complete targeted discovery and required implementation

Completed for srv1. See the [reviewed bootstrap procedure](history/completed-bootstrap-2026-10-25.md#complete-targeted-discovery-and-required-implementation). Do not rerun completed setup.

#### Scoped privileged discovery

Completed for srv1. See the [reviewed bootstrap procedure](history/completed-bootstrap-2026-10-25.md#scoped-privileged-discovery). Do not rerun completed setup.

## 2. Bootstrap and deploy

Completed for srv1. See the [reviewed bootstrap procedure](history/completed-bootstrap-2026-10-25.md#2-bootstrap-and-deploy). Do not rerun completed setup.

## 3. Verify and hand off

**Owner/location:** agent via Unibase Actions/browser checks; operator handles
credentials/MFA and confirms access to Actions and the protected shared key.
Prerequisite: actual Phase 2 deployment. Collect remaining manual checks together.

Follow [Unibase's acceptance record](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md#phase-3--verify-and-hand-off)
for login/session/profile/admin/logout, web/dependencies/current workers, Firebase
helper and proxy checks. Preserve optional-provider disabled modes and use isolated
fixtures for accounting/retry invariants. Do not introduce paid calls, job endpoints
or new timers. Reuse the completed shared-host baseline unless new shared changes
warrant another check.

**Expected result:** passing app acceptance, installed release identity above and
usable routine instructions below. Mark the progress row verified only after all
required checks pass; distinguish later backup/rollback/consolidation work.

**Failure/resume:** preserve working services and app data; resume the failed check.
Record a sanitized diagnostic, source/digest and workflow URL. Follow the applicable
first-release or predecessor procedure below; never automatically restore a DB.

### Routine operator quick start

Run from a workstation with GitHub CLI authenticated for `Uniwares-LTD/unibase`,
or use the corresponding workflow's **Run workflow** form in GitHub Actions.
The runner uses protected repository secrets; no local deploy key is needed for
routine workflow operation. Actions access and SSH operator access are separate.

| Task | Action and verification |
| --- | --- |
| Identify serving release | Read this runbook's source/digest/config record; run Check and compare its reported serving commit/image with that record |
| Check | Run the command below; open its exact run URL and require terminal success with healthy app, dependency and worker checks |
| Deploy | Review and authorize the application revision; publish that revision to `_staging` once. The automatic Release builds/publishes, proves anonymous digest pull and deploys. Record terminal result and serving identity; do not also dispatch the same release |
| Roll back | Only with a retained compatible healthy predecessor, select `_staging` in Restore previous Unibase release with `environment=staging`. Inspect current/predecessor state first; rollback may change the serving release and config but never restore the DB |
| Privileged maintenance | Use the separately authorized trusted root/operator procedure. `srv1-ops-admin` currently grants only fixed discovery sudo; routine deploy has neither general sudo nor Docker-group access |

```powershell
gh workflow run check-deployment.yml --repo Uniwares-LTD/unibase --ref _staging -f environment=staging
gh run list --repo Uniwares-LTD/unibase --workflow check-deployment.yml --limit 1
# Use the ID for the exact run you just dispatched, not a concurrent operator's run:
gh run view RUN_ID --repo Uniwares-LTD/unibase --exit-status
```

`gh run view --exit-status` reports a completed run; a queued/running run is not
acceptance. Inspect its status and wait for that same run rather than dispatching
another operation. Use `gh run watch RUN_ID --repo Uniwares-LTD/unibase --exit-status`
in an operator terminal when desired. Agent polling remains bounded.

**Failure routing:** a failed build/publish/anonymous pull makes no host deployment.
An uncertain client timeout requires inspecting the same run and restricted Check
before retrying. With no predecessor, failed deployment stops only its candidate
app/workers (and candidate timers if present); preserve config/data and correct the
cause. After a later release, inspect whether automatic image/config restoration
already succeeded before selecting manual Rollback. Never repeat bootstrap to fix
an application release failure. Root-owned control/config changes require a reviewed
operator bundle update; pushing an image cannot replace the installed control code.

**Secret references:** see [workflow credentials](#workflow-credentials),
[provider access](provider-access.md) and the
[shared operator key handoff](#shared-operator-key-handoff). Records contain names,
consumers and locations, never values. Keep the shared vault's protected copy and
recipient list authoritative; do not make keys downloadable from GitHub.

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

This admin key is separate from the installed restricted deployment key below. Do not
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

Compose 5.6.1 and Buildx 0.38.1 were installed and compatibility-checked on
October 25; Docker Engine 27.0.3 was retained. The operator parsed active projects
with their actual environment bindings and passed disposable create/start/health/remove
checks before installation. Retained packages allow plugin rollback. For future upgrades:
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
