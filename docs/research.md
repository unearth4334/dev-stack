# Research and architecture

## Recommendation

Build a small development platform around a portable workspace contract. Keep Portainer as the infrastructure management layer. Run project code, dependencies, browsers, and tests on dev-host; place the durable task record, operator entry point, artifact publication, and eventually secret management on QNAP. A coding task should receive a distinct repository checkout, execution environment, identity, resource budget, and artifact namespace.

Evaluate **Coder Workspaces** first for provisioning, browser terminals, IDE access, and workspace lifecycle. Evaluate **OpenHands Agent Canvas** separately for interacting with existing coding agents. They solve overlapping but different problems; installing both is not the default. If neither meets the pilot's requirements economically, retain a small supervised runner using native agent interfaces and a basic task index. Avoid building a general agent platform before measuring the gaps.

Use structured agent events for orchestration and SSH/tmux for operator access. Mosh remains a useful optional human connection method. Centralize credential policy, but distribute only the credentials a task needs. Keep the Portainer release credential outside ordinary coding environments.

These are architectural recommendations, not claims that the complete stack has been validated. The most established pieces are Git, container/VM isolation, SSH, declarative environment definitions, and ordinary operational monitoring. New agent control surfaces need direct testing for approvals, cancellation, recovery, and authentication. Public project documentation establishes capabilities; it does not prove reliability on this hardware.

## Starting conditions and scope

The existing management endpoint is configured privately; this public document uses `https://portainer.example.test:9443/` as a placeholder. The intended Portainer environments are QNAP's `local` environment and `dev-host` using Edge Agent Standard. These names and roles are supplied design inputs; endpoint IDs, reachability, edition, versions, TLS configuration, architecture, and spare capacity have not been inspected.

The confirmed agent runtimes are Codex CLI and Claude Code, with two to five concurrent workers. Dev-host has an Intel Ultra 7 265, 64 GiB RAM, and an RTX 5070 Ti, as reported by the operator. Start the pilot with one worker of each runtime, then test mixed workloads up to five workers. One operator, Linux execution, and externally hosted models remain planning assumptions; OS, subscription versus API authentication, storage, workload sizes, and GPU use remain open. Desktop applications or hardware-dependent development may need separate workspace classes. See the [inventory](inventory.md) for a provisional capacity budget.

Success means an operator can submit a task, see its progress, answer a question, inspect a preview or test report, review the patch, and destroy the environment without losing the result. QNAP restarting should not silently lose task identity or cause duplicate work. A development session should not acquire access to unrelated NAS shares or production deployments.

The first release does not need Kubernetes, a service mesh, multi-region scheduling, a new IDE, or a custom secrets implementation. Those would increase operational surface before the core workflow is proven.

## Existing deployment skill

The linked `portainer-deploy` gist already separates repository deployment intent, host-specific profiles, and credential resolution. It supports read-only diagnostics and updating an existing stack, and distinguishes build, deploy, verification, and rollback. Preserve that design. The reviewed revision is `7ad4fa91594a2ad99f7ff34946216be272a39308`; use an immutable revision when distributing it.[^1]

The skill's client should remain a release tool. It is not a task scheduler or a workspace allocator. A future runner needs a distinct lifecycle interface for creating, stopping, and collecting development environments. That interface must not convert arbitrary agent-authored Compose or Terraform into privileged host operations.

For a release task, inject the profile-specific API-key environment variable into a dedicated deploy process, resolve the exact environment and stack, and preserve the skill's artifact verification and authorization behavior. A headless container may not have a usable OS keyring. Central secret delivery can supply the existing environment-variable interface without modifying projects to contain credentials.

Shared skills should contain procedure and validation, while machine configuration contains connection details. A deployment skill being installed in an agent environment must never itself confer permission to deploy.

## What existing software actually covers

