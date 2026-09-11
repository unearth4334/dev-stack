# Development workflow

Follow the [development conventions reviewed for this repository](https://gist.github.com/unearth4334/ce71aa978f5e0fa822544018be83ca49/00f4d32ddf00d07b9bc0cb39d67f85e6f899ae52).

For the pilot, [docs/pilot/index.html](docs/pilot/index.html) is the canonical implementation plan. Keep the public page, milestone and phase issue links in sync. Deliver one reviewable PR per phase issue, starting from current main after prerequisites merge. Do not mark a phase complete before its deployed acceptance criteria pass.

Run `python3 scripts/check_docs.py` for documentation changes and `python3 -m unittest discover -s scripts -p 'test_*.py'` for configuration tooling. Runtime phases add meaningful checks for their own acceptance criteria. Review the final diff and CI results; automatic Copilot review is configured through repository rules when available. Address valid comments and request re-review after substantive revisions. If review is unavailable, record the limitation rather than claiming a reviewed merge.

GitHub Pages publishes the static `docs/` source from `main`; it is public documentation only. Never commit live credentials, private topology, real task transcripts or private artifacts. Keep runtime configuration templates nonsecret and use the existing deployment skill for authorized, named Portainer stack changes.

Phase issues are staged with `stage:ready` or `stage:blocked` labels. These labels are a maintained snapshot, not an authorization mechanism. After merging a prerequisite, verify its exit gate, update the next issue, and advance its stage. The milestone remains the live inventory.
