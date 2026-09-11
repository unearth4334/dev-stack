# Configure the terminal-first pilot

Run this on your trusted workstation, from the repository. Python 3.10+ is required. The script does not install software, connect over SSH, execute fixture commands, create directories on remote hosts, or deploy stacks.

```bash
cd ~/dev/dev-stack
python3 scripts/dev_stack.py configure
python3 scripts/dev_stack.py doctor
```

Enter keeps a displayed default or previous answer. `?` clears a field to unknown. Unknown values can be saved; `doctor` lists missing field names and exits 1 until required inputs are supplied. Ctrl-C cancels the current configuration transaction without changing the saved profile. Cross-field inconsistencies reject the save; rerun to correct them. Use sections to keep each transaction short:

```bash
python3 scripts/dev_stack.py configure --section portainer
python3 scripts/dev_stack.py configure --section access
python3 scripts/dev_stack.py fields
```

`--profile NAME` before the command selects another independent profile. No values have been collected from the operator yet; suggested names and budgets are not verified facts.

## Configuration layers

| Layer | Location and ownership |
|---|---|
| Portable pilot intent | Reviewed defaults and input schema in [scripts/dev_stack.py](../scripts/dev_stack.py), architecture in the [pilot plan](pilot/index.html) |
| Private machine settings | `$XDG_CONFIG_HOME/dev-stack/profiles.json`, default `~/.config/dev-stack/profiles.json`; override with absolute `DEV_STACK_CONFIG_HOME` |
| Credentials | Profile-specific environment variables or a supported native OS keyring; never the JSON profile |

The script refuses private profile storage within a Git repository. New profile directories use mode 700 and atomic file replacements use mode 600 on POSIX; existing files must be owned by the current user and have no group/other permissions. Profiles contain private infrastructure metadata even though they have no designated secret fields. Do not commit them or paste their contents into issues. Existing unrelated profiles are preserved, unknown schema fields rejected, and symlink profile files refused. Configure from one terminal at a time; simultaneous edits are not supported.

## Variables and when they are needed

The `fields` command is the exact machine-readable-schema inventory in human-readable form. Each field is also prompted with its type/meaning.

| Section | Inputs | Purpose / gate |
|---|---|---|
| `portainer` | HTTPS origin, exact QNAP and dev-host environment names, existing/new credential profile name, optional local CA bundle | Read-only environment lookup in Phase 0; never guess IDs or disable TLS |
| `access` | Workstation SSH aliases for QNAP/dev-host; worker service alias as configured on QNAP; private route description; phone OS, Termius version; private mosh UDP range | Phase 0 network inventory; Phase 1 restricted SSH and phone attach trial |
| `hosts` | Actual dev-host/QNAP OS, QNAP architecture and available RAM, dev-host free workspace disk | Record operator measurements now; verify runtime versions, cgroups, disk backing and capacity on each actual host in Phase 0 |
| `storage` | Remote absolute workspace, control, result and backup directories; retention days; minimum free disk | Paths are intent, not auto-created or locally tested. QNAP state/results/backup paths cannot overlap. Verify mounts, permissions, capacity and backup failure domain before rollout |
| `agents` | Per-CLI `subscription` or `api`; fixture Git `public`, `ssh` or `https-token` | Record auth mode only. Verify disposable per-workspace auth and refresh behavior in Phase 0; never copy broad home directories |
| `fixture` | Trusted repository URL, full immutable commit, verification argv as JSON, internal container-build requirement, outbound host list (`[]` explicitly denies all; null is unknown) | Scope the reproducible fixture and grants. No command is run by setup. `needs_container_builds=yes` requires a separate-builder/VM decision |
| `capacity` | Initial/max workers, ordinary RAM/CPU, aggregate RAM, host/support reserves, heavy-build concurrency, active-work budget per attempt | Proposed admission limits. Defaults: 2→5 workers, 4 GiB/2 CPU per ordinary task, 40 GiB aggregate, 16+8 GiB reserves, one heavy build, 120 active minutes per attempt (quota/input waits excluded) |

Only the CA bundle is optional for completion of this input inventory. A `doctor` exit 0 means these fields are present and locally consistent, **not** that Phase 0 or deployment is ready. Resource budgets still need measured host/sidecar validation; egress names are a proposed policy, not an installed firewall. Five-worker capacity is demonstrated in Phase 6, not established by arithmetic.

Phase 0 additionally records observed Docker/Compose, SSH/mosh/tmux and CLI versions, baseline workload behavior, host-key verification, Portainer edition and actual Edge Standard connectivity. Phase 1 pins image/CLI versions and protocol contracts. Phase 2 pins a reviewed shared-skills Git revision and defines project-specific secrets, UID/GID mappings, PID/disk limits and tested network enforcement. These are implementation outputs, not values the operator must guess to run setup. No web hostnames, UI keys, browser authentication or TLS proxy settings are required for this pilot.

## Credentials

The pattern follows the operator's [Portainer deploy skill](https://gist.github.com/unearth4334/e40579c112a31d4c0a3ed275cbb911e7). Choose its existing credential profile name explicitly to reuse that credential namespace; the wizard does not inspect other projects or import their settings.

