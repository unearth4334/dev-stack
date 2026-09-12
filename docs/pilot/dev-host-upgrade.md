# Dev-host upgrade plan: Kubuntu 25.10 to 26.04.1 LTS

Status: **plan prepared; execution not started**. The operator selected preparation of an in-place dev-host upgrade on September 11, 2026. A maintenance window, verified backup and recovery access must be established before execution. This is workstation maintenance supporting Phase 0, not pilot deployment.

## Observed readiness

| Item | September 11 observation | Maintenance implication |
|---|---|---|
| Release | Ubuntu 25.10 base with `kubuntu-desktop` installed | Preserve Kubuntu; review its desktop release notes |
| Stable upgrade offer | `do-release-upgrade --check-dist-upgrade-only` offers **26.04.1 LTS** | Use the normal upgrader, without `-d` |
| Package state | `dpkg --audit` and `apt-mark showhold` returned no entries | Repeat after refreshing package indexes; this is not dependency simulation |
| Disk | ext4 root, about 339 GiB available; separate 300 MiB EFI partition, about 289 MiB available | Space appears adequate; preserve EFI and partition metadata |
| Other storage | Separate NVMe with NTFS partitions; removable encrypted partitions present | Do not assume ownership, unlockability or backup suitability; identify disks before recovery work |
| NVIDIA | RTX 5070 Ti; `nvidia-driver-580-open` 580.159.03; DKMS installed for current and previous kernels | Verify a target-release driver/new-kernel combination before accepting reboot |
| Firmware | Secure Boot disabled, firmware reports Setup Mode | Record baseline; no Secure Boot change is part of this upgrade |
| Docker | Docker CE 29.2.1 and Docker Desktop 4.81.0 installed | Preserve Engine/Desktop data separately; confirm active contexts before checks |
| Repository mismatch | Docker and Microsoft product feeds use `plucky`, while Ubuntu feeds use `questing` | Review each vendor feed; do not globally substitute codenames |
| Existing Engine workloads | 4 running, 13 exited; 20 volume and 13 bind mount references across containers | Preserve stopped workload data too; references are not unique volumes |
| Restart policies | 9 unless-stopped, 1 always, 7 no | Restore the recorded desired state; do not start all containers indiscriminately |

The stable offer was checked without running the upgrade. No packages, repositories, boot settings or workloads were changed. Root authentication is available only through an operator's interactive terminal.

## Backup and recovery gate

Reserve a half-day maintenance window as an initial planning allowance, plus backup time; this is not a measured duration. Use the local keyboard/display and reliable power. Save all work and checkpoint agent sessions: tmux cannot preserve running processes across reboot.

Before the window, record privately:

