# Staging provider access handoff

## Credential inventory and naming

### Obtain the initialization handoff

Ask the operator: **“Please retrieve the Unibase derived-project staging
initialization files from the secure Credentials channel, save them outside Git
in a protected local directory, and provide only the directory path. Confirm that
your GitHub, Google/Firebase, Atlas and tunnel-owner setup access is available.”**
The channel is the team's handoff source; this guidance does not assert that its
membership, retention or encryption has been audited. Do not request values in chat.
Prefer the existing channel files before asking users to create replacement keys.
The operator confirmed the handoff was stored in that channel under
**Unibase derived-project staging initialization credentials**.

The collected handoff was checked locally on 2026-10-25: all six JSON files parsed,
required inspected fields were populated, Firebase project/config and preparation
copies matched, and MongoDB preparation credentials matched the database file.
Both OpenSSH files contain public components matching their `.pub` files; both are
unencrypted and require protected storage. This was structural verification, not
a fresh provider-permission, SSH-login or credential-expiry check.

| Channel filename | Purpose and reuse boundary |
| --- | --- |
| `uniwares-ops-admin` | Shared srv1 operator private key, also named `srv1-ops-admin`; operator setup only |
| `uniwares-ops-admin.pub` | Matching public key for authorized host installation |
| `uniwares-deploy-user` | Shared restricted deployment private key; destination `DEPLOY_SSH_PRIVATE_KEY` |
| `uniwares-deploy-user.pub` | Matching deployment public key for authorized host installation |
| `firebase-staging-service-account.json` | Reusable shared staging Firebase Admin identity |
| `cloudflare-discovery.json` | Shared scoped API token (`apiToken`), consumed as `CLOUDFLARE_READ_TOKEN` |
| `atlas-discovery.json` | Existing Atlas API public/private key pair; verify permissions before writes |
| `firebase-staging-web.json` | Unibase web registration; reference only for children, which need their own registration/config |
| `unibase-staging-database.json` | Unibase database/user/password; do not use as a child's runtime identity |
| `unibase-staging-host-input.json` | Unibase-specific preparation snapshot; rebuild for each child from its own bindings |

After retrieval, inspect only necessary files without printing values. Check JSON
fields, key pairing and intended project/database before use; filenames alone do
not prove scope or permissions. Keep existing filenames, including extensionless
SSH keys. Copy the operator key to the documented workstation SSH location only
when needed and without overwriting an existing different key. Populate destination
repository secrets through byte-preserving protected input; never paste them in PRs.
Create the child's own Firebase web registration and Atlas database user, then
assemble its preparation input. Provider writes still require the reviewed setup
scope; an Atlas discovery key may lack write authority.

Not included in this collection: Redis password, provider-login/access references,
or recovery credentials. Redis is generated for each fresh app by preparation;
the existing Unibase password is needed only for its own recovery. Recovery inputs
remain conditional follow-up work. Obtain missing provider access references in one
batch. Public hostname/project/route bindings belong in tracked configuration and
the runbook; the verified public SSH host record below does not need secure delivery.

For the existing srv1 destination, `DEPLOY_SSH_HOST_KEY` uses this public record,
recovered from local known_hosts and matched to the previously operator-verified
fingerprint on 2026-10-25 (not a new live host check):

```text
vps-ae0a9d01.vps.ovh.net ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILKxGt38OQAf3tZh7wzXzSImX+Mc493q4SyIsky7b+Xa
```

Fingerprint: `SHA256:Jk5pHbF36TXs3PZ+50CuaX074dLjCd4/Gs7uIrU6vyc`.
Reverify through trusted operator access for a replacement server or changed key.
Do not copy this trust record to a different destination.

### Storage conventions

This is the canonical acquisition/storage inventory for new deployments. Names below
are conventions, not a claim that password-manager items or recovery secrets already
exist. Keep values in the team password manager; give agents item references or
protected local exports, never values in chat, Git, PRs or artifacts.

- Shared item: `Uniwares / Shared / <credential-name>`.
- App item: `Uniwares / <project> / <environment> / <credential-name>`.
- New exports: `%USERPROFILE%\.config\<project>\<environment>-<credential-name>.<extension>`.
- In the tables, **Shared** and **App** expand to those item prefixes. Host trust
  items additionally include the destination hostname. Access items may contain
  only an account/session reference, not a stored token. Public IDs are not secrets.
- Use `staging` today; `prod` is the target production label. Existing Unibase
  production tooling still uses `production`; do not rename it through this checklist.

### Required runtime and deployment inputs

