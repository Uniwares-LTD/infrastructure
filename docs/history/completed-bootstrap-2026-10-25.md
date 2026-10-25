# Completed srv1 bootstrap procedure — 2026-10-25

Historical procedure for the reviewed installation, not a command batch to rerun.
The accounts, plugins and first staging release are installed. Start with
[current operations](../operations.md); inspect state before any repair.
A new host requires reviewed discovery and tooling for that host.

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

For additional operators, use the [shared key handoff](../operations.md#shared-operator-key-handoff)
instead of creating another account or regenerating the installed key.

#### Scoped privileged discovery

The [discovery helper](../../scripts/srv1-discovery.py) and
[one-time installer](../../scripts/install-discovery.sh) were installed and verified
on October 22; see the [acceptance evidence](../inventory/srv1.md#scoped-discovery-installation-and-acceptance--2026-10-22).
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
Phase 1 tooling and concrete scope in [staging preparation](../staging-preparation.md).
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
