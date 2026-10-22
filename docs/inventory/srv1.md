# srv1 inventory

Observed **2026-10-22**, from two operator-supplied read-only command outputs.
This is a sanitized snapshot, not an ongoing health guarantee. No SSH credential
was supplied and no host change was performed during this discovery.

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

Confirm host/VPN routes, effective firewall/provider rules, active gateway routes,
DNS/tunnel ownership and integration, external Redis availability, logical database
allocations, cron/external schedules, off-host backup destination and permissions,
Compose compatibility, and actual release digests. MinIO on this VPS alone is not
evidence of off-host backups. Investigate Xray separately from staging provisioning.

Evidence sources: operator output from `hostname`, OS/capacity commands,
`docker version`, `docker compose version/ls`, `docker ps -a`, `docker system df`,
filtered Nginx configuration/mount inspection, `apt-cache policy`, Docker network
IPAM inspection, `ss`, `ufw status`, systemd timer/service lists and account checks.
Raw transcripts and credentials are deliberately not stored.

See [architecture](../architecture.md), [operations](../operations.md) and
[pending implementation](../implementation-plan.md) for interpretation and next work.