| Purpose | Applicability | Password-manager item | Local filename (new export) | Actions secret / runtime variable | Acquisition | Permissions | Consumer | Recovery / rotation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Operator SSH | Initial setup/host maintenance, either environment | Shared / `srv1-ops-admin` for srv1; name other hosts explicitly | Existing `%USERPROFILE%\.ssh\uniwares-ops-admin` on srv1 | None | Reuse owner's protected private key; follow operations handoff | Installed operator access; trusted root session for unsupported privileged actions | Operator only | Private key cannot be recovered from public key; retain protected original; no routine workflow copy |
| Deployment SSH | Both | Shared / `uniwares-deploy-user` | `uniwares-deploy-user` | `DEPLOY_SSH_PRIVATE_KEY` | Reuse shared protected key after destination installs its public key | Restricted registered app operations only | Release/check/rollback | Keep complete OpenSSH bytes/newlines; coordinate rotation across trusted repos |
| Host trust (public) | Each destination | Shared / `ssh-host-key / <hostname>` | `<environment>-ssh-host-key.txt` | `DEPLOY_SSH_HOST_KEY` | Verify host public key through trusted operator session | No credential privilege | SSH client | Re-read publicly; changed key requires trusted verification, not blind replacement |
| Firebase Admin JSON | Shared staging; app-specific production project | Shared / `firebase-admin` for staging; App / `firebase-admin` for production | `<environment>-firebase-admin.json` | VPS `firebase.json`; `GOOGLE_APPLICATION_CREDENTIALS` points to mounted file | Reuse saved key; Firebase Project settings → Service accounts identifies account; generate replacement only if authorized and original unavailable | Runtime Firebase Admin operations for selected project; no provisioning authority implied | Web/workers | Existing private key cannot be downloaded again; save original and coordinate shared staging rotation |
| Firebase web config (public) | Each app/environment | App / `firebase-web-config` | `<environment>-firebase-web-config.json` | `FIREBASE_API_KEY`, `FIREBASE_APP_ID`, project ID and auth domain | Firebase Project settings → General → Your apps → SDK configuration; register derived app separately | Console read for retrieval; app-registration permission for creation | Preparation/browser auth | Re-readable; identifiers are browser-visible, not confidential credentials |
| MongoDB runtime | Each app/environment | App / `mongodb-runtime` | `<environment>-mongodb-runtime.json` | `MONGODB_URI` | Atlas Database Access: create scoped user and retain generated password; Connect supplies URI template | `readWrite` on app database, selected cluster and allowed network | Web/workers | Password not recoverable from Atlas; retrieve protected copy or deliberately reset/update runtime |
| Redis authentication | Each current app/environment | App / `redis-password` | `<environment>-redis-password.txt` | VPS `redis-password`, derived `REDIS_URL` | Current preparation generates it on host; export through authorized operator to protected store | Private app Redis DB 0 | Redis/web/workers | Current preparation has no password-import option; operator recovery required. Fresh instance may use new password with matching app config; retain existing password for existing instance |
| Cloudflare verification | Shared owner; current staging | Shared / `cloudflare-read-token` | `<environment>-cloudflare-read-token.json` (`apiToken`) | `CLOUDFLARE_READ_TOKEN` | Reuse token; otherwise owner creates scoped token in Cloudflare API Tokens | Account Tunnel Read, Zone DNS Read for selected resources | Route discovery/release verification | Retain token at creation; replace deliberately if unavailable; not a connector token |

Current staging has only the three Actions secrets listed above. Runtime Firebase,
MongoDB and Redis credentials are **not** currently Actions secrets. Public deployment
settings are tracked in the application's environment JSON; GitHub Actions variables
are unused. Runtime files and retained snapshots on the VPS remain private.

### Setup authority and conditional recovery inputs

