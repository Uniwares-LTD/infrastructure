# Host operations

## Routine operation

Use the application's release/check/rollback interface for routine releases.
Infrastructure owns host access, installation, approval trust, protected updates,
maintenance and privileged recovery. Application release identity and functional
acceptance belong in the application's deployment guide.

| Task | Procedure |
| --- | --- |
| Check an existing application | [Routine operator quick start](#routine-operator-quick-start) |
| Install a new application | [Connect and prepare](#1-connect-and-prepare), then bootstrap |
| Update an existing controller | [Initial trust and controller installation](#initial-trust-and-controller-installation) |
| Update protected configuration | [Approved plan operations](#approved-plan-operations) or reviewed [operator update](#optional-ai-configuration-update) |
| Resolve disk pressure | [Image retention](#image-retention) |
| Recover an uncertain operation | [Prepare, approve, apply, inspect](#prepare-approve-apply-inspect) |
| Restore application data | [Manual encrypted recovery](#manual-encrypted-mongodb-and-gridfs-recovery) |

Never replay bootstrap to update an existing registration. Keep private runtime files,
credentials and recovery snapshots outside Git. Documentation changes require no host
installation. Booklet, Dify and tunnel ownership remains with their existing owner.

## Configuration and progress

The [host inventory](inventory/srv1.md#installed-control-and-capacity--2026-10-31)
owns installed identities and dated capacity observations. The [credential inventory](provider-access.md)
owns protected references; request missing references together without printing values.
For new projects use the application's initializer and reviewed allocation/provider preview.

October 31 installation and configuration correction are verified. Application release
and check evidence is canonical in [Unibase's current release](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md#current-staging-release).
Remaining acceptance: actual OIDC approval workflow claims, recovery configuration and
rehearsal, timer activation, production activation and project tracking access.
Shared gateway/Redis/worker consolidation remains deferred.

### Current Unibase release — 2026-10-25

Historical anchor retained for existing links. Use [Unibase's current release](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md#current-staging-release)
for serving source/image and acceptance; [historical evidence](history/deployment-evidence-2026-10-25.md)
preserves the earlier bootstrap and release observations.

## 1. Connect and prepare

For a new host/application, gather the [named public inputs and credential references](provider-access.md), verify transport, privilege, capacity and allocations, and prepare a reviewed immutable installation batch for that target. Use the application initializer for bindings. The [historical bootstrap procedure](history/completed-bootstrap-2026-10-25.md#1-connect-and-prepare) is evidence, not a ready-made batch for another host. Setup is complete for srv1; do not rerun it.

### Establish access

Completed for srv1. See the [reviewed bootstrap procedure](history/completed-bootstrap-2026-10-25.md#establish-access). Do not rerun completed setup.

### Complete targeted discovery and required implementation

Completed for srv1. See the [reviewed bootstrap procedure](history/completed-bootstrap-2026-10-25.md#complete-targeted-discovery-and-required-implementation). Do not rerun completed setup.

#### Scoped privileged discovery

Completed for srv1. See the [reviewed bootstrap procedure](history/completed-bootstrap-2026-10-25.md#scoped-privileged-discovery). Do not rerun completed setup.

## 2. Bootstrap and deploy

For a new registration, use the reviewed `scripts/bootstrap-deploy.py` interface and application preparation procedure after discovery. Install compatible controller/trust and an explicitly reviewed maintenance policy before enabling clients that require them. Existing srv1 registrations instead use the update paths in this guide. The [completed bootstrap record](history/completed-bootstrap-2026-10-25.md#2-bootstrap-and-deploy) preserves prior evidence; do not replay its machine-specific commands.

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

**Expected result:** passing app acceptance, the application deployment guide's serving identity and
usable routine instructions below. Record acceptance only after all
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
| Identify serving release | Read the application's release record and Infrastructure's installed-state inventory; run Check and compare the serving commit/image |
| Check | Run the command below; open its exact run URL and require terminal success with healthy app, dependency and worker checks |
| Deploy | Review and authorize the application revision; merge a promotion PR from main into `_staging` once. The automatic Release builds/publishes, proves anonymous digest pull and deploys. Record terminal result and serving identity; do not also dispatch the same release |
| Roll back | Only with a retained compatible healthy predecessor, select `_staging` in Restore previous Unibase release with `environment=staging`. Inspect current/predecessor state first; rollback may change the serving release and config but never restore the DB |
| Privileged maintenance | Use the separately authorized trusted root/operator procedure. The key-only operator has passwordless fixed discovery; its broad sudo entry requires authentication unavailable with the disabled password. Do not enable a password to obtain broad sudo; use the existing authorized root session for installation. Routine deploy has neither general sudo nor Docker-group access |

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

The installed policy enrolls only Unibase. Automatic cleanup and the timer remain
disabled; installation is not activation. See the [dated capacity and enrollment record](inventory/srv1.md#installed-control-and-capacity--2026-10-31).
A one-time authorized Booklet cleanup used a 72-hour threshold with current/previous
and container protections; it did not change the policy below or enroll Booklet.

### Policy and protection

Infrastructure owns /etc/uniwares-infrastructure/image-retention.json and the fixed
/usr/local/sbin/uniwares-image-maintenance command. The
[example policy](../config/image-retention.example.json) enrolls Unibase and Unitale
(Unitale owner-approved 2026-11-27), maps staging/prod explicitly, and disables automatic cleanup. Derived-project proposals
grant no enrollment. Other applications require their owners' explicit review.

Retain three distinct successful snapshots per environment and fourteen days of
activations. Rollback records another activation, not another distinct snapshot.
Always protect current/previous selections, every running/stopped container reference,
and unresolved operation plans. Prepared/failed plans never age out. Pending configuration
recovery, unknown deployment state, corrupt state or uncertain ledger recording blocks
deletion. Explicit legacy review overrides missing activation evidence only, never
current/previous, container or pending-operation protection.

Only allowlisted application references are eligible. Cross-repository references and
unowned/dangling images are not removed. Private snapshots, controller predecessors,
configuration backups, volumes and data remain untouched. Historical snapshots outside
retention may require an image pull; status reports cached availability.

### Initial cleanup and installation

First obtain the privileged controller/registration/configuration/release readback and
check pending journals under Initial trust and controller installation. Do not replay
bootstrap. Transfer the reviewed image_maintenance.py, install-image-maintenance.py
and policy from the exact reviewed Infrastructure revision. Prepare their exact paths
and SHA-256 identities in the workstation handoff once that revision is fixed.

The installer accepts --source, --sha256, --policy and optional
--expected-policy-sha256. It previews by default; --apply installs the checksum-bound
module, fixed command, policy and systemd units. Updating an existing changed policy
requires its observed checksum. Standalone installation supports manual cleanup before
controller replacement. No account/sudo changes are needed. Installation never starts
or enables the timer or changes an existing timer's activation state.

After authorized installation, run in the root Ubuntu session:

~~~bash
/usr/local/sbin/uniwares-image-maintenance preview unibase
/usr/local/sbin/uniwares-image-maintenance status unibase
~~~

Preview saves /var/lib/unibase/image-maintenance-preview.json and returns its digest,
candidate references, protection reasons, ownership inventory and filesystem measurements.
Review the exact candidates before invoking apply unibase --digest with that digest.
For explicitly reviewed legacy images, repeat preview with one --legacy-reference per
immutable reference; the resulting digest binds those exceptions. Never blanket-prune,
force removal or delete overlay2 directories directly.

Manual apply removes only the reviewed candidate set. Each reference is revalidated
against current containers, snapshots, plans and policy immediately before deletion.
Changed state requires a new preview. Automatic cleanup stops once every checked
filesystem has 30 GiB free; no protection is relaxed to meet that target. If free space
remains below 20 GiB, stop release and use the ownership inventory to request other
owners' cleanup or capacity expansion. Measure actual recovered space after deletion.

### Deployment and timer

Install compatible Infrastructure tooling/policy first, then the application control
bundle declaring image-retention-v1. New requests bind required capabilities. Old
clients remain supported but are not claimed to have retention protection.
Both direct root and dispatcher paths acquire the application lock before the shared
image lock and hold them through pull, readiness and release-ledger recording.

Check Docker's actual data-root and release/state filesystems, deduplicated by device.
Require 20 GiB free before pulling and again before container replacement; this floor
does not guarantee that an arbitrarily large image fits. Warn at 80% usage. Failed
pulls or low-space checks preserve the running release. A failed ledger/cleanup step
reports maintenance separately and must not restore an otherwise healthy release.

After manual cleanup and staging release verification, explicitly review a policy
update enabling Unibase automatic cleanup, install it with the prior policy checksum,
and obtain timer activation authorization before running:

~~~bash
systemctl enable --now uniwares-image-maintenance.timer
systemctl list-timers uniwares-image-maintenance.timer
~~~

The daily timer runs at 03:00 UTC, with up to thirty minutes of jitter and persistent
missed-run handling. The service has a ten-minute timeout and kills its control group.
It processes enrolled applications individually, skips busy locks and uses the same
implementation as post-release cleanup. Backups remain manual.

### Failure and recovery

status unibase, or the application command npm run deploy:ops -- maintenance staging,
reports disk pressure, cached snapshots and the last maintenance outcome.
Root-private image-maintenance-status.json records intent before removal and completion
afterward. A timeout/disconnection means outcome unknown. Inspect current inventory
and status, then create and approve a fresh preview; automatic retries stop on uncertainty.

If image-ledger-pending.json exists, verify selected identity and readiness before
using record unibase --environment staging (or prod) in the root session. Corrupt
ledger or pending configuration recovery requires owner investigation, not deletion
of blocker files. Command updates retain their predecessor; disable the timer before
investigating repeated failures. Database restore is never image-cleanup recovery.

## Minimum staging backup and recovery

Manual encrypted MongoDB/GridFS backup and restore are implemented through the
[approved recovery interface](#manual-encrypted-mongodb-and-gridfs-recovery). Configure
the off-host destination, encryption-key recovery and separate database credentials,
then rehearse restoration to a disposable database before claiming recovery acceptance.
These live prerequisites remain pending. Do not automatically restore data after an
image deployment failure. Runtime-secret recovery remains separate; shared Firebase
identities and Dify infrastructure are outside an application database restore.

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

The installed dispatcher supports read-only `preflight` in protocols 1 and 2.
Unibase uses version 2 with `requiredCapabilities`; legacy version-1 clients remain
supported. Requests carry `version`, `project`, `environment`, `action` and
`configurationHash`; version 2 can also bind `requiredCapabilities`. Version 1 accepts `staging`; version 2 accepts
`staging` and `prod`. Responses carry the request protocol version, `code`,
`compatible`, `installedRevision`, `installedConfigurationHash` and
`requestedConfigurationHash`. Unknown identities are null. `COMPATIBLE` exits 0,
rejections exit 2 and internal failure exits 1. Error codes are allowlisted by the
dispatcher; private exception text is suppressed.
Preflight never executes application control scripts or modifies registration/runtime.
Hashes identify public configuration only; no private settings or exception text are
returned. Deploy independently revalidates registration/configuration immediately
before invoking installed control code. Preflight reserves no state and grants no
permission to update configuration.

**For a new or unmigrated host:** the trusted srv1 operator
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
The October 31 privileged readback confirmed the former installed hash. The reviewed
operator update installed the corrected profile and compatible application bundle;
preflight and the subsequent staging release/check passed. See the [installed identities](inventory/srv1.md#installed-control-and-capacity--2026-10-31)
and [application acceptance](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md#current-staging-release).
The mismatch is resolved; Dify functional acceptance remains pending. Do not replay
this correction or an owned Run as routine setup.

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
The controller and trust are installed. Actual emitted OIDC claims and an approved-plan live execution remain unverified.

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
The installer needs working Python venv/ensurepip support and access to the pinned
Python package dependencies. Importing `venv` alone is not a sufficient prerequisite
check. In the root Ubuntu terminal, verify a disposable environment before installation:

```bash
(
  set -euo pipefail
  probe="$(mktemp -d /root/controller-venv-check.XXXXXX)"
  trap 'rm -rf -- "$probe"' EXIT
  python3 -m venv "$probe/venv"
  "$probe/venv/bin/python" -I -m pip --version
)
```

On the recorded Ubuntu 24.04/Python 3.12 host, missing ensurepip was resolved with
`apt-get update` and `apt-get install --no-install-recommends python3.12-venv` in the
root session. Review package changes before accepting; a reboot is separate maintenance.

If installation fails, inspect dispatcher checksum, candidate directory,
`dependencies-ready`, dependency import success and trust-file presence without
printing credentials. The October 31 failure left the old dispatcher selected and a
partial venv without pip. After fixing that prerequisite, the same reviewed installer
resumed successfully with its original expected dispatcher checksum. Never delete the
candidate or predecessor blindly, bypass a changed checksum, or replay bootstrap.
An error after replacement needs readback before deciding whether to retry.
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
A known deployment failure can resume only after the prior selected release is proven
healthy; completed configuration checkpoints are reused. Other uncertain writes require
operator readback. Application rollback restores its retained release snapshot. Protected host-runtime
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
its `_rehearsal_NAME` database is allowed. Before the destructive restore starts,
the status record retains the pre-restore backup ID. If restore fails or is interrupted,
application writers stay stopped; inspect the unknown outcome and recover explicitly
before restarting them. Failures before any database write restart the previous writers.

When a recovery operation resumes the app writer, the controller validates and reloads
its running Compose ingress so Nginx resolves the current app address. Other stopped
services remain stopped. Migration completion still requires the existing readiness check.

Rehearse against a disposable destination
before production acceptance and verify web, both workers and data afterward.

There are no schedules and no retention/prune operations. Keep backups until separately
reviewed retention work. Destructive migrations are not implemented by this executor;
their named owner must provide a fresh verified backup and explicit recovery acceptance.
Ordinary releases use backward-compatible migrations and never restore data automatically.

<a id="proposed-reusable-backup-and-migration-workflows"></a>

### Reusable backup and migration workflows

[Unibase #62's implementation contract](https://github.com/Uniwares-LTD/unibase/blob/main/docs/features/deployment-data-operations/implementation-plan.md#implementation-contract)
is implemented in the local task branches. These source changes are not installed on
srv1. Existing dated host/controller identities remain unchanged. Publication, immutable
workflow/source pin updates, separately approved controller/app-control installation,
actual approval-claim acceptance and isolated target restore rehearsal precede live use.
Production activation and provider/trust-member changes remain outside this work.

`data-operations-v1` extends version 2 with fixed `migrations` (read-only report) and
`migrate` (prepare only) actions. Existing v1/v2 shapes remain valid. New backup and
migration preparations bind a canonical request UUID; same-input retry returns the
same immutable plan, different inputs are rejected, and fresh requested work uses a
fresh identity. A no-pending report creates neither plan nor backup, after checking
unresolved recovery first. Full approval batches are never truncated to fit transport.

For new data-capability backup/migration plans, the existing
`expected.configurationHash` binds public configuration plus protected runtime,
recovery/password files and controller Python/probe bytes. Preparation and apply
recompute it; drift requires a fresh reviewed plan. Top-level protocol
`configurationHash` remains the public configuration hash. Only digests are exposed;
no private settings are serialized and no second approval engine is introduced.

Preparation anonymously pulls the exact configured repository digest, checks OCI
revision/source labels, and extracts/hash-checks static manifest/runner bytes from an
unstarted container. The installed Node/MongoDB probe runs in the currently approved
image with a fixed overridden entrypoint; unavailable executable/module prerequisites
need owner action. No candidate code executes before approval and no driver is installed
as a fallback. Restricted report/status details are paged; clients retain complete
reviewed details as artifacts.

Use the application's report/prepare/status workflow and this repository's existing
Apply deployment plan workflow on the reviewed published `main`, with configured
project/environment and exact plan ID/digest. Publishing a new executor requires updating
its immutable reusable-workflow and checkout pins and validating the corresponding
OIDC executor identity under separate installation authority. Preserve enrolled actors.
No extra apply workflow or approval service is added.

The executor holds application lock first, then one renewable migration lease through
backup and apply. It journals the original writer set, stops it only after runner
readiness, verifies retrieval and identity/hash of the whole-database/GridFS archive,
then persists backup and application-data write intent **before** sending the
`backup-verified` acknowledgment. The runner has private pipes, configured networking,
non-root execution and no host-control mounts/socket. Each phase is capped at 30 minutes;
the total operation is capped at 60 minutes, reserving bounded finalization time.
Timeout/interruption kills/reaps children and removes the named runner before unlock.
Uncertain writes never restart writers automatically. A proven pre-write failure with
restored writers and healthy serving state is failed-but-safe, not a forced root task.

`data-operation-resolution.py` is one root-only utility in the installed reviewed
controller bundle. It accepts only configured project/environment and original plan ID:

```text
python3 -IB CONTROLLER/scripts/data-operation-resolution.py --project PROJECT --environment ENVIRONMENT --plan-id PLAN_ID --inspect
python3 -IB CONTROLLER/scripts/data-operation-resolution.py --project PROJECT --environment ENVIRONMENT --plan-id PLAN_ID --record --expected-state-hash STATE_HASH --disposition safe-to-retry --operator OPERATOR --reason REASON
```

`CONTROLLER` is the immutable installed bundle from the inventory/registration; obtain
all capitalized identities from that installation and the original journal/inspection,
not from arbitrary paths or database inputs. Root recovery must be separately authorized.
The utility never migrates, restores a database or restarts services. Inspect original
plan/journal/image/ledger/backup, predecessor process/container, writers and health; it
acquires the existing database lease and runs only original-image read-only verifiers.
After any separately authorized manual recovery, repeat inspection and record its exact
state hash. The operator/reason explicitly attest a safe serving baseline for any
unrecorded partial work. `safe-to-retry` permits a freshly approved remaining batch;
when all original IDs were written, use `verified-complete`, requiring full verifier,
backup, writer and health proof. Missing evidence or drift refuses acknowledgment.
The atomic root-owned mode-0600 resolution binds original identities and results,
excludes sampling/own-lease renewal times, preserves original history, reads back an
identical retry and rejects conflicting replacement or original-plan reapplication.

Both routine and protected activation use the same authoritative gate immediately
before candidate startup under the inherited application lock. Required pending IDs,
unresolved writes or missing/corrupt verifier/recovery evidence block activation even
when the ledger has zero pending entries. Only newly recorded IDs in this flow require
its host verifier evidence; existing ledger records remain the reviewed legacy baseline.
A terminal MongoDB report copy is optional evidence, never approval or activation
membership. Missing copies do not override complete host evidence; completed-looking
copies cannot override an unresolved host journal. Original failed/unknown outcomes
remain unchanged when resolution metadata is copied. No periodic synchronization,
retention job, generic resume engine or verification-only apply plan is introduced.

Operator intervention for publication: publish reviewed Handbook first, regenerate
consumer references from that revision, then publish pinned-compatible Infrastructure
and application artifacts. Separately authorize/install the controller and app-control
capability before enabling clients. Verify actual approval claims and target recovery
prerequisites/restore rehearsal. Finally authorize a fresh Unibase staging readback/run
and record backup, ledger, health and affected-flow evidence. Do not repeat completed
bootstrap or treat source checks as installed/live acceptance.

### Rollout acceptance and ownership

Install/verify the compatible controller first, then the projected permission correction
and application control capability, then enable version-2 clients. Verify staging before
production activation. Preserve legacy production paths/resource/database identities;
external prod maps to production runtime. Disable old general-sudo access only after
migration verification under a separately authorized access change. Verify matching and
mismatching preflight, exact runtime credentials preservation, web and both workers,
readiness, Dify catalog permissions and serving identity. Any owned Run retry is separate.
Implementation/publication is not installation, deployment or live acceptance.
