# Uniwares infrastructure

Shared infrastructure inventory, architecture and operating guidance for Uniwares
applications. It includes documentation and a narrowly scoped discovery helper
with a one-time root installer, plus reviewed staging bootstrap/dispatcher tooling. The operator installed this helper and its scoped
sudo rule; agent-side acceptance passed. Operator-created admin access is recorded
in the inventory. Restricted deployment bootstrap and Unibase's first staging
deployment and Phase 3 staging acceptance/handoff are verified. Shared gateway/Redis,
recovery rehearsals and ownership transfers remain later work. The default branch is `main`.

## Read first

- [VPS inventory](docs/inventory/srv1.md): dated observations and unresolved checks.
- [Architecture](docs/architecture.md): accepted preferences and proposed design.
- [Staging bootstrap runbook](docs/operations.md): start here for the configuration
  checklist, three phases, verification and failure/resume procedures; existing app
  workers/Redis/Nginx stay in place for the first deployment.
- [Phase 1 preparation](docs/staging-preparation.md): verified bindings, prepared tooling and concrete Phase 2 scope.
- [Credential inventory and provider handoff](docs/provider-access.md): stable vault/file names, acquisition, permissions and the new-deployment checklist.
- [Implementation plan](docs/implementation-plan.md): pending delivery and acceptance.
- [Agent guidance](AGENTS.md): evidence and change boundaries.

## Ownership

| Repository | Responsibility |
| --- | --- |
| This repository | Canonical shared-host inventory and proposed shared gateway, account, Redis and timer conventions; installed account/bootstrap tooling; later shared-service migrations remain deferred |
| [Unibase](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md) | Reusable application deployment, application configuration, jobs and application backup/restore |
| [agentic-poc](https://github.com/karpishe-experiments/agentic-poc/blob/master/docs/deployment/contracts.md) | Existing Booklet deployments and current Dify Community, Cloudflare Tunnel/Access and associated Terraform ownership |
| Derived application repositories | Their own application images, releases, runtime configuration and data |

The legacy Nginx deployment and other host applications remain in their existing
locations; their canonical repository ownership needs confirmation. Documentation
here does not transfer Terraform state, credentials or service ownership.

Shared host facts belong here. Application behavior belongs in its application
repository. Link to canonical documents rather than copying an operational inventory.

## Developer tooling and Handbook

Requires Python 3 for tests, and Node.js 22+ plus Git for Handbook tooling.
No npm dependencies or Node installation on the managed host are required.
Use `npm.cmd` on Windows when PowerShell wrappers are blocked.

Run `npm run handbook:setup`, then `npm run handbook:check` / `npm run handbook:doctor`.
The shared checkout follows main lazily; preserve existing work branches and use the
recorded task snapshot for explicit synchronization. `handbook:ready` is offline.
Run `node scripts/handbook.mjs resources --revision SHA` with the task's returned SHA,
then `npm run handbook:sync -- --source SNAPSHOT` and
`npm run handbook:entrypoints -- --source SNAPSHOT` with its returned resourcePath.
Run `python -m unittest discover -s tests` for control behavior.

Adoption uses the eight core workflow skills and no frontend technology skills.
Local guidance lives in the [adapter](.agents/repository-adapter.md) and
[source map](docs/source-map.md). Tracking selects Uniwares #2; live project validation
is pending read:project access. No project, issue, permission or host change is implied.
Bootstrap tooling was copied from Handbook revision
`68114406d21c7f811281503970f7982d73239c0c`; this is provenance, not a version pin.


## Deployment operations

Applications expose doctor/plan/status/check/rollback/backup/restore through their thin
command entrypoint. Infrastructure owns installed operations and the **Apply deployment
plan** approval workflow. Start with the [approved-plan runbook](docs/operations.md#approved-plan-operations)
for one-time trust, immutable bundles, approvals, status and manual encrypted recovery.
For tests install `requirements-controller.txt` in a developer venv, then run the Python
suite on Linux. These Python dependencies belong to controller verification/runtime;
Handbook itself remains dependency-free developer tooling.
