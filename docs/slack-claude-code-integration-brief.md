# Two-Way Claude Code ↔ Slack Integration — Project Brief

## Goal

Run a local Claude Code CLI session that can be driven from Slack: send it a
message in a Slack channel, it picks the task up, works on it, and posts
results/questions back into the thread. Two-way — Claude should also be able
to pause and ask a clarifying question via Slack mid-task, not just report
results at the end.

## Why this needs to be containerized, not run on the host

A first attempt was made directly on the dev workstation (DESKTOP1) using
**SlackAgentBridge (SAB)**. It technically works, but running it on the host
was the wrong call:

- The bridge daemon has **full shell access** on whatever machine it runs on
  — anyone who can post in the Slack channel it creates can effectively
  drive a live terminal session there.
- Setup required scattering state across the host: `~/.local/bin/sab`,
  `~/.slack-agent-bridge/`, `~/.config/ccs/`, a modified `~/.bashrc`, edits
  to `~/.claude/settings.json` and `~/.claude/.mcp.json`, and (briefly) a
  changed ownership on `/usr/local/bin`. All of that had to be manually
  audited and undone afterwards.
- Credentials (`SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_TEAM_ID`) are
  read from plain `process.env` with no `.env` file support built in —
  fine in a container with a scoped `.env`, messy to manage safely in a
  shared shell profile on a real dev machine.

**Conclusion:** this belongs in a container with its own filesystem, its own
network egress, and secrets injected only at the container boundary —
never touching the host's `~/.claude`, `~/.local/bin`, or `~/.bashrc`.

## Options evaluated

| Approach | What it is | Verdict |
|---|---|---|
| **Official Slack MCP plugin** (`/plugin install slack`) | Anthropic's own plugin — Claude reads channels/threads/search via MCP | One-way (data source), not a remote-control bridge. Good building block, not a full solution alone. |
| **slackcli** | Third-party CLI for scripted Slack read/write | Just a Slack client library substitute — no bridging to a Claude session by itself. |
| **SlackAgentBridge (SAB)** | Two-way bridge: per-session private Slack channel, `/sab-*` slash commands, tmux-backed sessions | Full-featured but **macOS-oriented installer** (Homebrew paths, `~/Library/LaunchAgents`), no Linux-specific packaging, plain-env-var secrets. Needs manual patching to install cleanly on Linux. |
| **claude-slack-bridge** | Lighter two-way bridge, single-machine, Socket Mode | Simpler surface area than SAB — worth evaluating as an alternative if SAB's Linux quirks are too much friction. |
| **Official "Claude Code in Slack" cloud app** | Anthropic-hosted, tags `@Claude` in a thread, runs against a GitHub repo in the cloud | No local machine involved at all — doesn't run *your* local session/tools, so it doesn't meet "drive my local CLI session" if that's a hard requirement. Worth reconsidering if local execution isn't actually required. |

## Recommended path forward

1. **Decide if local execution is actually required.** If the real goal is
   "trigger Claude Code work from Slack" rather than specifically "control
   *this* machine's terminal," the official cloud-hosted Claude Code in
   Slack integration sidesteps this entire containerization problem. Worth
   a deliberate yes/no before building infrastructure.

2. **If local/self-hosted is required, containerize the bridge:**
   - Base image: Node + tmux + git + jq + the `claude` CLI.
   - Claude auth: pass in via `CLAUDE_CODE_OAUTH_TOKEN` env var rather than
     mounting `~/.claude/.credentials.json`, to avoid exposing the host
     credential file inside the container.
   - Slack secrets (`SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_TEAM_ID`):
     supplied via a `.env` file consumed by `docker-compose.yml`, never
     baked into the image.
   - Persistent state (SAB's `~/.config/ccs` equivalent) on a named Docker
     volume, so session history / `/sab-claim` binding survives restarts.
   - Project directories bind-mounted explicitly and only as needed —
     the container should not have blanket access to the whole home
     directory the way SAB does natively on a host.
   - Network egress scoped to what Slack's Socket Mode actually needs
     (outbound only, no inbound port required — Socket Mode avoids needing
     a public URL).

3. **Re-evaluate SAB vs. claude-slack-bridge inside the container**, now
   that Linux path issues (`/opt/homebrew/bin` defaults, `BIN_DIR` etc.)
   are moot in a Linux-based image regardless of which tool is chosen.

4. **Access control**: before wiring this up for real use, decide who can
   post in the bridge's Slack channel and treat that as equivalent to
   "who has a shell on this box" — restrict the channel accordingly
   (private channel, explicit member list) rather than relying on
   workspace-wide trust.

## Open questions to resolve in dev-stack

- Local execution vs. cloud-hosted Claude Code in Slack — pick one.
- SAB vs. claude-slack-bridge, once running in a container.
- Where container secrets live relative to the rest of the dev-stack's
  existing `.env`/secrets conventions.
- Whether this container should be always-on (daemon) or spun up on
  demand.
