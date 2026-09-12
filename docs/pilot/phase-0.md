# Phase 0 — initial evidence and remaining gates

Status: **in progress; not ready to advance Phase 1**. Evidence collected September 11, 2026. This is a sanitized inventory; private connection details, certificate material and the operator profile remain outside Git. No pilot services or new agent workspaces are deployed.

## Verified baseline

| Check | Observed result | Limit |
|---|---|---|
| dev-host identity | Operator confirmed the current workstation is dev-host; Ubuntu 25.10, kernel 6.17.0-41-generic, x86_64 | Host configuration can change |
| dev-host Docker | Engine 29.2.1, Compose 5.2.0, cgroup v2, overlay2, 20 logical CPUs, approximately 62.3 GiB usable RAM | Effective task restrictions and sidecar accounting are not tested |
| QNAP access | Existing operator SSH connection succeeds with strict host-key verification and batch authentication | Does not establish a controller-to-worker service identity |
| QNAP runtime | QTS reports 5.2.9; kernel 5.10.60-qnap; x86_64; about 15.4 GiB usable RAM | Operator-reported full QTS build remains to be correlated; available memory is a snapshot |
| QNAP Docker | Engine 27.1.2-qnap8, Compose 2.29.1-qnap2, cgroup v1, 4 logical CPUs | Docker binary is under Container Station, outside the default SSH PATH |
| Portainer | Version 2.39.6; native-vault API credential resolves exact distinct local and Standard Edge environments, both reported up, through verified HTTPS | Worker isolation and service SSH remain separate gates |
| Storage | Selected QNAP parent share exists; intended control/results/backup directories are separate siblings and not yet created | Same backing volume for backup and live data does not protect against volume failure |
| Existing CLI auth | Codex 0.154.0 reports ChatGPT login; Claude Code 2.1.269 reports first-party subscription login | Login status alone is not an authenticated model call or isolated worker auth proof |
| Fixture Git access | Operator SSH can read the public fixture repository refs | Operator identity must not be copied into workers; scoped deploy-key delivery remains open |
| Pinned fixture | Revision `7fe97ca42b205e2fa969081c017a46f63aa56747`, extracted into a disposable directory, passes all 19 configured unittest cases | Baseline configuration tests do not cover database/port collisions; add the Phase 1/2 runtime probes separately |

The operator selected four initial workers and five maximum. Preserve that target; commissioning still starts with one worker per runtime before increasing to four and then validating five. Four ordinary workers nominally request 16 GiB and eight CPU equivalents, excluding sidecars. Admission must use current available resources: the configured 40 GiB aggregate ceiling is not a promise to allocate 40 GiB on a busy machine. Retain the operator's conservative 100 GiB disk planning allowance and 8 GiB QNAP pilot allowance until the deployed admission/storage policy is measured.

## Profile revisions and tooling finding

Corrected dev-host OS to the observed release/kernel and QNAP architecture to `x86_64` (the CPU model is not an architecture identifier). Preserved the supplied paths, credential profile, fixture revision, four-worker target and numeric limits. The operator subsequently confirmed the phone model and iOS version; both are recorded in the private profile. The phone route and reconnect behavior still need testing.

The default Python keyring is a chain of native OS vault adapters. The setup script formerly rejected all chains, preventing credential setup despite installed native backends. It now accepts a chain only when every fallback is a supported positive-priority native backend. A regression test rejects a mixed native/plaintext chain and an empty chain. No plaintext credential file was created and no secret value was logged.

