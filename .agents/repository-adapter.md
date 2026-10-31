# Infrastructure repository adapter

## Authority and workflow

The user's accepted task and [implementation plan](../docs/implementation-plan.md)
define scope. Preserve accepted milestones without retroactive issues or backlog
migration. New substantial work follows Handbook issue policy; propose issues before
creation. Preferences are in [repository.md](repository.md). Work on task branches.
Commits, pushes, PR publication, merges, host installation, deployments, permission
changes and releases require explicit session authorization. Shared commit defaults
do not override this reviewable-working-tree workflow. Humans own closure and Done.

## Ownership and operations

Preserve [AGENTS.md](../AGENTS.md), [architecture](../docs/architecture.md),
[inventory](../docs/inventory/srv1.md) and [operations](../docs/operations.md).
Infrastructure owns shared hosts, access and root-owned control installation.
Applications own their runtime behavior/configuration and release acceptance.
Booklet, Dify and the existing tunnel retain their existing owners. No adoption,
image publication or documentation change authorizes live installation.
Keep secrets, private snapshots and raw operator output outside Git.
Publication descriptions state operator intervention, owner/location, ordering,
verification and failure/resume. Do not replay completed bootstrap.

## Validation and tracking

Run `python -m unittest discover -s tests` and affected Handbook readiness/entrypoint
checks. Node is workstation tooling, not a host dependency. Run a separate read-only
review. Readiness warnings are advisory; real test and operational failures must be
reported. Do not add a deployment or CI gate solely for adoption.
The selected tracking destination is Uniwares project #2, recorded in tracking.json.
Live identity, fields, association and access remain unverified because the current
CLI lacks read:project. Repair access and verify before external tracking changes;
local adoption does not enroll issues or change organization permissions.

Deployment changes must classify image, host configuration, controller, provider or data impact. Report operator ordering, verification and failure/resume; unsupported requirements require a named owner action. Preserve session authority and separate publication from installation/live acceptance.