```bash
python3 scripts/dev_stack.py credentials portainer
```

This prompts without echo and stores only in a supported native OS vault. Python `keyring` is optional, and the workstation must have a usable Secret Service, KWallet, libsecret, macOS or Windows backend. Plaintext, alternate/chained backends and home-grown encryption are refused. See [keyring's installation and backend guidance](https://keyring.readthedocs.io/en/latest/) if needed; no keyring service is installed automatically. This workstation vault does not by itself provide runtime credential delivery on QNAP/dev-host.

| Credential | Resolution order / storage |
|---|---|
| Portainer | `PORTAINER_API_KEY_<CREDENTIAL_PROFILE>` (uppercase; punctuation becomes underscores), then `PORTAINER_API_KEY`, then native keyring service `portainer-deploy`, account `<credential_profile>@<HTTPS origin>` |
| OpenAI API mode | `OPENAI_API_KEY`, or `credentials openai`: keyring service `dev-stack`, account `<profile>:openai` |
| Anthropic API mode | `ANTHROPIC_API_KEY`, or `credentials anthropic`: keyring service `dev-stack`, account `<profile>:anthropic` |
| GitHub HTTPS token | `GH_TOKEN`, or `credentials github`: keyring service `dev-stack`, account `<profile>:github` |

The current script consumes only Portainer credentials for diagnostics. Other vault entries prepare for a reviewed scoped runtime delivery path; they are not injected into workers yet. Subscription logins and SSH private keys stay in their supported authentication mechanisms; do not paste them into API-key fields. Use distinct credential profile names if their uppercase/underscore environment forms would collide.

For a workstation without a native keyring, a one-time hidden prompt is sufficient for the Portainer check:

```bash
python3 scripts/dev_stack.py doctor --portainer --prompt-key
```

The key is used in memory for that check and discarded on exit. Alternatively provide a credential through the session environment or CI secret facility; do not put a literal key in shell history, command arguments or a checked-in `.env`. There is no plaintext credential-file fallback. Replacing a keyring entry does not revoke the old token at its provider.

## Diagnostics

```bash
python3 scripts/dev_stack.py doctor
python3 scripts/dev_stack.py doctor --portainer
```

Default `doctor` only validates local input; it makes no network request and does not unlock the credential vault. `--portainer` explicitly performs `GET /api/endpoints`, requiring exactly one matching environment for each name, distinct positive IDs, Docker-local/Edge endpoint types, reported up status, and no reported async Edge mode (nested or legacy metadata). The field mapping follows the [Portainer API model](https://github.com/portainer/portainer/blob/develop/api/portainer.go). It does not inspect stack environments or invoke Docker proxy operations. Endpoint metadata is not proof of a working Standard tunnel or remote runtime. Names, IDs, raw API bodies and secrets are omitted from diagnostic output.

HTTPS verification is mandatory; use the optional CA bundle when system trust is insufficient. Redirects are refused so the API key cannot follow an unexpected origin. API responses are bounded, request timeout is 20 seconds, and HTTP/network error bodies are suppressed. A failed check does not rewrite settings or retry a mutation. Live Portainer checks require a configured profile and a credential you enter locally; none have been run as part of implementing the wizard.

## Managed setup and recovery

Managed setup may create the documented JSON directly with mode 600. Shape: `{"schema_version":1,"profiles":{"pilot":{"portainer":{"url":"https://portainer.example.test:9443"}}}}`. Section/field names come from `fields`; omitted or null fields are unknown, and unknown names are rejected. Do not use that partial example as a complete profile.

Rerun `configure --section SECTION` to update settings; `?` removes an obsolete optional CA path or resets an answer. A missing profile produces a clear diagnostic. Invalid JSON/schema is not overwritten: correct or move aside the private file locally, then configure again. Deleting a private profile does not remove vault entries, revoke tokens or change remote infrastructure. Use the OS vault/provider tools for credential removal and revocation.

## Multi-day sessions and quota waits

A development session can span days and multiple execution attempts. `capacity.task_deadline_minutes` retains its existing key and numeric value for compatibility, but specifies an **active-work budget per attempt**, not a session expiry. No runtime currently enforces this setting; Phase 3 implements and verifies these semantics before rollout. Keep 120 as the initial active-work allowance. Quota waits, operator-input waits and queued time do not consume it. Active tool execution does count; silence or a sleeping process alone is not evidence of a quota wait.

A confirmed provider limit produces `waiting_for_quota`, preserves the checkout and provider session reference/state, and records any trustworthy retry time. Resume revalidates credentials, capacity and exclusive workspace ownership. An unknown reset time requires operator input or bounded backoff; never repeatedly restart the agent or switch identities to avoid provider limits. Quota waiting is not task failure or permission to delete a workspace.

The controller-disconnect allowance is a separate supervisor safety setting, defined and tested in Phase 3. Pausing the active-work clock does not extend permission for background tools to run during an outage. Account for retained containers and sidecars until they actually stop; recover resources only after verified checkpoint/stop. Storage retention applies to captured results of completed/explicitly abandoned tasks, not an unfinished session waiting for quota.
