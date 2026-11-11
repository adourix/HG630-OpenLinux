# V1.7 account and authentication design

## Supplied account evidence

`passwd1` contains `root` with home `/bin` and shell `/bin/sh`; service identities (`web`, `upnp`, `cwmp`, etc.) point to `/bin/false`. `/etc/shadow` has an empty root password field. The image contains no `/etc/passwd`, `/etc/group`, or `/etc/shells`; `/etc/profile` copies `passwd1`/`group1` into tmpfs `/var/passwd` and `/var/group`. SSH strings include standard `getpwnam`/`getspnam` calls and vendor `/var/sshusers.cfg` policy. Which database Dropbear actually uses is unproven.

## Preferred account and blocker

The intended account is `openlinux`, shell `/bin/sh`, non-root, with a dedicated home and no password login. Current evidence does not establish a supported account database or user-provisioning extension. Creating a runtime `/etc/passwd`, editing Huawei `passwd1`/`shadow`/`group1`, or guessing the `sshusers.cfg` format could change vendor auth policy and might not affect the daemon's lookup. Therefore the package does not create accounts, edit OEM account files, or fall back to root. Start/provision require an already present unique non-root `openlinux` entry whose home and shell match configuration.

The physical OEM image cannot currently satisfy that prerequisite from known supported mechanisms. This is the exact account blocker. A future account overlay requires proof of uClibc account lookup paths and Dropbear's Huawei policy, plus a recovery-backed RootFS experiment.

## Authentication policy implemented in the host package

- `SSH_ENABLE=disabled` by default.
- Service invocation uses the OEM binary with `-c` (disable password auth), `-w` (deny root), `-j -k` (disable forwarding), `-F -E`, a single explicit `-p LAN_ADDRESS:PORT`, and an explicit ECDSA host key via `-r`.
- It never supplies `-B`, never uses root, never modifies OEM account files, and never enables firewall/WAN access.
- Provisioning accepts only `ecdsa-sha2-nistp256` public-key lines and creates a 256-bit ECDSA host key via target `dropbearkey`, outside the firmware, with restrictive modes. The required keygen program is absent in the supplied OEM RootFS, so provisioning reports a hard failure until the operator supplies a compatible, trusted generator through an authorized process.
- It refuses existing host key or authorized_keys files rather than overwriting user data.
- `openlinux-ssh-provision backup FILE` makes a mode-0600 copy without overwriting; `restore FILE` requires a mode-0600 ECDSA P-256 Dropbear key accepted by target `dropbearkey -y` and refuses an existing destination. Both paths require operator-selected storage outside firmware and are excluded from uninstall.

These rules are implementation policy, not proof that the customized daemon accepts the exact policy. No SSH authentication was attempted or simulated.