| Candidate | Useful role | Material limitation | Recommendation |
|---|---|---|---|
| Portainer | Operate existing Docker environments and support services | No complete coding-task history, agent protocol, or Git integration workflow | Retain |
| Coder Workspaces | Environment templates, lifecycle, IDE/browser access | Terraform ownership and remote provisioning topology need care | First workspace-platform pilot |
| Coder Agents | Native self-hosted coding agent | A different agent harness from Codex or Claude Code | Optional separate evaluation |
| OpenHands Agent Canvas | Web interaction with multiple agent backends | Per-backend state and isolation; newest integration paths need validation | First agent-UI pilot |
| DevPod | Portable remote devcontainers and editor access | Client-oriented; not a central task scheduler | Lightweight workspace alternative |
| Docker Sandboxes (`sbx`) | Per-agent microVMs and an internal Docker daemon | Host requirements, account dependency, and Portainer visibility differ | Test when stronger isolation/build support is needed |
| Vibe Kanban | Task board, branch/diff/review interaction patterns | Company shutdown; transition to community/local operation | Reference design only |
| Daytona public core | API-driven sandboxes and runner architecture | Public core no longer maintained | Do not adopt as the foundation |
| gVisor / Firecracker | Stronger execution boundary | Building blocks, not a development platform | Defer direct integration |

### Coder

Coder models workspaces with Terraform templates and supports container and VM infrastructure. It supplies browser/IDE access and workspace lifecycle, making it the best initial fit for the environment-management part of this project. Its standard Docker installation includes PostgreSQL and lists two CPU cores and 4 GB free memory as requirements. Verify QNAP architecture and headroom before placing it there.[^2][^3]

Current Coder Agents is a native agent loop in the control plane, not a wrapper around third-party CLIs. Its architecture can keep model keys out of tool workspaces, but selecting it changes the agent experience. Keep this choice separate from adopting Coder Workspaces.[^4]

Coder's pricing page currently lists unlimited Community workspaces and up to five concurrent native Coder Agents in Community and Premium, with AI Premium removing that agent cap. This is not a blanket five-process limit on third-party CLIs running inside workspaces. Feature entitlement still needs checking against a selected release; the pricing table's visual checkmarks are not fully represented in text extraction.[^5]

Remote provisioning is the important deployment wrinkle. Built-in provisioners execute Terraform in the Coder server. External provisioners can keep infrastructure access on dev-host, but their documentation is marked Premium and describes special user-scoped behavior as well. Do not assume the desired centrally managed external-provisioner arrangement is free. Test exact entitlements. If using Community with a built-in provisioner on QNAP, a protected Docker SSH/TLS connection is a topology to validate, not an already-proven integration. It gives that provisioner substantial control over the target daemon.[^6]

The Portainer Edge tunnel does not automatically become a general Docker endpoint for Coder's Terraform provider. Keep Portainer responsible for support stacks and let Coder own the workspaces it creates. Editing those same resources through both controllers creates conflicting desired state. Portainer may observe them where the runtime is visible; routine lifecycle changes should use their owner.

### OpenHands Agent Canvas

The current OpenHands repository describes Agent Canvas as a browser control surface with separate frontend and backend launch modes. This differs from older Local GUI instructions still appearing in search results. It is particularly relevant to a central UI with remote execution.[^7]

Canvas supports backends containing Agent Server and, when enabled, Automation Server. Backend selection also changes settings, MCP configuration, secrets, and automations. This is not proof of a single global scheduler or a cross-backend task database. The pilot must establish which central orchestration functions exist and which remain integration work.[^8]

ACP integration launches external agent CLIs as subprocesses. The published provider list includes wrappers for Claude Code and Codex. Those wrappers add another compatibility boundary; pin their versions and test permissions, session resume, tool events, and cancellation. The backend needs an appropriate model credential or CLI login. Backend-level saved secrets are not automatically a per-task central secret policy.[^9]

