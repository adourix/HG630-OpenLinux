# DSL support investigation

## Requirement

The target must retain the integrated DSL modem. Ethernet-WAN-only firmware is not an acceptable final result.

## Inventory required

1. DSL kernel module(s).
2. DSL firmware blob(s), version and expected path.
3. DSL control daemon(s).
4. Required vendor shared libraries.
5. Kernel symbols, ioctls and ABI assumptions.
6. Board-specific AFE, GPIO, LED and calibration settings.
7. WAN protocol integration (PPPoE and applicable DSL mode).

## Questions

- Is DSL support a kernel module or built into the kernel?
- What kernel vermagic does the module require?
- Are corresponding GPL kernel sources and config available?
- Are DSL binary firmware files redistributable?
- Can the stack be isolated, or is it tightly coupled to the vendor SDK?

## Risk

High. Preserving the original proprietary DSL stack may require the original kernel ABI and vendor userspace. An upstream kernel port is not assumed possible.

## Acceptance criteria

A successful test requires DSL training/synchronization, stable WAN session, bidirectional traffic, reconnect handling and sustained operation. A UI showing DSL enabled is insufficient.
