# Dev stack

> **Superseded (2026-09-19).** This planning repository is archived at tag [`archive/pilot-v0.1-plan`](https://github.com/unearth4334/dev-stack/releases/tag/archive%2Fpilot-v0.1-plan). Active work continues in [dev-stack-v2](https://github.com/unearth4334/dev-stack-v2): Claude Code only, Discord as the frontend, control on dev-host. Nothing below is current.

A self-hosted development platform for concurrent coding agents, with management services on QNAP and isolated execution on dev-host.

Start with the [Pilot v0.1 implementation plan](docs/pilot/index.html), published through [GitHub Pages](https://unearth4334.github.io/dev-stack/pilot/). The [research and architecture report](docs/research.md) explains the recommendations, alternatives, and evidence. The [decision register](docs/decisions.md) separates proposed choices from unresolved questions. The [example task manifest](examples/task.example.json) makes the proposed task contract concrete.

The pilot uses fixed Docker workspaces, a small Python/SQLite command-line controller on QNAP, and a trusted supervisor on dev-host. Use Termius with mosh/tmux for human access and structured CLI interfaces for automation. All runtime web UIs are deferred. Private results are files available through SSH/SFTP.

Research checked on September 10, 2026. This directory contains the pilot plan, configuration tooling and an illustrative manifest; no services have been installed or deployed, and no Portainer credentials have been copied here. Confirmed scope: Codex CLI and Claude Code, with 2–5 concurrent workers on dev-host (Intel Ultra 7 265, 64 GiB RAM, RTX 5070 Ti, as reported). See the [inventory](docs/inventory.md) for remaining OS, storage, QNAP, and authentication questions.

The [development workflow](CONTRIBUTING.md) defines phased issues, review, and delivery. The [original platform roadmap](docs/platform-roadmap.md) is background; the pilot page defines current scope and ordering.

Pilot tracking: [milestone](https://github.com/unearth4334/dev-stack/milestone/1), starting with [Phase 0 — inventory, access and authentication](https://github.com/unearth4334/dev-stack/issues/2). All runtime phases remain unimplemented; the planning/publication PR is [#1](https://github.com/unearth4334/dev-stack/pull/1).

Start configuration with `python3 scripts/dev_stack.py configure`. See [configuration and variables](docs/configuration.md) for private profile storage, credentials and diagnostics. Configuration does not deploy anything or complete the live Phase 0 checks.
