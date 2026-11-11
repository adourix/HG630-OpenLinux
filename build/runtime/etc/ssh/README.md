# OEM Dropbear policy

The OEM daemon has no evidence of OpenSSH `sshd_config` support. Its command line
is assembled by `bin/openlinux-ssh-start`; this directory intentionally contains
no OpenSSH-style directives. The service is disabled by default. A supported
non-root account, verified LAN address, mounted devpts, target-side Dropbear key
generator, and operator-selected private-key storage are prerequisites.