| Purpose | Applicability | Password-manager item | Local filename (if needed) | Actions secret / variable | Acquisition | Permissions | Consumer | Recovery / rotation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Atlas administration | Setup only | Shared / `atlas-provisioner` | `<environment>-atlas-provisioner.json` | Current staging: none; legacy `ATLAS_CLIENT_ID`, `ATLAS_CLIENT_SECRET` are not public/private API keys | Atlas owner supplies existing API key (`publicKey`, `privateKey`) or service account (`clientId`, `clientSecret`) | Project Read Only for discovery; separately scoped user/network administration for approved writes | Operator/setup tooling | Keep secret at issuance; public/client ID alone is insufficient; read-only discovery cannot provision |
| Google administration | Setup only | Shared / `google-provisioner` (or project owner reference) | None for console login; protected identity export only if selected tooling needs it | No new staging secret; legacy OIDC bindings are public config | Existing authorized Google/Firebase operator login | Selected app registration/Auth settings; IAM changes only when explicitly needed | Operator/provider setup | Account recovery/MFA stays with owner; do not generate service-account keys by default |
| Tunnel/DNS administration | Setup/relocation | Shared / `tunnel-owner-access` | None for existing owner workflow | No new app secret; legacy `SHARED_OWNER_TOKEN` is not needed by current owner-managed staging route | Access existing agentic-poc owner runbook/workflow | Owner-authorized route/DNS writes | Tunnel owner | Record account/workflow reference; owner retains tokens/state; app read token cannot write |
| GitHub setup | Repo creation/secrets/package setup | Shared / `github-setup-access` | None for authenticated CLI | Automatic `GITHUB_TOKEN` handles release publication | Existing authenticated GitHub CLI/account | Repo creation/access, secrets write and package visibility as required; document exact permissions if a token is chosen | Setup operator/agent | Reauthenticate via owner; never store CLI session in app secrets |
| DB recovery | Conditional, implementation required | App / `mongodb-recovery` | `<environment>-mongodb-recovery.json` | Proposed consumer only; no installed secret name | Atlas owner creates separate recovery identity after commands are chosen | Verify backup/restore/GridFS operations; do not assume `dbAdmin` is sufficient | Future manual recovery workflow | Retain/reset through protected store; never replace runtime identity with recovery authority |
| Backup storage | Conditional, destination unresolved | App / `backup-storage-access` | `<environment>-backup-storage-access.json` | Proposed consumer only | Selected storage owner issues scoped access | Required backup read/write/retention scope only | Future backup/restore | Save issued credentials; recovery must work without original VPS |
| Backup encryption | Conditional, implementation required | App / `backup-encryption-key` | `<environment>-backup-encryption-key.txt` | Proposed consumer only | Generate with selected encryption tooling | Decrypt app backups | Future backup/restore | Retain old keys for retained backups; loss can make backups unrecoverable |

### Optional and legacy inputs

These are **not required while disabled**. Public endpoints, workspace IDs, bucket
names and client permissions belong in public configuration; keys stay private.

| Purpose | Applicability | Password-manager item | Local filename | Actions secret / runtime variable | Acquisition | Permissions | Consumer | Recovery / rotation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dify execution | Live Dify only | App / `dify-execution-<binding>` | `<environment>-dify-execution-<binding>.txt` | `DIFY_KEY_<BINDING>` referenced by `DIFY_ORCHESTRATORS_JSON` | Existing Dify Community app API Access; use separate app/env bindings, tag `app:<project>-<environment>` | Selected Dify app execution | AI worker | Save issued key; owner retrieves if supported or rotates; preserve binding names |
| Dify management | Only selected lifecycle features | App / `dify-management` | `<environment>-dify-management.txt` | `DIFY_MANAGEMENT_KEY` | Dify owner supplies compatible console credential for selected deployment | Required workspace lifecycle actions | Server lifecycle code | Verify credential type/expiry with owner; no assumption of permanent session token |
| Dify credential encryption | Live managed credentials | App / `dify-credential-encryption` | `<environment>-dify-credential-encryption.txt` | `DIFY_CREDENTIAL_ENCRYPTION_KEY` | Generate 32 random bytes encoded as 64 hex characters | Local encryption/decryption only | Server credential storage | Preserve key for stored ciphertext; rotation requires migration, not simple replacement |
| Persona completion | Live completion only | App / `persona-completion` | `<environment>-persona-completion.txt` | `PERSONA_COMPLETION_API_KEY` | Selected compatible provider's key management | Selected completion API/budget | Server completion | Save issuance; retrieve if supported or rotate through provider |
| Stripe API/webhook | Live payments only | App / `stripe-api`, App / `stripe-webhook` | `<environment>-stripe-api.txt`, `<environment>-stripe-webhook.txt` | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | Stripe Dashboard API keys and matching webhook endpoint signing secret; use test mode for staging | Required payment operations; webhook verification | Server payments/maintenance | Retrieve where provider permits or roll deliberately; keep test/live and endpoint bindings distinct |
| MCP clients | Enabled MCP only | App / `mcp-token-<client>` | `<environment>-mcp-token-<client>.txt` | `MCP_TOKEN_<CLIENT>` referenced by `MCP_CLIENTS_JSON` | Generate strong client token and register explicit client permissions | Only documented tools/scopes for that client | Server MCP authentication and authorized client | Save original; coordinate client/server rotation; `RUN_MCP_CLIENT_ID` is an identifier, not a secret |
| S3 assets | `ASSET_STORE=s3` only | App / `asset-s3` | `<environment>-asset-s3.json` | `ASSET_S3_ACCESS_KEY_ID`, `ASSET_S3_SECRET_ACCESS_KEY` | Storage provider IAM/key console | Required object operations scoped to app bucket/prefix | Server asset store | Save secret at issuance; rotate via provider; asset recovery also needs object backups |
| Email | No independent SMTP transport in current runtime catalog | None today | None | None | Firebase Authentication provider handles current auth-email settings | Provider configuration only | Firebase Auth | Do not invent SMTP secrets; inventory any future transport before activation |
| Legacy provisioning OAuth | Only legacy procedure that consumes it | App / `google-oauth-client-secret` | `<environment>-google-oauth-client-secret.txt` | Legacy `GOOGLE_OAUTH_CLIENT_SECRET` | Google Auth Platform → Clients; use matching client, protected existing copy or authorized replacement | Matching OAuth client configuration | Legacy provisioner, not routine staging release | Never confuse client ID with secret; current staging does not require this Actions secret |
| Legacy SSH Access/private pulls | Legacy production, not current direct/public staging | App / `cf-access`, App / `ghcr-pull` | `<environment>-cf-access.json`, `<environment>-ghcr-pull.txt` | `CF_ACCESS_CLIENT_ID`, `CF_ACCESS_CLIENT_SECRET`, `GHCR_PULL_TOKEN` | Existing Cloudflare Access owner/service token and GitHub package-read credential if retaining that legacy path | Access application and package read respectively | Legacy tooling | Production compatibility is pending; do not create these to initialize current staging |