For the pilot, provision a separate backend container or VM for each task, with only that task's checkout and state mounted. Opening two conversations against one backend should not be treated as two isolated machines. Avoid the convenient example of mounting an entire projects directory when the purpose is per-task isolation. Self-hosted backend authentication and network exposure must be configured explicitly.[^7][^10]

If Canvas passes the interaction tests, use it to avoid writing chat, terminal, and agent controls. If it cannot provide a useful unified overview of several backends, a small index linking task IDs to backend URLs is a better first addition than forking its UI.

There is a specific browser trust issue to resolve before adoption: the current self-hosting guide says the bundled editor shares Canvas's origin, and scripts on that origin can read local storage containing registered backend session keys. A path prefix does not isolate browser credentials. Require a supported mitigation, such as disabling that surface or separating its origin with verified behavior; otherwise reject the shared UI for this credential model. Keep the pilot credentials disposable and limited.[^10]

### DevPod and Docker Sandboxes

DevPod uses devcontainer definitions and providers to create workspaces on local or remote machines. It is explicitly client-only and provides a CLI and desktop application. It is attractive when editor access and reproducibility matter more than a central browser control plane. Disable or constrain automatic credential synchronization; convenience defaults are not the intended credential policy for autonomous workers.[^11]

Docker's current Sandboxes product uses microVM isolation, with a Docker daemon inside each sandbox. This addresses an awkward agent workload: building and testing containers without exposing the host Docker socket. It is a serious runtime candidate, although free CLI availability should not be confused with a verified open-source license for every component.[^12]

Current Linux prerequisites include Ubuntu 24.04 or later, a supported 64-bit CPU, and KVM. Nested virtualized dev-host installations must expose virtualization. Docker also documents PAT-based sign-in for noninteractive operation. Treat host compatibility, unattended lifecycle, credential handling, export, and restart recovery as acceptance gates. Portainer's existing Docker endpoint will not automatically manage microVM internals.[^13][^14]

### Candidates to avoid adopting on stale information

Daytona's live repository states that its core moved to a private codebase in June 2026 and that the public repository will receive no further fixes or releases. Older indexed material still describes the open Compose deployment as a current path. Do not build a new long-lived stack on that unsupported core. A commercial Daytona product or community continuation would require a separate maintenance and licensing assessment.[^15]

Vibe Kanban's repository now links to an April 10, 2026 company shutdown announcement. It describes continued community maintenance and local workspace operation, with remote collaboration services being removed. Its branch, diff review, preview, and task-board workflow remains useful inspiration, but the changed maintenance and service model weakens its fit for this central platform. This does not mean local Vibe Kanban stopped working.[^16][^17]

## Execution isolation

Treat isolation as several independent controls. Each workspace needs separate files, process state, service data, ports, credentials, and resource limits. An agent can run destructive commands accidentally or execute hostile dependency code even when working in a trusted repository.

| Boundary | Initial design | Stronger option or validation |
|---|---|---|
| Source tree | Independent clone per task | Snapshot/COW optimization after measuring disk cost |
| Processes and filesystem | Unprivileged task container; narrow mounts | VM/microVM for untrusted repositories or privileged builds |
| Networking | Task-specific network and enforced management-network restrictions | Dedicated VM network/firewall policy |
| Services | Own database/Redis instances and volumes | Shared server only with explicit per-task database/user isolation |
| Resources | CPU, memory, PID and disk budgets | Dedicated build concurrency class |
| Credentials | Per-task grants; no operator home mount | Brokered operations or workload identity |
| Git integration | Separate task branch and protected base branch | Serialized integration queue |

Git worktrees share repository metadata and objects. That is efficient for trusted concurrent work, but the shared common Git directory complicates container mounts and grants cross-task mutation opportunities. Independent clones are the simpler starting boundary. If later using worktrees, document common-directory permissions, path consistency, locking, and pruning. A branch name alone is not an access control.[^18]

