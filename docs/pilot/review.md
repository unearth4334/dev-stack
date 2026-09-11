# Pilot planning review

## Scope and baseline

Reviewed the initial repository at `aea999548bbacc14836e1e23c313f0b6d16b575d`, the existing research/inventory/task example, and [development conventions revision 00f4d32ddf00d07b9bc0cb39d67f85e6f899ae52](https://gist.github.com/unearth4334/ce71aa978f5e0fa822544018be83ca49/00f4d32ddf00d07b9bc0cb39d67f85e6f899ae52).

This is an author design review, not proof of live runtime behavior or independent approval. GitHub PR review and CI evidence are recorded below once available.

## Findings addressed before publication

| Finding | Resolution |
|---|---|
| Broad roadmap could delay the pilot with secret-manager migration, GPU work and automated releases | Defined a bounded pilot; preserved the roadmap as history and assigned follow-up ownership |
| Platform selection followed implementation, risking discarded infrastructure | Moved a bounded selection trial before permanent workspace/controller implementation |
| Credentials appeared later than the first live agent run | Made protected bootstrap and scoped task delivery mandatory from initial execution |
| UI/backend selection could imply isolation or reliable approvals without evidence | Required separate task boundaries and per-CLI lifecycle/denial/follow-up tests |
| QNAP restart could cause duplicate writes or unsafe side-effect replay | Defined attempt ownership, observation before retry, bounded offline execution and cancellation confirmation |
| Public plan hosting could be confused with private artifact publication | Separated Pages from runtime control/results and prohibited private diagnostic data in public evidence |
| Agent completion could be confused with successful implementation | Separated agent exit, verification and review; included a failing-test acceptance scenario |
| Hardware capacity and product compatibility were still assumed | Made measured inventory and selected topology blockers for downstream phases |
| Staged work could appear ready before prerequisites land | Defined one issue/PR per phase, explicit merge gates and maintained stage labels |

## Verification

- `python3 scripts/check_docs.py`: local document links, HTML anchors, footnote references and illustrative JSON syntax pass.
- Author inspection: phase dependency order, required runtime coverage, rollout/rollback, secret boundaries, unexported-work preservation and observable acceptance criteria.
- Live QNAP/dev-host tests: not run; explicitly assigned to phase issues.
- GitHub Pages publication: pending merge and HTTP verification.
- [Plan PR #1](https://github.com/unearth4334/dev-stack/pull/1): documentation CI passed on the initial reviewed revision. Copilot reviewed the plan/workflow and reported two checker portability findings: implicit text encoding and a Python 3.9-only path method. Both are corrected; re-review and final CI are pending.
- Checker validation: UTF-8 documents pass; missing HTML anchors and symlink escapes outside the repository fail. These are manual fixture checks, not live runtime acceptance.

## Re-review follow-up

Copilot re-reviewed `edf252e` and identified a current-docs publication inconsistency: the original research named the actual Portainer management address while the new workflow prohibits private topology. The current research now uses a placeholder; the already-public initial Git history is unchanged. The review also requested including contributor-facing `.github` Markdown in link validation; the checker now includes it. Final CI and re-review remain pending.