Android signing/Play publishing is separate from web deployment; use the application's
[Android guidance](https://github.com/Uniwares-LTD/unibase/blob/main/docs/android.md)
if that delivery channel is selected.

### Existing Unibase storage mappings

Do not rename or overwrite working files. Under `%USERPROFILE%\.config\unibase`,
`firebase-staging-service-account.json` maps to `firebase-admin`,
`firebase-staging-web.json` to `firebase-web-config`, `atlas-discovery.json` to
Atlas discovery access (not proof of write permissions), and
`cloudflare-discovery.json` to `cloudflare-read-token`. `uniwares-deploy-user` is
the deployment key. `unibase-staging-database.json` holds the runtime database
identity/password; `unibase-staging-host-input.json` is the sensitive preparation
bundle, not an independent credential source. The existing operator key remains
under `.ssh` as above. Redis is currently generated/stored on the VPS; a vault
copy is a recommendation, not verified completed backup evidence.

### New-deployment credential checklist

Copy this checklist into a protected setup note. Fill **references only**, mark
optional entries disabled, and request missing inputs together. A vault reference
does not grant an agent vault access: provide a protected export when necessary.

```text
Project/repository and reviewed source revision:
Environment (staging; production compatibility plan if applicable):
Public environment JSON / selected infrastructure profile:
Destination host / verified host-key reference / operator access reference:
Vault item or local path — deployment SSH key:
Vault item or local path — Firebase Admin JSON:
Firebase project/web app IDs and web-config reference:
Vault item or local path — app MongoDB runtime credentials:
Redis — new host-generated credential, or existing protected reference:
Vault item or local path — Cloudflare read token:
Setup access references — GitHub, Google, Atlas, tunnel/DNS owner:
Hostname, listener/subnet allocation and provider network approval:
Optional integrations — disabled, or credential references from inventory:
Recovery — planned/not implemented, or DB/storage/encryption references:
Missing inputs and owner:
Preparation/release verification and remaining operator actions:
```

### Recovery and automation boundary

Recommended flow: password manager → protected local export → destination repo
secrets and reviewed host preparation. Preserve readable protected originals:
GitHub's secrets API returns metadata, not stored values. Children do not inherit
Unibase secrets; GitHub Free private repos cannot use organization secrets.
See [GitHub secrets API](https://docs.github.com/en/rest/actions/secrets) and
[organization-secret availability](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets#creating-secrets-for-an-organization).

**Implementation required:** automated initialization and restricted runtime-secret
restoration. Prerequisites are a reviewed secret manifest, destination-specific
identity validation, root-owned bounded installation operation and authenticated
setup access. Acceptance: preview names/references without values; populate only
the intended repository; restore missing files atomically; refuse conflicting
existing configuration; preserve ownership/modes; resume interrupted preparation;
no secrets in logs/artifacts; verify runtime on the intended destination. Define
new Actions secret names with that implementation, not as fictitious installed inputs.

Current `prepare-host.py` is initial staging preparation, not a general recovery
command: existing routes/configuration can reject replay. Ordinary releases must
report missing configuration, not silently reconstruct it. Recovery uses reviewed
operator procedures today. A new server also needs host bootstrap, pinned identity,
allocations, database network access, owner-managed routes and health checks.
Credential restoration does not restore MongoDB/GridFS data. Keep operator/admin
credentials out of ordinary release workflows.

## Existing staging handoff

Confirmed by the operator on 2026-10-24: staging hostname
`unibase-staging.uniwares.co.uk`; shared Firebase project `uniwares-base`, project
number `870391561828`. The display parent `admin-org` is not a Google resource ID.
The operator reports no external schedules or reserved VPN/subnet ranges. These
confirmations do not replace live provider checks or apply-time network checks.

Use existing credentials from the team's password manager where available. Store
local copies outside Git in `%USERPROFILE%\.config\unibase`, accessible only to
the operator and necessary system administrators. Share **file paths or vault item
references only** with the agent; never paste credential values into chat. Do not
attach these files to issues, PRs or workflow artifacts. A reference alone does not
grant access to a vault that the agent cannot read; a protected local export is the
simplest handoff on this workstation.

| Local file | Contents | Purpose |
| --- | --- | --- |
| `firebase-staging-service-account.json` | Existing Firebase Admin SDK service-account JSON for `uniwares-base`, unchanged | Shared staging runtime identity |
| `firebase-staging-web.json` | Existing web application's Firebase configuration JSON including `projectId`, `appId`, `apiKey`, `authDomain` | Validate app registration and client configuration |
| `atlas-discovery.json` | Existing API key: `publicKey` and `privateKey`; alternatively service account: `clientId` and `clientSecret` | Atlas control-plane inventory; distinct from a database connection URI |
| `cloudflare-discovery.json` | JSON object with `apiToken` | Read tunnel identity/configuration and zone DNS |

Suggested Windows preparation (does not create or download credentials):

```powershell
$providerDirectory = Join-Path $env:USERPROFILE '.config\unibase'
New-Item -ItemType Directory -Force -Path $providerDirectory | Out-Null
explorer.exe $providerDirectory
```

Inspect folder permissions before saving credentials; inheriting a user profile's
permissions is not proof that a folder is restricted. Use the folder's Security
properties to limit access to your account and required system administrators.
Keep credential values out of shell commands/history. Save JSON with an editor or
export directly from the password manager; do not overwrite an existing key.

For Firebase, first reuse the saved service-account key. The Firebase console's
Project settings -> Service accounts identifies the account; existing private keys
cannot be downloaded again. If no copy exists, report that before generating a new
key. Project settings -> General -> Your apps -> web app -> SDK setup/configuration
provides web configuration. If there is no web app, report that; app registration
and authorized-domain changes belong to the reviewed setup scope.

For Atlas, reuse an existing Administration API key pair or service account assigned to the owner's project
`6a869d84e65675f845fa22eb` with **Project Read Only** for discovery. Atlas recommends
service-account client ID/secret authentication for new integrations, but existing
public/private API keys remain supported through HTTP Digest; do not relabel them
as client credentials or create a replacement merely for discovery. Its API access list must permit
the machine performing discovery; this is separate from the cluster's database
network access list. If access is unavailable, the operator can supply sanitized
cluster, database-user role and network-list evidence instead. Do not grant broad
write permissions merely to finish discovery. App user creation/network changes
are reviewed separately for Phase 2; the runtime user gets `readWrite` only on
`unibase_staging`, not administrative API credentials.

For Cloudflare, use a scoped API token with **Account: Cloudflare Tunnel: Read** on
the existing owner's account and **Zone: DNS: Read** on `uniwares.co.uk`. This is
an API token, not a tunnel connector token or Global API Key. Existing owner
configuration identifies the account/zone; see [the inventory](inventory/srv1.md).
Tunnel and DNS writes stay with agentic-poc's owner process. The app's installed
`CLOUDFLARE_READ_TOKEN` repository secret needs only these read permissions.

For a new operator/missing credential only, provide the available protected references
and anything unavailable in one reply. Existing staging credentials are already installed;
do not request them again to run acceptance or routine deployment. The agent
reads only the necessary files, suppresses secret-bearing output, and records
non-secret identifiers and permission results. Never copy provider credentials
into a deployment control bundle. Discovery does not authorize resource changes.

References: [Firebase Admin setup](https://firebase.google.com/docs/admin/setup),
[Firebase web configuration](https://firebase.google.com/docs/web/setup),
[Atlas API authentication](https://www.mongodb.com/docs/atlas/api/api-authentication/),
[Cloudflare API tokens](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/).

Return to the [three-phase runbook](operations.md#1-connect-and-prepare).
