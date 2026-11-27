# srv1 inventory

Original discovery observed **2026-10-22**, with subsequent dated evidence below.
This is a sanitized snapshot, not an ongoing health guarantee. No SSH credential
was supplied and no host change was performed during this discovery.

## Unitale staging registration — proposed 2026-11-27

Reviewed configuration only; nothing below is installed until the Unitale Gate 1 root
batch and its readback ([Unitale runbook](https://github.com/Uniwares-LTD/unitale/blob/main/docs/staging-first-deployment.md),
Uniwares-LTD/unitale#21).

| Item | Configured value |
| --- | --- |
| Approval target | `unitale.staging` → `vps-ae0a9d01.vps.ovh.net` |
| Image retention | `ghcr.io/uniwares-ltd/unitale`, staging/prod mapped, `automatic: false` |
| Hostname and listener | `unitale-staging.uniwares.co.uk` → loopback `34312`, routed by agentic-poc Terraform |
| Ingress subnet | `172.30.243.0/24` (P0 2026-11-26: no network or route in use; `172.23.251.128/28` conflicts with `minio_default`) |
| Database | Atlas `kids-booklet`, database and user `unitale_staging` |
| Controller capabilities | P0 readback 2026-11-26: `operation-lock-v1`, `plans-v2`, `github-oidc-v1`, `image-retention-v1`, `data-operations-v1` |

## Installed control and capacity — 2026-10-31

These are user-supplied root-session observations and linked workflow evidence, not
continuous health monitoring. The older discovery tables below retain their own dates.

| Host-controlled identity | Verified value |
| --- | --- |
| Infrastructure source | `cc045864386f6ca6ba92600f238223431f4d1aba` |
| Controller bundle checksum | `e991382e623f1a285ac895fbe31994765bf007af6ea822a0ad67a85c57cae71f` |
| Installed dispatcher checksum | `4404fb361f9e99c43c58061202ed8fed16caa5d705fb0c52b48d08a1ac26731a` |
| Application control source | `594f9c816e16ce02077892a7a0e9abc29e57999d` |
| Installed Unibase control bundle | `8304d73b1b85428c52a1bed38452faf392055bdbb7fd023190ed7e7fe9c49869` |
| Installed staging configuration hash | `3be35b4456ec3086cb65ed82bc8a8bc3ecd7d634fc0dabaebae5974dce2f0d1c` |
| Controller capabilities | `operation-lock-v1`, `plans-v2`, `github-oidc-v1`, `image-retention-v1` |
| Configuration recovery journal | Absent after verified update |
| Approval trust | Installed from the reviewed explicit Admin enrollment; live OIDC approval-path acceptance remains pending |
| Maintenance | Unibase only; `automatic: false`; timer disabled/inactive |

Before cleanup, `/` reported 154 GB total, 11 GB available and 94% usage. The owner-authorized
one-time Booklet cleanup removed 93 image references older than 72 hours while protecting
container references and current/previous releases. Afterwards `/` reported 29 GB used,
126 GB available and 19% usage; Docker reported 37 images, 25 active, and 14.98 GB image
storage. Container and volume counts were unchanged. This did not enroll Booklet or
change the Unibase three-release/14-day retention policy.

The later pre-release check measured 135085899776 free bytes (125.8 GiB), 18.28% usage
on Docker's `/var/lib/docker` filesystem and no pressure warning. These measurements
precede the release; recheck before another capacity-sensitive operation.

The installer initially stopped because `python3.12-venv` was missing; the dispatcher
remained unchanged. Installing that package plus its pip/setuptools wheel dependencies
allowed the same immutable installation to resume. No containers needed restart;
a pending kernel reboot remains separate host maintenance. See [installation recovery](../operations.md#initial-trust-and-controller-installation).

The restricted SSH release and separate check succeeded. [Unibase's current release](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md#current-staging-release)
owns serving commit, image digest and application acceptance. Production activation,
restore rehearsal, timer activation and Dify functional acceptance remain pending.

## Staging acceptance follow-up — 2026-10-25

The corrective application release and independent check succeeded after a reproduced
Cloudflare email-obfuscation/CSP hydration failure. Unibase now sends no-transform
with its private/no-store document response; fresh authenticated account/admin pages
show no injected decoder or new console errors. This was an application-image change,
not host/bootstrap/provider maintenance. That image-only change retained the then-installed control/config identity. The [operations release record](../operations.md#current-unibase-release--2026-10-25)
links to application source/digest evidence and the original bootstrap evidence below remains dated.

## Historical staging bootstrap — 2026-10-25

Operator output confirms Compose 5.6.1 and Buildx 0.38.1 installation, with Docker
Engine retained. The candidate parsed the active projects with their retained
interpolation inputs and passed a disposable create/start/health/remove check.
The shared restricted `uniwares-deploy-user` account and root-owned control bundle
are installed. A checksum-bound, single-file null-IPAM preflight repair selected
bundle `15bc84b1691eb42fd6053c36a4363aa0c18b5ba51e210521e41e9209d7ea18f2`.
Runtime preview/apply and additive indexes completed (`PHASE2_PREPARATION_OK`).
Before first release, agent-side restricted check reached `No current release`,
replacing the earlier missing-setup result. Subsequent release/check workflows
verified Unibase app and both workers healthy, with private Redis and Nginx bound
only to `127.0.0.1:35101`. The application network is `172.30.241.0/24`.
The [operations record](../operations.md#current-unibase-release--2026-10-25)
preserves historical bootstrap evidence; current host identities are recorded above.

Scoped discovery immediately before release found Booklet staging/production
healthy, Dify's previously health-checked services healthy and legacy services
running as before. Xray remains in its pre-existing restart loop; no Xray repair,
Engine upgrade, legacy migration or broad cleanup is included. Historical tables
below retain their October 22 provenance; use the operations progress table for
subsequent application release evidence. During release, Booklet's separate owner
deployment temporarily stopped staging; the final scoped check found it healthy
again. Booklet production, Dify and legacy service statuses were retained.

## Host and capacity

| Item | Observation |
| --- | --- |
| Host | `vps-ae0a9d01`, Ubuntu 24.04 LTS, x86_64 |
| CPU / memory | 16 CPUs; 15 GiB RAM, 4.7 GiB used, about 10 GiB available; no swap |
| Root filesystem | 154 GiB total, 98 GiB used, 57 GiB available, 64% used |
| Docker Engine | 27.0.3 installed; APT candidate 29.9.2 |
| Compose plugin | 2.28.1 installed; APT candidate 5.6.1 |
| Docker storage | 81 images, 22 active; 80.52 GB reported image size, 69.34 GB reclaimable; 674.7 MB container storage; 160.8 MB named-volume storage; no build cache |
| Proposed accounts | `id` returned no identities for `uniwares-ops-admin` and `uniwares-deploy-user` (errors were suppressed) |

APT candidates are observations of the host's package metadata, not validated
upgrade selections. Docker's volume report excludes bind-mounted application data.
Reclaimable images can include rollback images; do not infer safe deletion.

## Existing services and ports

| Compose project / service | Observed state and access |
| --- | --- |
| `kids-booklet-staging` | Healthy application; `127.0.0.1:3100` to container 3000; release directory `4236375426466d9e4c3419cdde9ef9d8384f8259` |
| `kids-booklet-prod` | Healthy application; `127.0.0.1:3200` to container 3000; release directory `2ab3889f67f5e664d2a883cba4358c58ed94bc28` |
| `booklet-dify` | 15 running services; release directory 1.17.1; Nginx on `127.0.0.1:3300`; internal Redis, Postgres, Weaviate, workers, beat, API/websocket, sandbox and proxy services |
| `nginx` | `nginx:1.13.12-alpine`; publishes TCP 80 on IPv4/IPv6 wildcard addresses |
| `minio` | Publishes TCP 9000 and 9001 on IPv4/IPv6 wildcard addresses |
| `labs` | Healthy `labs-aiproxy`; publishes TCP 3500 on wildcard addresses |
| `app` | Ariyana API/web; publishes TCP 4550 and 4551 on wildcard addresses |
| `uniwares` | Client publishes TCP 4303 on wildcard addresses |
| `proxy` | v2ray publishes TCP 4380-4382; Xray repeatedly restarts with exit code 23 |
| Host services | SSH on wildcard TCP 22; Shadowsocks on loopback TCP/UDP 8388; Cloudflare connector running as `kids-booklet-tunnel.service` |

Only Dify's Redis was identified; no separate application Redis was found among
the listed containers, listeners or running system services. External instances
have not been ruled out. No listeners on TCP 443 or 35101 were shown.
Container health and release directory names do not establish image digest identity
or end-to-end functional acceptance.

UFW reports **inactive**. Wildcard listeners are potentially externally reachable;
provider firewall and effective packet filtering were not inspected. The host has
cron running. Its 17 listed systemd timers are OS maintenance timers, with no
application timers shown. Cron entries, container schedules and external schedulers
were not inventoried; Dify has its own worker/beat services.

## Legacy gateway

Nginx mounts its configuration from
`/code/dev_server/deployments/uniwares/srv1/nginx/config/nginx/`.
Its filtered configuration declares port 80 and these server names:

- `br-ariyana.uniwares.co.uk`, `app.ariyanaelderlycare.com`
- `es.uniwares.co.uk`, `kb.uniwares.co.uk`
- `minio.uniwares.co.uk`, `minio-ui.uniwares.co.uk`
- `51.uniwares.co.uk`, `d12y243fn7560.cloudfront.net`
- `univerb.uniwares.co.uk`, `ptemag.uniwares.co.uk`
- `www.uniwares.co.uk`, `uniwares.co.uk`

These are configuration declarations, not verified DNS ownership or active sites.
Upstreams, rewrites, authentication, headers, certificates and route usage remain
uninspected. Do not infer that every listed hostname can receive a new certificate.

## Docker network allocations

| Network | Subnet |
| --- | --- |
| `bridge` | `172.17.0.0/16` |
| `nginx_elastic` | `172.18.0.0/16` |
| `app_ariyana_network` | `172.19.0.0/16` |
| `booklet-dify_local_sandbox_proxy_network` | `172.20.0.0/16` |
| `labs_labs-network` | `172.21.0.0/16` |
| `booklet-dify_agent_sandbox_network` | `172.22.0.0/16` |
| `minio_default` | `172.23.0.0/16` |
| `proxy_default` | `172.24.0.0/16` |
| `uniwares_default` | `172.25.0.0/16` |
| `kids-booklet-staging_default` | `172.26.0.0/16` |
| `kids-booklet-prod_default` | `172.27.0.0/16` |
| `booklet-dify_default` | `172.28.0.0/16` |
| `booklet-dify_ssrf_proxy_network` | `172.29.0.0/16` |

Unibase's current suggestions `172.29.241.0/24` (staging) and `172.29.242.0/24`
(production) both overlap Dify's `/16`. Replacement networking must also be checked
against host/VPN routes, not just this Docker list.

## Repository and service discovery

Separate read-only GitHub/API checks on 2026-10-22 found:

- `Uniwares-LTD` uses GitHub Free; Unibase is private, with only `main`, no
  repository Actions secrets and no GitHub environments at that observation.
- Unibase's provisioning code requires Compose 2.30 or newer. Its staging provider,
  SSH and shared-owner bindings remain placeholders.
- The connected Dify Community workspace responds; this does not verify Unibase
  bindings, credentials or tags.
- agentic-poc's historical host observation is dated 2026-09-28; it remains
  historical evidence rather than a second current inventory.

## Remaining checks

### Operator access verified on 2026-10-22

Subsequent operator-supplied output supersedes the earlier missing-admin-account
observation: `uniwares-ops-admin` was created with UID/GID 1003 and a disabled
account password. The operator installed the shared public key and reported a
successful key-authenticated Windows SSH connection to
`vps-ae0a9d01.vps.ovh.net` (`51.195.218.185`), port 22. `whoami` and `hostname`
returned `uniwares-ops-admin` and `vps-ae0a9d01`.

The ED25519 host fingerprint accepted on that connection was independently
confirmed by output from the existing trusted root session:
`SHA256:Jk5pHbF36TXs3PZ+50CuaX074dLjCd4/Gs7uIrU6vyc`.
`sudo -n true` returned `sudo: a password is required`; unattended privileged
access is not established. Other operators' devices remain individually unverified.
The login banner reported a required restart; no restart was performed.
The deployment account remains unverified. No private-key contents or passphrase
were provided. See [shared operator access](../operations.md#shared-operator-key-handoff).

### Outstanding discovery

Agent read-only verification at 12:02 UTC on 2026-10-22 succeeded over direct SSH
with `BatchMode=yes`, `IdentitiesOnly=yes` and `StrictHostKeyChecking=yes`, using
the local `srv1-ops-admin` key reference. No privileged action or service change ran.

- Identity: UID/GID 1003, groups include `sudo` and `users`; `sudo -n true` still
  requires a password. The Docker socket is not readable by this account and
  `getent passwd uniwares-deploy-user` returned no account.
- All IPv4 route tables and policy rules showed the existing connected Docker
  ranges `172.17.0.0/16` through `172.29.0.0/16`, the provider gateway and default
  route, with only standard local/main/default policy rules. Observed IPv6 routes
  were link-local. No additional VPN route was shown; inactive Docker networks or
  future VPN allocations still require checking before allocating a subnet.
- TCP listener inventory still shows no listener on 35101; this is not a reserved
  allocation. Existing loopback ports 3100/3200/3300 and public port 80 remain bound.
- Compose reports 2.28.1; existing APT metadata lists candidate 5.6.1. No package
  index refresh, upgrade or compatibility test was performed.
- Tunnel service is active; this does not prove end-to-end application health.
  Seventeen systemd timers were listed, all named for OS maintenance. Cron and
  container schedules remain uninspected.
- Root filesystem has 57 GiB available; memory reports 10,747 MiB available and
  no swap. `/var/run/reboot-required` confirms a pending restart.

Effective host/provider firewall, protected schedule contents and provider bindings
remain to be inspected through authorized interfaces. Do not
grant Docker-group membership or general passwordless sudo to finish discovery.

### Scoped discovery installation and acceptance — 2026-10-22

The operator supplied successful installer checksum and sudoers validation output.
Agent-side `sudo -n /usr/local/sbin/uniwares-discovery` then succeeded. The installed
helper is `root:root`, mode 755, with SHA-256
`d5e7d42f4097624043bf9471fab33d139aef2f1c02a780e8ad335d483244a0e3`.
Both the same command with `--help` and unrelated `sudo -n true` were denied with
exit 1. The sudoers file cannot be stat-ed by the non-root account; its validation
evidence comes from the operator's trusted root session, not direct agent inspection.

The helper confirmed all 13 allocated Docker subnets in the table above, plus the
host/none networks without IPAM allocation. UFW remains inactive. Booklet staging
and production report healthy; existing Dify containers report running, with health
checks healthy where provided, and its permission-init container exited 0. This is
container-state evidence, not end-to-end provider/application acceptance. Legacy
containers remain running except Xray, still restarting with exit code 23.

Schedule-name discovery found `/etc/cron.d/e2scrub_all` and `/etc/cron.d/sysstat`,
and no files under `/var/spool/cron/crontabs`. It did not inspect `/etc/crontab`,
periodic cron directories, schedule contents or external schedulers. No runtime
configuration, service restart, firewall change or deployment was performed.

### First-staging inventory refresh — 2026-10-24

Agent SSH and the installed helper were rerun without host changes. Docker IPAM,
IPv4 routes/policy rules and listeners match the October 22 baseline; port 35101
still has no listener. Compose remains 2.28.1, UFW inactive and the tunnel service
active. Booklet containers report healthy; Xray still restarts with code 23.
Root disk now reports 114 GiB used and **41 GiB available (75% used)**, compared
with 57 GiB available on October 22. Memory available is 10,716 MiB with no swap.
The source of disk growth has not been measured; no cleanup was performed.

Read-only schedule summarization found four `/etc/crontab` jobs referencing the
hourly/daily/weekly/monthly directories, two entries each in e2scrub_all and sysstat,
and no `/etc/anacrontab`. Periodic filenames were OS tools (apport, apt-compat,
dpkg, logrotate, man-db, sysstat); hourly/monthly had only placeholders. The 17
systemd timer names remain OS maintenance. These checks do not audit every script's
contents or exclude external/container schedulers; raw job commands were not emitted.

The locally checked owner Terraform declares Booklet staging/production on loopback
3100/3200, SSH on 22 and enabled Dify on 3300, plus its fallback. This is declared
configuration, not current Cloudflare API evidence. No Actions cron trigger was
found in the inspected local Unibase/agentic-poc workflow copies; remote changes
and other repositories' schedulers are not ruled out.

| Remaining item | Required evidence / scope |
| --- | --- |
| Effective host firewall | Received operator root output October 24; findings below |
| Provider firewall | OVH enabled/disabled state and active rules for 51.195.218.185; no connected provider control-plane access available |
| Tunnel route ownership/drift | Owner's live Cloudflare tunnel identity and hostname-to-service list, compared with declared configuration; no token values |
| External schedules / reservations | Operator confirmation of other automation or reserved VPN/subnet allocations not visible in active state |
| Disk growth | Docker dominates usage; image-count/size increase observed below; cleanup remains separately scoped |

Subnet/listener selection must recheck this evidence at apply time. Tested Compose
upgrade selection and application provider bindings are implementation/preparation
work, not established by inventory. Full legacy-route migration, external Redis
selection and off-host backup storage remain deferred for first staging. MinIO on
this VPS alone is not an off-host backup. Investigate Xray separately.

### Operator firewall, storage and provider evidence — 2026-10-24

Source: operator-supplied root command output at 13:54 UTC and OVH console summary.
No raw terminal transcript is retained.

- IPv4 and IPv6 iptables filter policies show INPUT/OUTPUT ACCEPT and FORWARD
  DROP. DOCKER-USER contains only RETURN; Docker's explicit forwarding/NAT rules
  permit published services. The FORWARD policy alone does not protect them.
- The supplied nft ruleset contains Docker's ip/ip6 filter/NAT tables, with no
  additional host-input filtering shown. Rules are managed through iptables-nft;
  this is the same ruleset presentation, not a second independent firewall.
- IPv4 DNAT for 3100/3200/3300 explicitly matches 127.0.0.1. Publicly published
  ports 80, 3500, 4303, 4380-4382, 4550-4551 and 9000-9001 have Docker accept/DNAT
  rules without a source allowlist. Actual Internet reachability still depends on
  provider filtering and network paths; it was not externally tested here.
- Docker reports 94 images, 22 active, 95.41 GB image size and 84.23 GB reclaimable;
  26 containers, 25 active, 683.8 MB writable container size; six active volumes,
  160.9 MB; no build cache. Compared with October 22, image count increased by 13
  and reported image size by 14.89 GB, consistent with images contributing to growth.
- Filesystem `du` reports Docker 106 GiB (overlay2 103 GiB, container directory
  2.5 GiB), logs 3.9 GiB (journal 3.1 GiB), and /code 1.2 GiB. These figures use
  different accounting from Docker's logical/shared-layer sizes; do not add them
  together or infer every reported reclaimable byte is safe to delete. Retained
  rollback images must be identified before selective cleanup.
- OVH summary reports an active London/os-uk2 VPS, 16 vCores, 16 GB RAM, 160 GB
  storage, no additional disks, and IPv4 51.195.218.185. Its display name is
  srv1.vps.ovh.net; this does not replace the verified SSH hostname.
- Provider-assigned IPv6 is 2001:41d0:801:2000::58af, gateway
  2001:41d0:801:2000::1. Earlier guest observations showed only link-local IPv6;
  provider assignment does not establish guest configuration or reachability.
- OVH snapshots and automated backups are disabled. The console's Ubuntu image
  label includes deprecated; this is not proof of guest OS support status or an
  instruction to reinstall/upgrade.

The supplied VPS overview does not show Edge Network Firewall state. Record it as
**unverified**, not disabled. OVH's [official navigation](https://docs.ovhcloud.com/en/guides/bare-metal-cloud/dedicated-servers/firewall-network)
is Network -> Public IP Addresses -> the IPv4 row's menu -> Configure Edge Network
Firewall (or its status badge). Inspect only; do not enable/change rules during
inventory. This feature concerns IPv4; it does not certify IPv6 filtering.

### Live follow-up — 2026-10-24

Phase 2 refresh at 15:42 UTC: Booklet staging and production were healthy, with no
temporary Booklet operation container present. Dify/legacy statuses were unchanged;
Xray continued its pre-existing restart loop. Root filesystem had 39 GiB free.
Compose remained 2.28.1 and `uniwares-deploy-user` was absent before the root batch.

Authorized Phase 2 provider changes: added `unibase-staging.uniwares.co.uk` to
Firebase's authorized domains while preserving previous entries; created Atlas
`unibase_staging` with only database-scoped `readWrite`, restricted to the existing
`kids-booklet` cluster. The operator updated Google OAuth origins/redirects; the
previous `redirect_uri_mismatch` response cleared on verification. Runtime inputs
and the separate shared deployment key remain in protected stores, not Git.

Owner workflow [40109137086](https://github.com/karpishe-experiments/agentic-poc/actions/runs/40109137086)
applied one DNS addition and one tunnel configuration update, zero deletions, at
owner revision `50536f0`. Subsequent live verification confirmed the exact staging
hostname, proxied CNAME and private listener route. This does not establish an
application deployment by itself: root bootstrap and release were still pending at
that checkpoint. The current staging bootstrap section above supersedes it.

Earlier Phase 1 read-only provider access confirmed tunnel `kids-booklet-vps`, UUID
`3d383dc7-335b-4989-b0f2-d1f32a7092f2`, healthy and Cloudflare-managed. Its live
four hostname routes and fallback matched the declaration below. At that point
there was no DNS record for the proposed Unibase staging hostname. The
[preparation checklist](../staging-preparation.md) records verified Firebase/Atlas
bindings and the remaining additive setup scope.

A later scoped host discovery observed Booklet staging's normal container exited
143 and a temporary `booklet-operation-staging` container unhealthy during an
existing operation. Booklet production remained healthy; Dify health statuses
were unchanged and Xray continued restarting. At that checkpoint the earlier healthy observation could not establish the
Phase 2 baseline. Later October 25 discovery confirmed recovery; use the final
baseline in the current staging bootstrap section rather than treating this
historical operation as still active. No service was changed by this discovery.

Refreshed IPv4 routes and Docker IPAM cover 172.17.0.0/16 through 172.29.0.0/16;
no route overlap with proposed 172.30.241.0/24 or listener on 35101 was observed.
The operator reports no external schedules or reserved VPN/subnet ranges. This is
an observation/proposal, not an allocation; recheck before apply.

Checksum-pinned Compose 5.6.1 executed as the unprivileged operator from a temporary
directory and parsed Unibase's current Compose definition with synthetic inputs.
No daemon operation or installation occurred. Apt simulation proposes Compose
5.6.1 plus Buildx 0.38.1 (currently 0.15.1), with no removals or Engine upgrade.
Legacy definition and disposable runtime compatibility checks remain required
before service recreation; the installed Compose remains 2.28.1.

### Tunnel declaration retrieved from the owner — 2026-10-24

GitHub reads of agentic-poc/master resolved to commit
`e02d9e477257572a44e6cac47d25fb76842232be`. Canonical sources are
[VPS configuration](https://github.com/karpishe-experiments/agentic-poc/blob/e02d9e477257572a44e6cac47d25fb76842232be/infra/config/vps.json),
[Terraform routes](https://github.com/karpishe-experiments/agentic-poc/blob/e02d9e477257572a44e6cac47d25fb76842232be/infra/terraform/main.tf)
and [project default](https://github.com/karpishe-experiments/agentic-poc/blob/e02d9e477257572a44e6cac47d25fb76842232be/infra/terraform/variables.tf).
The declared tunnel name is `kids-booklet-vps` using the project's default, with
Cloudflare-managed configuration. The generated tunnel UUID is a Terraform resource
ID, not a literal in these files; obtain only the `tunnel_id` output through the
owner's authorized state/API access before route changes. Do not export full state
or read the tunnel token to derive it. Current live route drift remains unverified.

| Declared hostname | Service |
| --- | --- |
| booklet-staging.uniwares.co.uk | http://localhost:3100 |
| booklet.uniwares.co.uk | http://localhost:3200 |
| srv1-deploy.uniwares.co.uk | ssh://localhost:22 |
| dify.uniwares.co.uk | http://localhost:3300 (public enabled in tracked config) |
| Unmatched hostname | http_status:404 |

Account/zone IDs remain canonical in the owner's configuration. Ownership and
Terraform state stay with agentic-poc. No Unibase route is declared in this revision.

Evidence sources: operator output from `hostname`, OS/capacity commands,
`docker version`, `docker compose version/ls`, `docker ps -a`, `docker system df`,
filtered Nginx configuration/mount inspection, `apt-cache policy`, Docker network
IPAM inspection, `ss`, `ufw status`, systemd timer/service lists and account checks.
Raw transcripts and credentials are deliberately not stored.

See [architecture](../architecture.md), [operations](../operations.md) and
[pending implementation](../implementation-plan.md) for interpretation and next work.
