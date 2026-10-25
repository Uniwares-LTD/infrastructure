# Staging provider access handoff

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
