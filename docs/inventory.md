# Inventory and capacity

## Confirmed inputs

Reported by the operator; not independently inspected on the machines.

| Item | Value |
|---|---|
| Required agent runtimes | Codex CLI and Claude Code |
| Initial concurrency | 2–5 workers total across both runtimes |
| dev-host CPU | Intel Ultra 7 265 |
| dev-host RAM | 64 GiB |
| dev-host GPU | RTX 5070 Ti |
| Execution placement | dev-host, existing Portainer Edge Agent Standard environment |
| Control-service placement | QNAP, existing Portainer local environment |

## Remaining inventory

| Area | Still to establish |
|---|---|
| dev-host OS | Distribution/version or other OS, kernel, bare metal versus VM/WSL |
| Execution runtime | Docker/Compose versions, rootless compatibility, cgroups, virtualization availability |
| Storage | SSD capacity/free space, filesystem, quotas, workspace/cache location |
| Existing load | Other services, baseline RAM/CPU use, available build capacity |
| GPU | Driver, usable VRAM, existing consumers, container/VM access if needed |
| Agent authentication | Subscription or API mode per CLI; installed versions and refresh behavior |
| QNAP | Model, architecture, OS, available CPU/RAM/storage, backup configuration |
| Portainer | Version/edition, endpoint IDs, roles, TLS trust and Edge connectivity |
| Networking | Private route, DNS, reverse proxy, UI and preview access |

Linux remains a design assumption until the OS is confirmed. CPU model alone does not establish that KVM is available to the execution environment.

## Provisional capacity budget

This is a proposed admission budget, not a benchmark or a claim about current free memory.

| Allocation | GiB | Purpose |
|---|---:|---|
| Host reserve and existing services | 16 | Initial reserve; increase if baseline use requires it |
| Execution support and contingency | 8 | Supervisor, collectors, runtime overhead and bursts |
| Aggregate task budget | 40 | Agents, builds, browsers, databases and sidecars combined |
| Total | 64 | Matches reported physical RAM |

Start with two workers, one Codex CLI and one Claude Code. A 4 GiB ordinary-task budget is the initial test setting. At five workers, five 4 GiB tasks account for 20 GiB, while five 8 GiB tasks would consume the entire 40 GiB task allowance. Memory limits for sidecars and VM overhead must be counted; a limit on the agent container alone does not cap the whole task.

Begin with one heavy build at a time and a two-CPU-equivalent limit per ordinary worker. These CPU quotas are scheduling settings, not dedicated physical-core assignments. Increase limits or build concurrency only after measuring test latency, memory peaks, disk contention, and host responsiveness. Larger tasks consume more of the shared admission budget and can reduce available slots below five.

The reported RAM gives room to test the intended range under this budget. Actual capacity depends on project dependencies, browser tests, existing host workloads, and storage. Validate a mixed five-worker run before treating five as the routine capacity.

## GPU role

Keep GPU access off in the initial ordinary-workspace profile. The initial plan uses externally hosted models; owning a GPU does not require introducing local inference into the first milestone.

If a project later needs CUDA, graphics, or local inference, create a separate GPU workload profile with explicit access and scheduling. Measure usable VRAM and host-memory consumption first. Initially allow only one GPU workload at a time, unless measured coexistence supports more. A persistent local inference service would have its own budget and would reduce the resources available to task workspaces.

GPU sharing/isolation and any local model selection require a separate compatibility assessment. No driver installation, passthrough configuration, or model download is implied by recording this hardware.
