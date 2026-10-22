# Uniwares infrastructure

Shared infrastructure inventory, architecture and operating guidance for Uniwares
applications. This private repository is initialized with documentation only.
It has not installed services, created host accounts, transferred ownership or
changed deployments. The default branch is `main`.

## Read first

- [VPS inventory](docs/inventory/srv1.md): dated observations and unresolved checks.
- [Architecture](docs/architecture.md): accepted preferences and proposed design.
- [Staging bootstrap runbook](docs/operations.md): start here for the configuration
  checklist, eight checkpoints, verification and failure/resume procedures.
- [Implementation plan](docs/implementation-plan.md): pending delivery and acceptance.
- [Agent guidance](AGENTS.md): evidence and change boundaries.

## Ownership

| Repository | Responsibility |
| --- | --- |
| This repository | Canonical shared-host inventory and proposed shared gateway, account, Redis and timer conventions; executable provisioning remains pending |
| [Unibase](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md) | Reusable application deployment, application configuration, jobs and application backup/restore |
| [agentic-poc](https://github.com/karpishe-experiments/agentic-poc/blob/master/docs/deployment/contracts.md) | Existing Booklet deployments and current Dify Community, Cloudflare Tunnel/Access and associated Terraform ownership |
| Derived application repositories | Their own application images, releases, runtime configuration and data |

The legacy Nginx deployment and other host applications remain in their existing
locations; their canonical repository ownership needs confirmation. Documentation
here does not transfer Terraform state, credentials or service ownership.

Shared host facts belong here. Application behavior belongs in its application
repository. Link to canonical documents rather than copying an operational inventory.
