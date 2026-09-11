# Dev stack

A self-hosted development platform for concurrent coding agents, with management services on QNAP and isolated execution on dev-host.

Start with the [implementation plan](docs/implementation-plan.md). The [research and architecture report](docs/research.md) explains the recommendations, alternatives, and evidence. The [decision register](docs/decisions.md) separates proposed choices from unresolved questions. The [example task manifest](examples/task.example.json) makes the proposed task contract concrete.

The initial direction is to retain Portainer for infrastructure, use a separate workspace per task, and control agents through structured interfaces. Evaluate Coder for workspace management and OpenHands Agent Canvas for agent interaction before building a custom web UI. Use SSH/tmux for human access, with mosh optional.

Research checked on September 10, 2026. This directory contains planning documents and an illustrative manifest; no services have been installed or deployed, and no Portainer credentials have been copied here. Confirmed scope: Codex CLI and Claude Code, with 2–5 concurrent workers on dev-host (Intel Ultra 7 265, 64 GiB RAM, RTX 5070 Ti, as reported). See the [inventory](docs/inventory.md) for remaining OS, storage, QNAP, and authentication questions.