Docker namespaces and reduced capabilities provide useful process isolation, but controlling the Docker daemon is highly privileged. Never mount the host Docker socket into coding workers, including as a read-only filesystem mount: that does not make the API read-only. Do not mount the NAS root, operator home, SSH agent socket, or global credential directories. Privileged components such as a provisioner must live outside the worker boundary.[^19]

Rootless Docker is worth evaluating on dev-host. It reduces daemon/runtime privilege but still requires compatible kernel/resource-control support and has operational differences. A rootless daemon may not be the daemon currently managed by Portainer; verify registration, visibility, metrics, and limits rather than claiming transparent compatibility.[^20]

Where shared-kernel containers are too weak, prefer an existing VM/microVM runtime over building a hypervisor integration. gVisor interposes a userspace application kernel; Firecracker provides KVM-based microVMs. Both are relevant isolation technologies, but neither alone supplies workspace lifecycle, identity, artifacts, or agent orchestration.[^21][^22]

Repository-authored Dockerfiles, devcontainer lifecycle hooks, Compose definitions, and Terraform templates are executable input. Review and allowlist platform templates. Run arbitrary dependency installation or image builds inside the task boundary or a separate constrained builder. An orchestrator accepting a manifest must not accept unrestricted host mounts, host networking, or arbitrary provisioner commands.

Use devcontainer metadata as the portable description of developer tools and editor behavior, with a platform-owned runtime policy enforcing limits and mounts. Supporting the standard does not itself guarantee identical behavior across providers; the pilot should exercise actual startup hooks, users, volumes, and sidecars.[^23]

## Agent control and task lifecycle

Mosh establishes a session using SSH, then synchronizes terminal state over UDP. Intermediate screen states may be skipped. Its default UDP range is 60000–61000, and it does not turn the Portainer TCP tunnel into a terminal connection. This makes it suitable for resilient human terminal use, not a durable event stream or job queue.[^24]

Keep session execution independent of the network client. A worker supervisor starts the agent, captures structured events and stderr, records process exit, and survives the operator disconnecting. SSH/tmux can provide manual inspection or an interactive fallback. A tmux pane is not authoritative task state, and a surviving process is not proof of useful progress.

For the simplest Codex adapter, `codex exec --json` emits machine-readable events and supports structured final output and saved session continuation. Store the provider session ID alongside the task ID. Configure authentication explicitly; do not share the operator's whole home directory with tasks. The local CLI inspected during planning was version `0.154.0`, which is an observation about this workspace, not dev-host.[^25]

For richer interactive control, Codex App Server exposes a bidirectional JSON-RPC-style protocol and approval requests. Current documentation labels the app-server command and WebSocket transport experimental/unsupported for production workloads. Treat it as a version-pinned pilot option, favor a local transport behind a supervisor, and do not expose an unauthenticated listener. It should not silently become a production dependency merely because it offers useful APIs.[^26]

Claude Code provides programmatic execution and JSON/stream-JSON output. Its CLI or SDK can be wrapped behind the same task interface while retaining provider-specific session and permission behavior. ACP is another interoperability option for compatible UIs; it does not provision machines or make all agents' tools and approval semantics identical.[^27][^28]

Separate three concepts in the task record: **workspace** (files and runtime), **session** (agent conversation), and **attempt** (one execution against a task). Resuming a conversation creates a new attempt when appropriate; it does not erase previous errors or reuse an execution lease blindly.

Proposed task states are `queued`, `provisioning`, `running`, `awaiting_input`, `verifying`, `ready_for_review`, `succeeded`, `failed`, `cancelled`, and `lost`. Workspace states are separate: allocated, stopped, retained, and destroyed. “Agent finished” advances to verification; only recorded checks and review policy can establish success.

Persist requests before dispatch. Give each attempt an idempotency key and a lease generation. The worker supervisor is the single owner of an attempt and rejects duplicate starts. If a host disappears, mark execution unknown/lost and reconcile its actual process and workspace before retrying. Lease expiry alone must not start a second agent against the same files. Retry a crashed attempt only after confirming the old process is gone or provisioning a distinct workspace.

