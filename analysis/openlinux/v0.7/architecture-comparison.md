# V0.7 deployment architecture comparison

| Approach | Feasibility | Evidence and risks | Missing evidence |
|---|---|---|---|
| A. OEM-supported RootFS component update | UNKNOWN/BLOCKED | Updater has distinct generic/area/config/bootloader APIs, but no section-to-MTD or RootFS-only branch is proven. Signature and outer integrity are unresolved. | Exact parser call graph, signed format, section selection, MTD map, recovery path |
| B. Replace RootFS while preserving OEM startup | PARTIALLY VERIFIED for offline assembly; UNKNOWN for deployment | Same-offset experimental assembly preserves kernel, metadata, and vendor files. RootFS startup still depends on the original shell/profile path and unknown kernel mount arguments. A bad image could prevent recovery. | Root MTD/mount protocol, BCJ support, OEM acceptance, UART/recovery |
| C. Additional userspace without replacing OEM RootFS | PARTIALLY VERIFIED as a staged model; UNKNOWN as persistent deployment | Existing RootFS already contains vendor services and an additive OpenLinux layer can be tested in user mode. Persistence, launch authority, writable storage, and safe service ordering on hardware are not established. | Hardware shell/access path, writable persistent location, non-interfering launch point |

## Recommendation

**RECOMMENDED: C for non-destructive discovery and userspace development.**
Use the preserved OEM RootFS and run OpenLinux components only through an
explicit, operator-controlled shell/test mechanism until hardware evidence is
available. This avoids changing the kernel, root filesystem, flash layout, or
OEM startup ordering.

**NOT RECOMMENDED for deployment yet: A or B.** Approach B is useful only as a
non-flashable laboratory artifact. Approach A cannot be implemented without
resolving OEM authentication and component-selection semantics.

OverlayFS is not assumed: no evidence in the available 2.6.30 kernel proves
`overlayfs` support, and no deployment design depends on it.
