# Staging bootstrap and operations runbook

For new deployments, start with the [named credential inventory and copyable checklist](provider-access.md)
and the application's [initialization procedure](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md).
Public app settings use tracked environment JSON, not Actions variables. Each PR
prepared for publication must state `Operator intervention: none` or identify actions,
owner, execution location, ordering, verification and failure/resume. Image releases
cannot update root-owned tooling or provider bindings. Runtime-secret restoration
and fully unattended initialization remain implementation work. Unibase's guided
setup helper covers credential validation, supported provider bindings and repository
secrets; its deployment guide lists the remaining operator checkpoints.

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

These checkpoints record the basic staging deployment. The optional AI extension
and its acceptance are recorded separately in the current release below.

| Phase | Status | Reviewed revision | Verification | Next action |
| --- | --- | --- | --- | --- |
| 1 Connect and prepare | Verified (preparation only) | Infrastructure `bb041e4`, Unibase `6edc411`, owner `c182b64` | October 24: provider reads, inventory, 47 Linux deployment tests, 10 Infrastructure tests and 3 Terraform mock tests; separate read-only review | Complete; subsequent live acceptance is recorded in Phase 2 |
| 2 Bootstrap and deploy | Verified | Runtime `edcc21d`; Infrastructure installer `90ed66a`; owner route `50536f0` | October 25: plugins/account/control and runtime/index preparation complete; Release `40168299056` attempt 3 and independent Check `40168997418` passed, including anonymous pull, local/public readiness and both workers. Booklet staging returned healthy after its separate owner operation; production/Dify/legacy baseline retained | Complete; use Phase 3 routine instructions and do not repeat bootstrap |
| 3 Verify and hand off | Verified | Corrective runtime `215044b`; handoff guidance in this runbook and the application deployment guide | October 25: account/admin/session/profile/logout checks, operator-reported incognito login/logout and workstation Actions/pinned SSH access verified. Corrective Release `40176352821` and independent Check `40176659441` passed; fresh account/admin loads have no injected decoder or new console errors | Routine staging uses the quick start below. Next: minimum off-host recovery workflow/rehearsal; keep consolidation and production separate |

### Current Unibase release — 2026-10-25

