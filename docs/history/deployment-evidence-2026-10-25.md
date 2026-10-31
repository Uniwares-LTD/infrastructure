# Historical deployment evidence through October 25, 2026

Historical evidence only. These instructions and identities are not current procedures or proof of current health. Use the parent deployment/operations guide.

## Configuration and progress

Use the [Phase 1 preparation package](../staging-preparation.md) and
[protected provider handoff](../provider-access.md). Use [the dated inventory](../inventory/srv1.md); refresh only facts needed for the
next decision. Discover available values first and request remaining non-secret
inputs together. Record secret names and protected-store references, never values.

| Input | Needed for first deployment |
| --- | --- |
| Access | Host identity, working SSH transport/profile, key reference, host-key pin and usable privilege path |
| Revisions | Reviewed infrastructure, Unibase and tunnel-owner revisions |
| Staging | HTTPS hostname, DNS/tunnel authority and owner-managed route to the app's private Nginx listener |
| Providers | Existing shared staging Firebase project/credentials, app registration/domains; Atlas cluster, app database/user and exact egress allowlist |
| Network | Free loopback port and application subnet checked against Docker and host/VPN routes |
| Runtime | Existing app Redis at database 0, private password reference; current worker/Nginx configuration |
| Release | Public GHCR package and reviewed source SHA; record immutable image digest when the release workflow builds it |
| Deferred recovery | Track destination, encryption-key recovery, retention and restore permissions as follow-up; not a first-startup prerequisite |

Use this table for current status, not a chronological log. Status values are
pending, in progress, blocked and verified. Retain only sanitized verification
and non-secret workflow/release identifiers.

These checkpoints record the basic staging deployment. The optional AI extension
and its acceptance are recorded separately in the current release below.

| Phase | Status | Reviewed revision | Verification | Next action |
| --- | --- | --- | --- | --- |
| 1 Connect and prepare | Verified (preparation only) | Infrastructure `bb041e4`, Unibase `6edc411`, owner `c182b64` | October 24: provider reads, inventory, 47 Linux deployment tests, 10 Infrastructure tests and 3 Terraform mock tests; separate read-only review | Complete; subsequent live acceptance is recorded in Phase 2 |
| 2 Bootstrap and deploy | Verified | Runtime `edcc21d`; Infrastructure installer `90ed66a`; owner route `50536f0` | October 25: plugins/account/control and runtime/index preparation complete; Release `40168299056` attempt 3 and independent Check `40168997418` passed, including anonymous pull, local/public readiness and both workers. Booklet staging returned healthy after its separate owner operation; production/Dify/legacy baseline retained | Complete; use Phase 3 routine instructions and do not repeat bootstrap |
| 3 Verify and hand off | Verified | Corrective runtime `215044b`; handoff guidance in this runbook and the application deployment guide | October 25: account/admin/session/profile/logout checks, operator-reported incognito login/logout and workstation Actions/pinned SSH access verified. Corrective Release `40176352821` and independent Check `40176659441` passed; fresh account/admin loads have no injected decoder or new console errors | Routine staging uses the quick start below. Next: minimum off-host recovery workflow/rehearsal; keep consolidation and production separate |

### Current Unibase release — 2026-10-25

- Staging: <https://unibase-staging.uniwares.co.uk/account>, branch `_staging`.
- Source: `1f19ce3963bbd41588b0972b8d55717a97ed1fb5`.
- Image: `ghcr.io/uniwares-ltd/unibase@sha256:ae8d7bbb5468f1f6ad7f481a9b3c2403a98cdaec34f3ebbb348488e8d30dce9d`.
- Installed control bundle: `4ce4da8ea0c9842330eeb6c96cf41aa26ecbaab6daf16cf6e7a5481ea4482fa2`.
- Tracked staging configuration SHA-256: `c13b8b81304490c768c07b769f1b650215d04211d4ce5504a1029dfa85aac91c`.
- Operator output confirms optional AI/MCP preview, encryption compatibility and
  `AI_CONFIGURATION_PREPARED`. [Release 40188936199](https://github.com/Uniwares-LTD/unibase/actions/runs/40188936199)
  passed on October 25, including anonymous digest pull and deployment health checks.
  Subsequent bounded Dify/MCP/Persona application acceptance also passed;
  the [application acceptance record](https://github.com/Uniwares-LTD/unibase/blob/main/docs/deployment.md#ai-activation-and-acceptance)
  owns Run, persistence and accounting evidence. No new release was needed for
  saved application/provider settings.
- Private release snapshots remain under `/opt/unibase/staging/releases/`; `current`
  selects the serving snapshot. The prior release was `215044b` with image
  `sha256:adee7653a0901b7340b300843066f5f7542e86dfa0bc0f569b7bc3dc357848d1`.
  Inspect retained state before rollback; no rollback rehearsal or data restore
  occurred. Operator-update backups preserve previous runtime/control bytes separately.
  Never copy private snapshots or backup contents to Git.

Routine operations use Unibase's own workflows on `_staging`:

```powershell
gh workflow run check-deployment.yml --repo Uniwares-LTD/unibase --ref _staging -f environment=staging
```

A reviewed push to `_staging` triggers Release automatically. Do not also dispatch
the same commit. Use Rollback only when a real compatible healthy predecessor is
retained; the preceding source is recorded above, without claiming a rollback rehearsal.
Secret references are repository Actions
secrets `DEPLOY_SSH_PRIVATE_KEY`, `DEPLOY_SSH_HOST_KEY`, `CLOUDFLARE_READ_TOKEN` and
the protected provider handoff, not values in this document.

Post-deploy shared-host baseline verification is complete; its dated evidence is
in the [inventory](../inventory/srv1.md). Reuse it unless a new shared-host change
could affect existing services. Routine Unibase acceptance checks its own app.

The goal is one access handoff, one consolidated input request and one authorization
for concrete live changes. Provider consent/authentication may still need operator
input. Honor existing scope authorization; stop for unexpected destructive changes.
