# Shared infrastructure architecture

Status: documentation baseline, 2026-10-22. The [inventory](inventory/srv1.md)
describes observed state. The design below is not an installed topology.

## Accepted preferences

Trusted applications share a VPS. Logical boundaries are sufficient; prioritize
manageable operations and reasonable protection of the host and public entrypoints.
Applications and derived repositories retain independent deployment workflows.

| Boundary | Target convention |
| --- | --- |
| Privileged operations | Shared `uniwares-ops-admin`, sudo for bootstrap and explicitly privileged operations |
| Routine deployment | Shared `uniwares-deploy-user`, restricted dispatcher; no general sudo or Docker-group membership |
| SSH credentials | One deployment key copied into trusted application repository secrets; separate admin credential |
| Images | Public GHCR, credential-free builds, immutable release digests and anonymous host pulls |
| Configuration | Per-environment tracked JSON and private retained runtime snapshots |
| Application branches | Unibase/children: `main`, `_staging` targeting `staging`, `_prod` targeting `prod`; `NODE_ENV=production` remains a framework setting |
| Firebase | Unibase and children share the staging Firebase project and staging credentials; app registrations/domains remain explicit; each production project owns its Firebase project |
| MongoDB | Shared cluster where available; separate application/environment database and runtime user with `readWrite`; separate workflow recovery credentials |
| Redis | One shared application Redis, distinct numbered logical databases per application/environment, shared credential, no per-app ACL requirement; Dify's Redis remains separate |
| Dify | Existing Community installation; separate app IDs/keys per application/environment; organizational tag `app:<project>-<environment>`, e.g. `app:unibase-staging` |
| Coordination | GitHub concurrency within each repository; runbooks coordinate shared-host maintenance; retain application leases/idempotency |

Redis logical databases and Dify tags provide organization, not security isolation.
Keep a registry of assigned Redis databases when provisioning; the instance's
configured database count and existing allocations must be checked first. Never
use `FLUSHALL` for application cleanup. Existing key prefixes may remain.

Shared staging Firebase means authentication-level deletion/revocation affects all
staging applications; app roles and business data remain in their app databases.
Tags do not replace Dify app bindings. Existing Dify apps need an explicit migration
before applying the convention; documentation does not retag them.

## First deployment and later topology

First staging retains the existing Unibase Compose runtime: app, maintenance worker,
AI worker, app Redis and private Nginx. The existing tunnel owner routes the staging
hostname to that Nginx loopback listener. Select a non-overlapping app subnet and
keep legacy public Nginx and Dify Redis unchanged. The shared conventions above
remain the target; shared-service and job refactors are not first-release gates.

After staging works: existing Cloudflare Tunnel -> new shared gateway -> application
web containers. The legacy public Nginx continues serving its current routes.
The shared gateway can use Caddy with internal HTTP while the tunnel supplies the
public HTTPS entrypoint. The exact listener/network and owner-managed tunnel route
integration remain unresolved; do not install a second independent route controller.

Later, assess moving the legacy routes to Caddy and exposing only public gateway
ports 80/443. This is a separate migration requiring route, certificate and DNS
checks. Public Nginx already owns port 80.

Prefer a shared application Docker network with unique service aliases and
service-name routing. Removing per-app Nginx and fixed ingress subnets also requires
reworking trusted-proxy headers and preserving Firebase auth-helper and streaming
behavior. Do not remove those boundaries by documentation alone.

Later, move job execution into the application. Proposed reusable systemd timers invoke
three authenticated, bounded local endpoints: AI, events and maintenance. Requests
must await work; retain durable retries and ownership/accounting safeguards. No
separate Unibase worker containers are required after that refactor is verified.
The [application deployment guide](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md)
owns job behavior and cadence. Dify's own workers are outside this refactor.

## Current ownership and transfer boundary

agentic-poc currently owns Booklet, Dify Community and the existing tunnel/Access
configuration through its [deployment contracts](https://github.com/karpishe-experiments/agentic-poc/blob/master/docs/deployment/contracts.md).
Infrastructure will initially own new shared components only. A future transfer
of Dify, tunnel or other services needs explicit state/configuration migration,
credential ownership, rollback and acceptance. Unibase never deploys through
Booklet's workflow or release paths.

See [operations](operations.md) and [implementation plan](implementation-plan.md).
