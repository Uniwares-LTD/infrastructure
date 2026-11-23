# Infrastructure source map

## Components

[Scripts](../scripts) own restricted dispatch, control-bundle construction, bootstrap,
configuration update and bounded discovery. [Tests](../tests) use disposable fixtures.

## Documentation

[README](../README.md) owns workstation setup; [architecture](architecture.md) owns
boundaries; [inventory](inventory/srv1.md) owns dated host facts; [operations](operations.md)
owns installation and recovery procedures; application repositories own serving release identities and functional acceptance. [Implementation plan](implementation-plan.md)
retains accepted milestones. [Provider access](provider-access.md) owns credential references.

[Data operations](operations.md#reusable-backup-and-migration-workflows) own the
configured backup/migration runbook. [data_operations.py](../scripts/data_operations.py)
implements static catalog/reporting, exact preparation, execution and authoritative
activation evidence; [recovery.py](../scripts/recovery.py) owns archive creation/retrieval.
The [root acknowledgment utility](../scripts/data-operation-resolution.py) inspects and
settles original journals without migrations/restores/restarts. The
[activation gate](../scripts/data-operation-gate.py) runs immediately before app startup
under the inherited application lock. The [trusted probe](../scripts/data-operation-probe.cjs)
uses Node/MongoDB in the currently approved image. Mirrored report fixtures and disposable
unit tests verify contracts; source validation is separate from installation/live acceptance.

## Commands

[package.json](../package.json) owns Handbook commands. Run Python's unittest discovery
against tests for control behavior. See [README](../README.md) for prerequisites.

## Generated areas

Handbook skill/client entrypoints and command safeguards are explicitly synchronized.
Caches, private configuration and operator bundles are not source. Templates copied
into .github and docs/templates become project-owned.

## Ownership

[Repository adapter](../.agents/repository-adapter.md) preserves local authority;
[preferences](../.agents/repository.md) and [tracking](../.agents/tracking.json) record
confirmed selections. Applications retain their release/data ownership; Booklet,
Dify and tunnel ownership remain as recorded in architecture.

Deployment changes require configuration ownership classification and operator-impact reporting. The deployment/operations guide owns plan approval, status and recovery; contract changes require validation, update behavior and compatibility coverage.

[Image maintenance](../scripts/image_maintenance.py) owns retention, disk checks and release-ledger protections. [Its operator installer](../scripts/install-image-maintenance.py) owns explicit policy and disabled timer installation. See [image retention](operations.md#image-retention) for rollout and recovery.

Current procedures link to dated evidence rather than duplicating it. Superseded first-deployment evidence is retained in [history](history/deployment-evidence-2026-10-25.md); it is not a task queue or runnable update procedure.