Human input and approval responses need IDs, deadlines, and an audit record. An autonomous planner can propose task decomposition and choose among approved capabilities; a deterministic service enforces budgets and target restrictions. Put resource creation and credential issuance behind narrow operations, not unrestricted shell access on QNAP.

## Networking and service ownership

The Portainer Standard Edge Agent polls the server and establishes a reverse tunnel when interactive management is needed. Documented server ports are TCP 9443 for HTTPS/API and TCP 8000 for the tunnel. This explains Portainer connectivity; it does not establish private routing for agent APIs, previews, SSH, or mosh.[^29]

Use an existing private LAN path where suitable, or a deliberately configured VPN/private overlay between QNAP, dev-host, and the operator. A subnet router can make private addresses reachable without installing a client on every resource, but routes and access rules must be scoped. Do not make every worker a general NAS-management client.[^30]

| Flow | Intended access |
|---|---|
| Operator → QNAP | Authenticated UI and artifact reads over HTTPS |
| dev-host → Portainer | Existing Edge polling/tunnel, validated separately |
| QNAP controller ↔ dev-host supervisor | Private authenticated control channel; durable reconnect |
| Task → source/package/model services | Only the dependencies and provider access it needs |
| Task → QNAP | Narrow artifact upload / approved broker endpoints |
| Operator → task preview | Authenticated proxy with explicit route registration |
| Task → Portainer, NAS admin, secret admin | Denied unless a specific privileged task is authorized |

Test network restrictions from inside a worker. Separate Docker bridges alone do not establish all the desired egress restrictions, especially access to host addresses and private networks. Include DNS, IPv6, proxy bypass, and Docker's firewall behavior in validation. A domain allowlist also cannot prevent misuse of an allowed destination that accepts uploads; minimize reachable services and credential scope together.

Use one lifecycle owner for each resource. Portainer manages long-lived QNAP services and the trusted dev-host support stack. The selected workspace provider creates and cleans up task environments. The task service manages attempts. The agent manages only its project work. A manually stopped workspace should be reconciled through its owner rather than causing a competing controller to recreate it unexpectedly.

## Credentials

A centralized secret service is useful once more than one runtime needs repeatable credential delivery. **Infisical** is the first usability-oriented candidate; **OpenBao** is the alternative when fine-grained machine policy and dynamic credentials outweigh setup cost. Do not install both.

Infisical has self-hosted deployment options, including Compose with PostgreSQL and Redis. Its Universal Auth exchanges a machine Client ID/Secret for a token; defaults are not necessarily short enough for ephemeral workers. Some controls, including trusted-IP restrictions for self-hosted Universal Auth, require paid licensing. Verify the exact policies needed before choosing it.[^31][^32]

OpenBao AppRole can issue policy-bound machine tokens. It introduces explicit seal/unseal and recovery responsibilities. Select it only with a documented bootstrap, backup, and unseal procedure that works after a QNAP restart. A secrets server that cannot restart independently can block recovery of the platform that hosts it.[^33][^34]

SOPS is useful for encrypting versioned bootstrap configuration, but it is not a live per-task credential broker. Compose secrets improve delivery by mounting values only into selected containers; they do not provide central policy, automatic rotation, or the same storage guarantees as a dedicated secret manager. Keep these roles distinct.[^35][^36]

Proposed grant classes are repository read, task-branch publish, model access, artifact upload, test-service access, and deployment. Routine coding receives only the first five as needed. Deployment credentials remain in the release process. Use a separate secret-manager identity per role/project initially and move to task-specific identities or brokered grants where the selected product supports them.

The trusted supervisor retains bootstrap access. Workers must not inherit a secret-store administrator credential. Retrieve only named grants after validating the task and deliver credentials through a supported process/file interface. Use isolated home directories and ephemeral secret mounts where possible. Environment variables and readable files are still usable by the agent and its children; central storage does not prevent runtime exfiltration.

