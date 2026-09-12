# Host readiness and access handoff

This runbook prepares the remaining Phase 0 prerequisites. It does not authorize an OS upgrade, reboot, firewall change or permanent service account. Keep machine addresses, keys, raw inventories and backup locations in the private operator record.

## Supported dev-host maintenance

The current Ubuntu 25.10 installation is out of support. The operator's choice of an upgrade to Ubuntu 26.04 LTS or a different supported execution host is pending. The existing NVIDIA driver reports 580.159.03 with the expected GPU; preserve this as a compatibility baseline, not a target driver pin.

Before scheduling an in-place upgrade:

1. Confirm local console access and a maintenance window. Finish or checkpoint development sessions and inventory running containers, restart policies, bind mounts and named volumes privately. Record Docker/Compose, storage driver, cgroup mode, GPU driver and networking state.
2. Make and verify a recoverable backup of development files, SSH configuration, native-vault recovery material and application data. Quiesce databases for consistent backups. Record an actual restore destination and recovery method; a sibling directory on the same disk is insufficient for disk failure. Do not export secrets into the repository.
3. Check free space in the root and boot filesystems and review enabled third-party package repositories, Docker packaging and NVIDIA driver/DKMS status. Use the release upgrader's supported checks; do not rewrite distribution codenames manually or request a development release.
4. Follow [Ubuntu's release upgrade procedure](https://documentation.ubuntu.com/server/how-to/software/upgrade-your-release/) from the local console. Resolve the current release's package state before upgrading. An OS upgrade has no reliable automatic downgrade; rollback means restoring the verified backup or reinstalling and restoring data.
5. After reboot, verify networking, SSH host identity, Docker/Compose, all pre-existing workloads and NVIDIA operation. Repeat the Portainer local/Edge Docker checks, fixture baseline and memory/disk inventory before changing the recorded host baseline.

This project has not run the upgrade or scheduled a reboot. Interactive sudo authentication must happen in the operator's own terminal, without sharing a password with an agent.

## Terminal prerequisites

On the selected supported Ubuntu dev-host, install the terminal packages from the distribution repositories in the operator's terminal:

```sh
sudo apt update
sudo apt install tmux mosh
tmux -V
mosh-server --version
```

SSH is already listening on the current dev-host. Package availability alone does not establish phone access. Confirm the private phone route before opening the configured mosh UDP range, scope any firewall rule to that route, and leave public router forwarding out of this pilot. Home LAN access only covers the phone while on that LAN; cellular testing requires an established private VPN route.

## SSH identities and phase ownership

A disposable Phase 0 probe authenticated from QNAP to dev-host over the LAN using an independently pinned dev-host host key. Its temporary key was restricted to QNAP's source address and a fixed response command, with forwarding and PTY disabled. The key and authorization were removed immediately afterward. This proves network reachability and public-key authentication, not a deployed runner or permanent service identity.

Keep these access roles distinct:

| Role | Credential location | Capability | Delivery gate |
|---|---|---|---|
| Human recovery | Operator workstation or Termius vault | Deliberate host recovery and later task attachment | Phase 0 records the selected route; real phone actions are Phase 1 evidence |
| Controller requests | QNAP control service private storage | Validated JSON to a fixed trusted runner; no generic shell or forwarding | Phase 1 defines and tests the boundary; later provisioning installs it |
| Task Git access | Scoped per-project delivery | Read the approved fixture/project repository | Disposable auth proof, then scoped worker provisioning |

`access.dev_host_ssh` names the operator's workstation SSH configuration entry. `access.controller_worker_ssh` names an entry available to the QNAP controller runtime; it cannot be `localhost` when the controller runs on QNAP. Leave both unknown until their actual intended identities are configured and tested. Do not populate them with the removed probe identity just to make `doctor` pass.

QNAP has an SSH client, but `python3` was not found on its default SSH PATH during inventory. The controller deployment must explicitly provide its pinned Python runtime, SSH client and private known-hosts/key mounts. An alias in the QNAP administrator's home is not automatically available inside a controller container.

Phase 0 can establish authenticated route feasibility with a fixed disposable probe. Permanent request and attach commands depend on the Phase 1 contract. Do not require a fully implemented production runner to exit inventory, or grant a broad shell to avoid that dependency.

## Phone acceptance handoff

After packages and the intended human identity are ready, record the following on the actual phone:

1. Connect over the private route, start a disposable tmux session, detach, reconnect and attach to the same session.
2. Repeat over mosh; interrupt connectivity and restore it. Separately force-close Termius and reconnect to the retained tmux session.
3. With a private VPN route available, test Wi-Fi/cellular changes. Record this as untested when only LAN connectivity exists.
4. During Phase 1, repeat attachment, prompting, approvals, detach and cancellation for both isolated agent CLIs. Record that reattachment creates no second writer.

A terminal connectivity demonstration does not prove isolated agent credentials, task lifecycle enforcement or persistence through host reboot.