- Staging: <https://unibase-staging.uniwares.co.uk/account>, branch `_staging`.
- Source: `1f19ce3963bbd41588b0972b8d55717a97ed1fb5`.
- Image: `ghcr.io/uniwares-ltd/unibase@sha256:ae8d7bbb5468f1f6ad7f481a9b3c2403a98cdaec34f3ebbb348488e8d30dce9d`.
- Installed control bundle: `4ce4da8ea0c9842330eeb6c96cf41aa26ecbaab6daf16cf6e7a5481ea4482fa2`.
- Tracked staging configuration SHA-256: `c13b8b81304490c768c07b769f1b650215d04211d4ce5504a1029dfa85aac91c`.
- Operator output confirms optional AI/MCP preview, encryption compatibility and
  `AI_CONFIGURATION_PREPARED`. [Release 40188936199](https://github.com/Uniwares-LTD/unibase/actions/runs/40188936199)
  passed on October 25, including anonymous digest pull and deployment health checks.
  Subsequent bounded Dify/MCP/Persona application acceptance also passed;
  the [application acceptance record](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md#ai-activation-and-acceptance)
  owns Run, persistence and accounting evidence. No new release was needed for
  saved application/provider settings.
- Private release snapshots remain under `/opt/unibase/staging/releases/`; `current`
  selects the serving snapshot. The prior release was `215044b` with image
  `sha256:adee7653a0901b7340b300843066f5f7542e86dfa0bc0f569b7bc3dc357848d1`.
  Inspect retained state before rollback; no rollback rehearsal or data restore
  occurred. Operator-update backups preserve previous runtime/control bytes separately.
  Never copy private snapshots or backup contents to Git.

Routine operations use Unibase's own workflows on `_staging`:

```powershell
gh workflow run check-deployment.yml --repo Uniwares-LTD/unibase --ref _staging -f environment=staging
```

A reviewed push to `_staging` triggers Release automatically. Do not also dispatch
the same commit. Use Rollback only when a real compatible healthy predecessor is
retained; the preceding source is recorded above, without claiming a rollback rehearsal.
Secret references are repository Actions
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

### Optional AI configuration update

`scripts/update-app-config.py` is the root-only update interface used successfully
on srv1 on 2026-10-25. It runs from a reviewed operator package, not through routine
SSH dispatch. It preserves account privileges and does not start containers.
Supported scope is staging AI/MCP runtime settings only; base
identity, Firebase, MongoDB, Redis, payments and storage changes are rejected.

The reviewed operator package must include this script and its sibling
`bootstrap-deploy.py`, a checksum-verified immutable app archive and a root-only
JSON private-input file. Required arguments are `--project`, `--expected-revision`
(currently installed bundle SHA-256), `--bundle`, `--sha256` and `--private-input`.
Preview first; `--apply` selects the validated runtime/control bundle. Concrete
host commands/checksums are generated only after bindings and the revision are reviewed.

The tool takes the existing application operation lock, checks candidate config and
the live database for existing encrypted credentials/active capabilities before first
encryption-key installation. It refuses encryption changes while Dify/MCP writers
are enabled. General key migration is outside this interface. A running app container
with the MongoDB Node module is required for the read-only compatibility probe.

The private input accepts only `DIFY_MANAGEMENT_KEY`,
`DIFY_CREDENTIAL_ENCRYPTION_KEY`, `PERSONA_COMPLETION_API_KEY`, and referenced
`DIFY_KEY_*`/`MCP_TOKEN_*` credentials. No local environment file is an input.
During apply, registration is temporarily invalidated to refuse new dispatch until
runtime and control selection agree. A private `config-update-pending` journal under
the app state directory records original bytes; caught failures restore them.
After an interrupted process, inspect state and invoke the same reviewed tool with
`--project`, the previous `--expected-revision`, `--recover --apply` before retrying.
Recovery preserves data and running containers. Successful updates retain a private
`config-previous-<bundle digest>` directory; do not publish or automatically delete it.

Application release follows separately using the matching reviewed configuration.
Before release, the old containers still serve their old snapshots. On failed release,
inspect automatic image/config restoration and coordinate operator configuration
recovery; never automatically restore MongoDB or change unrelated services.

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

## Deployment preflight

The repository now implements a read-only `preflight` action in dispatcher protocol
version 1. Installation on srv1 is pending; source availability is not live acceptance.
Install the reviewed dispatcher before enabling mandatory application preflight.
Existing deploy/check/rollback requests remain supported.

A preflight request has exactly `version`, `project`, `environment`, `action` and
`configurationHash`. Only staging is accepted. The response is bounded JSON with
`version: 1`, `code`, `compatible`, `installedRevision`, `installedConfigurationHash`
and `requestedConfigurationHash`. Unknown identities are null. `COMPATIBLE` exits 0;
rejections exit 2; unexpected internal failures exit 1. Codes are `COMPATIBLE`,
`CONFIGURATION_MISMATCH`, `INVALID_REQUEST`, `MISSING_REGISTRATION`,
`UNTRUSTED_CONTROL`, `IMAGE_REPOSITORY_MISMATCH` and `INTERNAL_FAILURE`.
Preflight never executes application control scripts or modifies registration/runtime.
Hashes identify public configuration only; no private settings or exception text are
returned. Deploy independently revalidates registration/configuration immediately
before invoking installed control code. Preflight reserves no state and grants no
permission to update configuration.

**Operator intervention required for dispatcher rollout:** the trusted srv1 operator
installs the checksum-verified controller bundle and explicit trust using the installer
described below, retaining the previous executable for recovery. The
bootstrap installer deliberately refuses changed existing files and must not be replayed
for this update. Prepare the exact operator batch only after current installed checksum
and candidate revision are known; preserve registrations, keys and sudo rules. This
document authorizes no installation.
Verify matching and mismatching read-only requests, then an existing restricted check.
Only afterwards promote the application's mandatory preflight change. If installation
or verification fails, retain/restore the previous dispatcher and defer application
promotion. Do not bootstrap providers or replace application registrations to install
this behavior.

### Permission-correction recovery

Unibase run 41177847093 built/published its image but was rejected by the dispatcher.
The successful parent projected host hash was
`c13b8b81304490c768c07b769f1b650215d04211d4ce5504a1029dfa85aac91c`;
the permission correction projects to
`3be35b4456ec3086cb65ed82bc8a8bc3ecd7d634fc0dabaebae5974dce2f0d1c`.
The recorded installation matches the former. This supports an uninstalled operator
update; the old generic exception does not prove its precise cause. The available
operator account cannot read the protected registration without password-based sudo.
Privileged readback of registration/hash and existence of a config-update-pending
journal is pending. Do not publish journal contents or private runtime files.

After confirmed readback, prepare the reviewed immutable application bundle using
its host_configuration projection, preview/apply the existing update-app-config.py
interface with the exact current revision, and retain credentials/encryption bytes.
If pending recovery exists, inspect and recover before retry. Publish/install/release
only with separate authorization. Application acceptance and Dify catalog/owned-Run
checks remain in Unibase's deployment guide. Do not rewrite dated release records as
current facts before verification.

### Projected bundles and version-2 execution

The bundle builder now accepts only a full immutable commit containing the supported
`deploy/contract.json`. It interprets that data with Infrastructure-owned code, strips
image-owned fields before creating the archive, and writes a sibling manifest with
source commit, contract version, configuration hashes, checksum and capabilities.
The bundle and manifest are a review pair. Never use a raw git archive as the operator
configuration update bundle. Existing source revisions without a contract must first
receive the reviewed contract change; the builder does not guess an old projection.

Version 2 currently supports the existing deploy/check/rollback/preflight request
shape and external targets staging/prod (prod maps to retained production paths).
It requires an installed bundle declaring operation-lock-v1. Preflight rejects old
bundles. The dispatcher acquires the existing per-application operation.lock before
registration validation, then inherits that descriptor into the application script.
Version 1 retains its existing execution behavior and is not claimed race-free.

Lock acquisition waits at most 300 seconds; execution waits at most 1200 seconds.
Timeout or handled interruption kills and reaps the process group before releasing
the lock. The root-private `/var/lib/<project>/operation-status.json` is atomically
written with unknown before execution, then completed or failed after a known return.
An abrupt termination therefore leaves unknown. This is not readiness evidence after
subsequent host changes. Do not retry unknown operations until privileged readback of
actual containers, selected release and pending configuration journals resolves them.
Source includes the status/approval workflow described below; installation remains pending.

## Approved plan operations

Version 2 adds capabilities, plan, apply and status plus manual backup/restore plan
preparation. Application clients send fixed JSON through the restricted account.
Preparation reads installed configuration under the application lock, verifies the
checksum-bound source bundle, derives changed setting names and credential references (including control.bundle for
application control-script/template updates),
and stores an immutable canonical plan under `/var/lib/<app>/operation-plans`.
No candidate code runs during preparation. Provider and data-migration executors are
unsupported and return OWNER_ACTION_REQUIRED. Existing optional AI/MCP settings use
the bounded updater; other host changes require an explicit executor extension.

The plan binds source/image/bundle/configuration identities, observed registration
and running release identity, ordered operations, interruption and recovery guidance.
Its SHA-256 digest is both plan ID and approval audience. Host changes after preview
require a fresh plan. Root-private journals record intent before mutation and completed
checkpoints afterward. One-use JWT IDs reject replay. A fresh workflow dispatch may
resume completed checkpoints; uncertain writes require conclusive readback. Workflow
reruns are rejected because actor identity alone cannot establish who clicked rerun.

### Initial trust and controller installation

This is a one-time reviewed operator action, not an application release. First obtain
sanitized privileged readback of installed dispatcher SHA-256, application registration,
projected profile hash, current release identity and presence (not contents) of pending
configuration journals. Resolve existing journals before changing tooling. Do not replay
bootstrap on installed applications. New-host bootstrap installs a fail-closed placeholder;
complete controller/trust installation before accepting requests.

Build with `python scripts/build-controller-bundle.py CHECKOUT REVIEWED_FULL_COMMIT OUTPUT.tar`
from the Infrastructure workstation checkout. The output manifest binds the archive to
the exact source commit. Securely transfer the reviewed archive, manifest, installer
and reviewed `config/approval-trust.example.json` to the operator. On the host,
`python3 controller-install.py --bundle OUTPUT.tar --sha256 MANIFEST_CHECKSUM --expected-dispatcher-sha256 READBACK_CHECKSUM --trust approval-trust.json`
is a preview; append `--apply` only for the separately authorized installation. These
identities are generated/read-back inputs; never substitute an unreviewed working tree.
The installer needs Python venv support and access to pinned Python package dependencies.
It keeps a root-owned immutable controller directory/venv, atomically replaces the
fixed dispatcher, and retains the previous executable. It preserves account/key/sudo
rules and refuses unreviewed trust replacement. Dependency installation can resume
without switching the executable prematurely.

The trust example records the user-selected Admin team membership as of 2026-10-31:
Amir-Ahani, sinasava, alivahidd, uniwares-uk and Mehdi-varm (numeric IDs in JSON).
Changes in team membership require reviewed explicit enrollment changes. No team or
organization permission was changed. Trust restricts repository/owner IDs, main,
workflow_dispatch, first run attempt, exact reusable workflow revision, token expiry,
RS256 GitHub issuer and audience `uniwares:plan:DIGEST`. Verification uses pinned PyJWT
and cryptography. Before acceptance, verify the actual claims emitted by the pinned
workflow against this configuration; synthetic signed-token tests are not live proof.

Configure Infrastructure's DEPLOY_SSH_PRIVATE_KEY with its restricted deployment key
and DEPLOY_SSH_HOST_KEY with the independently verified pinned host key (key-only or
an exact host-prefixed known_hosts line). Never install srv1-ops-admin in Actions.
Reviewed `config/approval-targets.json` binds each app/target to its host. Production
is deliberately absent until its separate activation review. No Docker socket or
general sudo is granted to workflows.

### Prepare, approve, apply, inspect

The application **Prepare protected deployment** workflow builds once, anonymously
verifies the immutable image and returns the host-stored plan and digest. Review the
changed names, credential references, identities and interruption/recovery steps.
An enrolled admin dispatches Infrastructure **Apply deployment plan** on main with the
plan ID and matching digest. Its reusable executor and checked-out client are pinned
to immutable commits. Host validation, not workflow visibility, enforces authorization.
Supported configuration application preserves existing credentials/encryption bytes,
then continues the exact associated image deployment under the same application lock.
Never reconstruct or upload privileged shell commands for a prepared plan.

Application `deploy:ops status TARGET --plan-id DIGEST` reports sanitized checkpoints.
Lost SSH, timeout or interruption means unknown until inspection. Deployment subprocess
groups are terminated/reaped before releasing the lock; recovery subprocesses have
bounded waits and the same cleanup. No automatic database restoration occurs.
Application rollback restores its retained release snapshot. Protected host-runtime
predecessors remain at config-previous-CHECKSUM for explicit operator recovery; inspect
the journal and installed/serving identities before choosing a recovery direction.
Do not retry an uncertain provider write or manually delete replay records.

Subsequent controller updates use the same approval path: build the immutable controller
archive, run the application's `deploy:ops plan TARGET --bundle OUTPUT.tar --manifest OUTPUT.tar.manifest.json --image CURRENT_IMMUTABLE_IMAGE --controller-checksum OBSERVED_DISPATCHER_SHA256`,
review and approve. The installer serializes global replacement, checks the expected
predecessor and atomically retains it. Trust changes remain a separate operator action.

### Manual encrypted MongoDB and GridFS recovery

Install reviewed MongoDB database tools and restic before enabling recovery. The operator
creates root-private `/etc/<app>/<staging|production>/recovery.json` containing exactly
repository (`s3:https://...`), passwordFile, accessKeyId, secretAccessKey, mongoUri and
database. Use separate recovery credentials and a root-private restic password file;
initialize the encrypted S3-compatible repository once with the recovery owner. Never
put these values in plans, artifacts or Git. The database must match the app environment.

Application backup/restore commands prepare plans for the same Infrastructure approval.
Backup pauses only previously running app/worker/ai-worker writers, creates a whole-db
MongoDB archive including GridFS, records its hash/identity, uploads through restic and
checks the repository, then restarts those writers. Restore requires a full snapshot
ID and explicit destination; it takes a fresh destination backup first, validates the
selected archive and remaps namespaces explicitly. Only the configured database or
its `_rehearsal_NAME` database is allowed. Rehearse against a disposable destination
before production acceptance and verify web, both workers and data afterward.

There are no schedules and no retention/prune operations. Keep backups until separately
reviewed retention work. Destructive migrations are not implemented by this executor;
their named owner must provide a fresh verified backup and explicit recovery acceptance.
Ordinary releases use backward-compatible migrations and never restore data automatically.

### Rollout acceptance and ownership

Install/verify the compatible controller first, then the projected permission correction
and application control capability, then enable version-2 clients. Verify staging before
production activation. Preserve legacy production paths/resource/database identities;
external prod maps to production runtime. Disable old general-sudo access only after
migration verification under a separately authorized access change. Verify matching and
mismatching preflight, exact runtime credentials preservation, web and both workers,
readiness, Dify catalog permissions and serving identity. Any owned Run retry is separate.
Implementation/publication is not installation, deployment or live acceptance.