Revoking a secret-manager token does not revoke a static Portainer or model key already fetched. Rotate or revoke the underlying credential when needed. Where a provider lacks short-lived scoped keys, prefer a narrowly constrained broker operation: for example, request a deployment of a verified digest to an allowlisted stack, rather than return a Portainer administrator token.

Choose subscription login or API authentication deliberately for each agent. A copied login may involve refresh-token races or shared account quotas across workers. Confirm the provider-supported unattended path, credential precedence, refresh behavior, and usage visibility in the pilot. Do not assume a generic OpenAI-compatible proxy works with every vendor CLI or subscription mode.

## Shared skills and reproducibility

Keep shared skills in one reviewed Git repository, with a release manifest containing source revision, integrity digest, supported agent versions, required tools, and declared capabilities. Initially this can be a small private repository rather than a registry service. Install the selected release read-only into each workspace and record its digest with every attempt.

Project-specific instructions belong in the project repository. Infrastructure procedures and shared tools belong in the skills repository. Runtime-specific installation paths can be adapted from one canonical source; avoid independently edited copies. Active workers should never follow a mutable `main` skill directory that changes mid-task.

A skill that needs network access or deployment capability should declare that requirement, while the platform grants it separately. Review executable scripts, MCP endpoints, package hooks, and installers as part of a skill update. The existing deployment gist is a good seed, but its current immutable revision should be reviewed and released through this process.

Each attempt should record repository/base SHA, image digest, runtime version, model identifier, dependency lockfiles, skills release, relevant nonsecret configuration, and test commands. These records support reproducibility of the environment and evidence; they do not imply that a probabilistic model will generate identical output.

## Artifacts, previews, and review

Start with immutable per-attempt directories on QNAP and an authenticated static HTTP service. Keep Markdown plans in Git. Publish rendered plans, screenshots, test reports, patches, and result summaries under project/task/attempt identifiers. A small index can link these to Git review and the selected workspace UI. Add S3-compatible storage only when lifecycle, upload, or integration needs justify another service.

An artifact upload grant should write only its attempt prefix and should not permit listing other projects. The trusted collector validates paths, rejects symlinks or archive traversal, enforces file/size quotas, scans for likely secrets, and records SHA-256 digests. Copy results into the publication area atomically; do not serve the entire live workspace directory.

Separate artifacts from previews. Artifacts are immutable outputs; previews are running applications with task-owned databases and an expiry. Generated HTML and test reports can contain JavaScript. Serve untrusted content on an isolated origin with no control-plane cookies, disable active content where practical, and use a separate registrable domain for active previews when available. Parent-domain cookies must not bridge that boundary.

Do not grant workers control over arbitrary reverse-proxy labels or route targets. The trusted owner registers a preview route for the known workspace and approved port. Check WebSocket support, authentication redirects, service workers, CORS, and access revocation during expiry. No task database should require a public port.

Use a single integration lane for changes to a repository's base branch. Each task submits a patch or task branch with tests and a summary. Rebase or merge into a fresh integration environment and rerun relevant tests against the actual combined result. Passing tests on two isolated branches does not prove their combination works. Prefer artifact generation without Git write access first; add constrained task-branch publishing when needed.

## Visibility, cost, and operations

Use three views: infrastructure health, task lifecycle, and result quality. Portainer provides container operations; it should not be asked to infer whether an agent is blocked waiting for input or whether its patch passes tests.

Prometheus plus Grafana is an established option for infrastructure metrics. cAdvisor can export container statistics, and Coder has monitoring integrations. Exporters often require broad host visibility and belong to the trusted support layer. Validate cgroup/runtime compatibility before choosing deployment privileges.[^37][^38]