The proposed egress list now includes subscription login origins in addition to API/Git hosts. [OpenAI authentication](https://learn.chatgpt.com/docs/auth) and its [device login protocol](https://learn.chatgpt.com/docs/app-server) require a subscription login flow; [Claude Code's network documentation](https://code.claude.com/docs/en/network-config) identifies `claude.ai`, `claude.com` and `platform.claude.com` alongside `api.anthropic.com`. This is a candidate policy, not a complete enforced allowlist. Separate worker model/Git access from installer, updater, browser and optional connector traffic; verify the pinned CLIs before granting further hosts.

## TLS and access findings

The original Portainer self-signed certificate covered only loopback identities, not the configured management hostname, and had an empty issuer name. Trusting that certificate did not resolve hostname verification. A temporary SSH-forwarding test also failed because QNAP explicitly configures `AllowTcpForwarding no`; the test tunnel was closed and that policy remains unchanged.

After the operator asked to continue with remediation, the existing standalone Portainer server received a 365-day server certificate signed by a dedicated private CA, covering the configured DNS management hostname and loopback. The server key was generated and retained on QNAP; the CA signing key remains in the workstation's private configuration directory. The original certificate/key pair is backed up on QNAP. Private apply/rollback scripts and a manifest record the exact container, image and paths outside Git. The pair was replaced while Portainer was stopped, then the same container restarted. No image pull, recreation or pilot stack deployment occurred. Other QNAP container IDs/states matched the pre-change snapshot.

Verified `GET /api/status` with hostname validation and the new CA before updating the private profile's CA bundle. Version remains 2.39.6. Retrieved the API credential from the native vault without logging it; `GET /api/endpoints` matched both exact configured names, distinct IDs, expected local/Edge types, reported-up status and no reported asynchronous mode. Read-only Docker proxy `GET /api/endpoints/<id>/docker/version` also succeeded for both environments: QNAP Engine 27.1.2-qnap8 and dev-host Engine 29.2.1. This verifies live access through the Standard Edge connection, beyond stored endpoint status. TLS verification and redirect refusal remain enabled. See [Portainer's certificate guidance](https://docs.portainer.io/advanced/ssl).

The CA is trusted explicitly by this pilot profile, not installed into global or browser trust. Browsers need the public CA certificate imported to trust this management origin. Direct LAN-IP access is not covered by this certificate. Renew the server certificate before its one-year expiry; retain the private manifest, CA signing key and QNAP rollback pair securely. The existing Edge agent tolerates self-signed polling certificates; successful connectivity does not establish strict agent-side TLS verification, which remains a hardening item.

Local SSH listens. A temporary source-restricted, forced-command-only key successfully authenticated from QNAP to dev-host over the LAN with an independently pinned host key. The probe authorization and all remote probe key/known-hosts files were removed afterward. Neither permanent operator access nor a controller service alias has been marked verified. The service identity must be tied to the fixed request/attach contracts; do not grant a generic autonomous shell just to make inventory pass.

## Host lifecycle finding

Ubuntu 25.10 [reached end of life on July 9, 2026](https://lists.ubuntu.com/archives/ubuntu-security-announce/2026-July/010877.html); Canonical identifies Ubuntu 26.04 LTS as its supported upgrade path. Record a host upgrade/compatibility decision before deploying the pilot. No OS upgrade or package installation was attempted; it requires a separate maintenance plan protecting existing services and development work. Read-only inventory and configuration preparation can continue.

The [host readiness and access runbook](host-readiness.md) records the maintenance preparation, package commands and phase ownership of temporary versus permanent SSH access. QNAP has SSH but no `python3` on its default SSH PATH; controller runtime provisioning remains explicit.

## Remaining Phase 0 gates

- [ ] Supported host OS/upgrade decision and post-upgrade Docker/driver compatibility checks.
- [ ] Tested Termius/private phone route (phone model and iOS version are now recorded).
- [x] Pilot Portainer credential stored in a native vault; exact environment/type/Standard Edge metadata checks through a verified TLS route.
- [x] Portainer management TLS remediated with private backups and rollback; HTTPS health and credential checks pass.
- [ ] Verified controller-to-worker authenticated route and operator recovery access.
- [ ] tmux/mosh availability and later real phone reconnect test. Packages are absent on dev-host; installing them requires local sudo authentication, which is not available noninteractively.
- [ ] Disposable per-worker subscription login/model smoke tests, refresh/expiry behavior and scoped Git authentication. No personal home directory or blanket SSH-agent forwarding into workers.
- [ ] Measured deployable RAM/disk/sidecar budgets, permissions on the chosen storage roots, and an explicit backup failure-domain decision.
- [ ] A fixture specification that pairs the pinned Python baseline with runtime isolation probes required by P01/P02.

Partial inventory and green configuration tests do not close [Phase 0 (#2)](https://github.com/unearth4334/dev-stack/issues/2). The [pilot plan](index.html) retains its dependent phase gates. Once access is resolved, record commands, expected/actual outcomes, pinned versions and sanitized evidence before advancing.