- Backup destination, free capacity, encryption/recovery method, completion time and a successful sample restore. Prefer a recoverable system image plus application-consistent data backups. With about 1.4 TiB used, size the destination from the actual included data rather than assuming the pilot backup allowance is enough.
- Source-disk identifiers, partition table, EFI/boot recovery procedure and verified Kubuntu installation/recovery USB. Confirm the USB boots without installing or changing partitions. Preserve any other OS boot entries; NTFS partitions alone do not prove a particular dual-boot arrangement.
- Home directories, uncommitted/untracked project work, local-only Git branches, SSH identities/configuration, native vault data and its recovery mechanism, and private dev-stack configuration including the Portainer CA signing material. Encrypt these backups and keep them outside Git.
- Docker daemon configuration, exact context/endpoints, image identities, desired container states, Compose/project sources, bind mounts, named volumes and any data written into container writable layers. Raw inspection output may contain secrets: retain it only in encrypted/private storage.
- Docker Desktop's separate VM/data backup if used. Do not assume a host Engine volume backup covers Desktop. Stop Desktop before copying its disk, following [Docker's backup procedure](https://docs.docker.com/desktop/settings-and-maintenance/backup-and-restore/).

For databases, use an application-native consistent backup and verify restoration. For filesystem copies of Docker state, stop dependent writers and the appropriate daemon first; a live copy of `/var/lib/docker` is not a verified recovery image. Record exactly which services were stopped and how to restore their previous states. QNAP remains available as a control/recovery machine, but neither its storage capacity nor a workstation backup there is yet verified.

**Do not start the upgrade until a named backup destination, restore test, recovery medium and maintenance window are recorded.** If using file-level recovery instead of a full image, explicitly accept the longer reinstall-and-restore path. Existing OS packages cannot reliably be downgraded as a rollback.

## Execution sequence for the maintenance window

1. Refresh the private baseline and verify the backup gate. Review [Ubuntu's release upgrade procedure](https://ubuntu.com/server/docs/how-to/software/upgrade-your-release/), [26.04 changes since 25.10](https://documentation.ubuntu.com/release-notes/26.04/changes-since-previous-interim/) and [Kubuntu's release notes](https://www.kubuntu.org/news/kubuntu-26-04-release-notes/). Kubuntu notes possible theme/panel regressions; retain desktop configuration for recovery.
2. In a local operator terminal, run `sudo apt update`. Resolve repository errors before proceeding. If the EOL Ubuntu mirrors fail, use the documented [EOL upgrade procedure](https://help.ubuntu.com/community/EOLUpgrades) for that specific failure; preserve signatures and never change all suites to the target release manually.
3. Review `apt list --upgradable` and `apt-get --simulate dist-upgrade`. The existing Docker/Microsoft `plucky` feeds require explicit review: preserve their configuration and identify compatible feeds/packages before accepting dependency changes. Other configured vendor feeds include browser/editor, VPN and NVIDIA Container Toolkit sources; re-enable only those needed and supported on the target.
4. Once the proposed current-release updates are understood, run `sudo apt full-upgrade` interactively. Do not use automatic yes flags. Stop if the transaction unexpectedly removes the desktop, Docker, networking, boot or GPU packages. Reboot first if required, then repeat the baseline and backup changes made since capture.
5. Quiesce workloads for the release upgrade and confirm backups reflect their final writes. Run `sudo do-release-upgrade` from the local console. Confirm the target is 26.04 LTS and review its proposed removals, disabled third-party feeds, disk requirements and configuration-file diffs. Do not bypass the release offer with development flags or force an unattended frontend.
6. Allow the package transaction to finish. Avoid interrupting it or powering off. Inspect failures and preserve `/var/log/dist-upgrade` privately. Review any NVIDIA/DKMS errors before reboot; verify an installed target kernel has a suitable NVIDIA module, whether packaged prebuilt or DKMS-built. Keep the previous kernel until validation passes.
7. Reboot when the upgrader requests it. If package configuration failed, resolve it from the console before an elective reboot rather than guessing at driver removal/reinstallation commands.

Docker officially lists [Ubuntu 26.04 as supported](https://docs.docker.com/engine/install/ubuntu/). After the OS transition, configure the reviewed target-release Docker feed using the official instructions, preserving the existing data root and packaging family. Do not switch from Docker CE to `docker.io`, invoke an installation convenience script, or prune data to fix a packaging problem. Re-enable other third-party sources individually after checking vendor support; the existing NVIDIA Container Toolkit configuration is a separate item from the display driver.

## Acceptance before reopening development

Run these individually and retain sanitized outcomes:

```sh
cat /etc/os-release
uname -r
dpkg --audit
systemctl --failed
nvidia-smi
dkms status
docker context show
docker version
docker compose version
python3 scripts/dev_stack.py doctor --portainer
python3 scripts/check_docs.py
python3 -m unittest discover -s scripts -p 'test_*.py'
```

The project commands run from the dev-stack checkout. `doctor` may still report the two deliberately unconfigured permanent SSH aliases; distinguish those known pilot gaps from TLS/API regressions. Its endpoint check alone does not prove Edge Docker proxy access: repeat the authenticated read-only Docker version requests for both Portainer environments.

Also verify desktop login, displays, keyboard, audio as needed, Wi-Fi/private LAN and VPN if used, DNS, strict-host-key QNAP SSH, native-vault credential retrieval without printing secrets, and CLI login status. Compare the Docker data root, cgroup/storage configuration, mounts and each existing application's behavior against the private baseline. Restore only previously running services, in dependency order; check persistent data before allowing new writes. Test Docker Desktop separately if it is part of the operator's workflow. Test an existing GPU workload if one is relied upon; pilot GPU enablement remains deferred.

Acceptance requires working desktop/network/GPU, expected existing services and data, clean package configuration, and verified Portainer connectivity. Update the private profile's observed OS and the Phase 0 evidence only after these pass. Install tmux/mosh and resume pilot access work afterward. Defer old-kernel removal and Docker cleanup until the workstation has completed a representative working session successfully.

## Recovery decisions

- **No desktop but console works:** use a local TTY to inspect display-manager, kernel and NVIDIA errors. An older kernel is a diagnostic fallback, not a rollback of upgraded userspace.
- **Docker or an application fails:** keep the affected writers stopped; compare context, daemon configuration, mounts and vendor packages. Do not prune, recreate volumes or initialize a fresh database over retained data.
- **System cannot boot:** use the verified recovery USB and recorded disk/EFI information. Preserve the other disk and its boot entries. Restore the system image or reinstall onto the explicitly selected Linux target and restore tested backups.
- **Recovery exceeds the window:** keep pilot deployment paused and use QNAP/another device for coordination. Record the chosen restore path before making further destructive changes.

Open execution inputs: backup destination/capacity and restore proof; recovery USB/console confirmation; maintenance window; application-specific backup and stop/start inventory; final repository/package transaction review. These are maintenance readiness items, not a request to begin the upgrade now.