Start with CPU/RAM/disk, queue depth, active attempts, time awaiting input, startup failures, agent exits, lost workers, artifact upload failures, and backup freshness. Track task/session IDs in the event store rather than unbounded Prometheus labels. Do not use agent activity or token count as a productivity score.

Capture provider usage when available and label cost as an estimate with the pricing revision used. Subscription quotas and API billing are distinct. Impose concurrency and wall-time budgets even when token usage cannot be measured accurately. A watchdog should distinguish an idle terminal, slow build, provider rate limit, hung process, and waiting question before cancelling work.

Use bounded local logs first; introduce centralized log indexing only when multi-host diagnosis demands it. Avoid storing prompts, source, secrets, or raw tool results as metric labels. Transcripts and test reports need retention and access controls because they can contain private data.

Keep active checkouts, language-server indexes, build caches, and workspace databases on dev-host local storage. QNAP is the durable result/backup destination. Do not assume a NAS mount is suitable for a transactional database, shared package cache, or heavy Git workload without testing filesystem semantics and latency.

Reserve capacity for the host and support services. A planning formula is `worker slots = floor((available RAM - host reserve - support services) / measured per-task peak)`, then reduce for CPU and disk pressure. Start with two slots and a separate build semaphore. Any numerical RAM/CPU allocation before measurement is a pilot setting, not a hardware requirement.

Back up control-plane databases, published artifacts, platform definitions, and secret-manager recovery material. Test restoring them together. Preserve unfinished patches separately from rebuildable images and caches. Keep an offline recovery route to QNAP and dev-host that does not depend on the UI being repaired. A single QNAP is an intentional failure domain; worker execution should degrade predictably while it is unavailable.

## Adoption decision

Run the portable two-worker pilot first, then compare Coder and Canvas against the same work. Choose the smallest combination that provides acceptable isolation, recovery, approvals, and review. The [implementation plan](implementation-plan.md) defines the ordered work and pass/fail gates.

The likely long-term composition is Portainer for support infrastructure, one workspace owner, one agent control surface, one secret manager, and a simple artifact service. The main custom code should be task metadata, policy enforcement, and narrow adapters that fill measured gaps. The exact products remain replaceable because source, environment definitions, skills, and results are portable.

## Sources

All live sources below were checked September 10, 2026. Unless otherwise noted, the publisher does not provide a fixed publication date on the cited page. Product claims are tied to that observation date; versions and entitlements must be rechecked at implementation.

