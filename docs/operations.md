# Shared operations

These are target conventions and implementation requirements, not executable
setup instructions. Read [the dated inventory](inventory/srv1.md) before acting.

## Credentials and access

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

Compose 5.6.1 is the observed package candidate, not validated compatibility.
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

The inventory reports 69.34 GB of reclaimable images. First identify each app's
active and retained rollback digests and whether they can be pulled again. Remove
only explicitly selected obsolete images; record a small retention policy when
implemented. Do not blanket-prune images/volumes across all projects. The current
57 GiB free disk does not require emergency deletion to begin staging work.

## Minimum staging backup and recovery

Target one manual application workflow with `backup` and `restore` actions.
Back up before migrations or destructive operations, rather than every image
deployment. A manual policy accepts loss since the last successful backup;
production recovery expectations remain a separate decision.

- Include the app MongoDB database and GridFS bytes; verify a private encrypted
  off-host archive, manifest and checksum before declaring success.
- Pause/drain writers and timers for a consistent backup/restore. Require an exact
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

- [GitHub Actions secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [GitHub environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [Docker firewall behavior](https://docs.docker.com/engine/network/packet-filtering-firewalls/)
- [Docker image pruning](https://docs.docker.com/reference/cli/docker/image/prune/)
- [Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https)
- [Redis logical databases](https://redis.io/docs/latest/commands/select/)
- [systemd timers](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)
