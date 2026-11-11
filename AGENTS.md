# Durable agent instructions

- Treat this repository as a research and build workspace, not a flashing workflow.
- Preserve the original firmware, kernel, known-good RootFS artifacts, and incomplete run directories.
- Never flash a router or claim hardware validation from host-side build results.
- Keep `PROJECT_CONTEXT.md` current after meaningful work. Label claims VERIFIED, INFERRED, UNKNOWN, or BLOCKED.
- Run `python3 -m unittest discover -s tests -v` after code changes.
- Keep generated artifacts outside Git unless they are explicitly small, reproducible test fixtures.
- Before starting a RootFS build, check for an existing `tools/build_rootfs.py` process and use a unique output directory.
- Do not use destructive cleanup commands against broad paths; preserve prior build evidence.