[^1]: unearth4334. [Portainer deployment skill, reviewed revision](https://gist.github.com/unearth4334/e40579c112a31d4c0a3ed275cbb911e7/7ad4fa91594a2ad99f7ff34946216be272a39308). Updated September 10, 2026. Retrieved through the GitHub Gist API; SKILL.md and configuration.md reviewed.
[^2]: Coder. [Documentation overview](https://coder.com/docs/index). v2.37 documentation observed.
[^3]: Coder. [Install with Docker](https://coder.com/docs/install/docker). Host requirements and PostgreSQL example.
[^4]: Coder. [Coder Agents](https://coder.com/docs/ai-coder/agents). Native control-plane agent architecture.
[^5]: Coder. [Plans and feature comparison](https://coder.com/pricing). Current Community/Premium agent limits and feature positioning.
[^6]: Coder. [External provisioners](https://coder.com/docs/admin/provisioners). Premium designation, topology, authentication, user-scoped provisioners.
[^7]: OpenHands. [Current repository README](https://github.com/OpenHands/OpenHands/blob/main/README.md). Agent Canvas launch modes and mount scope.
[^8]: OpenHands. [Backends](https://docs.openhands.dev/openhands/usage/agent-canvas/backends). Backend ownership and settings scope.
[^9]: OpenHands. [ACP agents](https://docs.openhands.dev/openhands/usage/agent-canvas/acp-agents). External CLI wrappers and credential delivery.
[^10]: OpenHands. [Self-hosting guide](https://github.com/OpenHands/OpenHands/blob/main/docs/SELF_HOSTING.md). Remote deployment and authentication.
[^11]: Loft Labs. [What is DevPod?](https://devpod.sh/docs/what-is-devpod). Client-only model, providers, credential synchronization.
[^12]: Docker. [Docker Sandboxes](https://docs.docker.com/ai/sandboxes/). MicroVMs and internal Docker daemons.
[^13]: Docker. [Install Docker Sandboxes](https://docs.docker.com/ai/sandboxes/install/). Linux/KVM requirements.
[^14]: Docker. [Run sandboxes in CI](https://docs.docker.com/ai/sandboxes/workflows/automation/). Noninteractive sign-in.
[^15]: Daytona. [Public core repository maintenance notice](https://github.com/daytonaio/daytona). Core moved private in June 2026; no further public-core updates.
[^16]: BloopAI. [Vibe Kanban repository](https://github.com/BloopAI/vibe-kanban). Workflow and sunsetting notice.
[^17]: Louis Knight-Webb, Bloop. [Goodbye bloop](https://www.vibekanban.com/blog/shutdown). April 10, 2026. Company shutdown, community continuation, and remote-service transition.
[^18]: Git project. [git-worktree](https://git-scm.com/docs/git-worktree). Multiple working trees and shared repository structure.
[^19]: Docker. [Docker Engine security](https://docs.docker.com/engine/security/). Namespaces, capabilities, and daemon attack surface.
[^20]: Docker. [Rootless mode](https://docs.docker.com/engine/security/rootless/). Daemon/runtime privilege model.
[^21]: gVisor project. [What is gVisor?](https://gvisor.dev/docs/). Userspace application-kernel isolation.
[^22]: Firecracker project. [Firecracker](https://firecracker-microvm.github.io/). KVM microVM architecture.
[^23]: Development Containers. [Development Container Specification](https://containers.dev/implementors/spec/). Portable environment metadata specification.
[^24]: Mosh project. [Mosh usage and technical design](https://mosh.org/). SSH bootstrap, UDP, and screen synchronization.
[^25]: OpenAI. [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode). JSONL, structured results, and automation authentication.
[^26]: OpenAI. [Codex App Server](https://learn.chatgpt.com/docs/app-server). Protocol, approvals, transport, and experimental status.
[^27]: Anthropic. [Run Claude Code programmatically](https://code.claude.com/docs/en/headless). JSON and stream-JSON interfaces.
[^28]: Agent Client Protocol contributors. [Protocol overview](https://agentclientprotocol.com/protocol/v1/overview). Agent/client message and session model.
[^29]: Portainer. [The Portainer Edge Agent](https://docs.portainer.io/advanced/edge-agent). Standard Edge polling and tunnel connectivity.
[^30]: Tailscale. [Subnet routers](https://tailscale.com/docs/features/subnet-routers). Private routing through an overlay.
[^31]: Infisical. [Self-hosting overview](https://infisical.com/docs/self-hosting/overview). Deployment components and edition considerations.
[^32]: Infisical. [Universal Auth](https://infisical.com/docs/documentation/platform/identities/universal-auth). Machine tokens, defaults, and paid trusted-IP controls.
[^33]: OpenBao. [AppRole auth method](https://openbao.org/docs/auth/approle/). Policy-bound machine authentication.
[^34]: OpenBao. [Seal/unseal](https://openbao.org/docs/concepts/seal/). Bootstrap and restart requirements.
[^35]: SOPS contributors. [SOPS](https://github.com/getsops/sops). Encrypted file management.
[^36]: Docker. [Manage secrets in Compose](https://docs.docker.com/compose/how-tos/use-secrets/). Per-service mounted secret delivery.
[^37]: Prometheus project. [Monitoring Docker metrics using cAdvisor](https://prometheus.io/docs/guides/cadvisor/). Container statistics integration.
[^38]: Coder. [Monitoring](https://coder.com/docs/admin/monitoring). Platform observability options.
