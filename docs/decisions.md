# Decision register

Decisions are proposed unless explicitly marked confirmed. “Confirmed input” records the requested direction, not a verified live deployment. Research and product status were checked September 10, 2026.

| ID | Topic | Current position | Status | Reopen when |
|---|---|---|---|---|
| D01 | Placement | QNAP control services; dev-host execution | Confirmed input | Capacity or runtime compatibility prevents it |
| D02 | Infrastructure management | Retain existing Portainer; separate workspace ownership | Proposed | Portainer integration adds more complexity than value |
| D03 | Workspace platform | Fixed Docker templates owned by a trusted Python runner | Selected for pilot; compatibility gate pending | Host compatibility, isolation, or resource budget fails |
| D04 | Agent UI | No runtime web UI; Termius/CLI only | Deferred by operator | Operator explicitly reopens web UI scope |
| D05 | Execution boundary | Unprivileged containers for trusted tasks; VM/microVM class for stronger isolation or container builds | Proposed | Threat model or build requirements demand stronger default |
| D06 | Source isolation | Independent clone and branch per task | Proposed | Measured storage cost warrants controlled worktrees or snapshots |
| D07 | Agent transport | Structured CLI/API for orchestration; Termius with mosh + tmux for people, SSH + tmux fallback | Human access intent confirmed; implementation pending | Selected agent offers no usable structured interface |
| D08 | Task authority | Durable deterministic state and policy; planner proposes work | Proposed | Existing platform fully covers this contract |
| D09 | Secrets | Environment/native OS keyring bootstrap; scoped runtime grants using an existing protected store | Selected bootstrap; runtime delivery pending | Edition, hardware, bootstrap, or policy requirements fail |
| D10 | Release access | Dedicated release path using existing deployment skill | Proposed | A reviewed broker replaces direct credential delivery |
| D11 | Shared skills | Reviewed Git releases pinned by revision/digest | Proposed | Scale warrants a distribution registry |
| D12 | Artifact storage | QNAP immutable directories with private SSH/SFTP access | Proposed | Storage lifecycle or integration needs justify object storage |
| D13 | Monitoring | Minimal events/metrics first; Prometheus/Grafana as needed | Proposed | Existing monitoring already covers the required signals |
| D14 | Network | Private control plane and explicitly constrained worker egress | Proposed | Access requirements need a different exposure model |
| D15 | Git integration | One integration lane per repository with tests on merged result | Proposed | Repository already has an equivalent merge queue |
| D16 | Vibe Kanban / Daytona public core | Reference only; do not adopt for the new platform | Proposed exclusion | Maintained supported successor is independently assessed |

## Confirmed runtime and hardware scope

Codex CLI and Claude Code are both required, with 2–5 concurrent workers total. Dev-host has an Intel Ultra 7 265, 64 GiB RAM, and RTX 5070 Ti, as reported by the operator. See the [inventory](inventory.md). GPU use is optional pending a concrete workload; it is not a prerequisite for the initial externally hosted-model plan.

## Information still needed

These questions do not prevent planning; they gate the corresponding implementation choices.

1. Should Codex CLI and Claude Code use subscription logins, API keys, or different modes per runtime?
2. What are dev-host's OS, storage, virtualization setup, and existing load; what are QNAP's hardware and OS details?
3. Which repositories/tests should define representative load for the confirmed 2–5 workers?
4. Are tasks limited to trusted personal repositories, or will agents execute arbitrary external repositories and pull requests?
5. Must projects build Docker images or start Compose stacks inside their workspaces?
6. What private networking, DNS, TLS, and reverse proxy services already exist?
7. Which Portainer edition/version is installed, and can the selected Docker/SSH boundary be enforced?
8. What private SSH identities, backup destination and artifact retention policy already exist?

## Evidence and uncertainty

The reviewed Portainer skill has revision `7ad4fa91594a2ad99f7ff34946216be272a39308`. Its configuration split is compatible with future injected secrets. Live Portainer endpoints and credentials were not inspected.

The local workspace has Codex CLI `0.154.0`; dev-host's agent installations are unknown. Product documentation is changing quickly: Coder's native agent is distinct from third-party CLIs, OpenHands's current Canvas differs from legacy Local GUI and documents a shared-origin credential risk, Docker Sandboxes has a current Linux/KVM path, and the public Daytona core and Vibe Kanban have maintenance/sunset notices. Vibe Kanban's company shutdown announcement describes continued local/community operation; it is not a claim that the local software is unusable.

See the [research sources](research.md#sources) for evidence. Pilot outcomes should replace assumptions here, including exact versions, measured resource use, edition entitlements, and failed acceptance scenarios.

## Pilot delivery scope

The [Pilot v0.1 implementation plan](pilot/index.html) owns current phase ordering. Its Phase 1 resolves D03–D05 before permanent implementation. Scoped credential delivery is mandatory from the first workspace; deploying a new central secret manager (D09), GPU support, automated integration/releases, and public previews can follow the pilot. The original broad roadmap remains historical context.

## Terminal-first pilot clarification — September 11, 2026

The operator deferred the web UI. Coder/OpenHands trials and browser publication are outside the pilot. The selected baseline is a Python CLI with SQLite control state on QNAP, a fixed-template Docker runner on dev-host, restricted SSH JSON control, and Termius with mosh/tmux for interactive access. Phase 1 validates this baseline rather than reopening the product shortlist. Historical research does not override this scope.

## Multi-day session lifetime

Quota-limited sessions lasting days are a confirmed operator requirement. Sessions/workspaces persist across quota waits and attempts. The legacy `task_deadline_minutes` key represents active-work minutes per attempt, excluding confirmed waits; a separate controller-disconnect deadline remains mandatory. See the [quota-wait contract](pilot/index.html#quota-waits). Runtime enforcement remains Phase 3 work, with retention protection in Phase 5 and P17 acceptance in Phase 6.
