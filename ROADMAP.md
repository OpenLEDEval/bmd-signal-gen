# bmd-signal-gen Roadmap

Derived from [SPEC.md](SPEC.md). Sections are in build-dependency order.
New work enters at the tail; completed work is deleted.

## Pattern library extraction §road:pattern-library

The pattern/chart modules moved to
[display-patterns](https://github.com/OpenDisplayEval/display-patterns)
v0.1.0 — extraction spine complete; PyPI publishing is deferred and
tracked in display-patterns' own roadmap (`§road:first-release` there).
bmd-signal-gen consumes the package from git and keeps the legacy
import paths alive as deprecation shims for one release cycle
(§spec:pattern-library).

### Remove the deprecation shims §road:remove-shims

Delete the `bmd_sg.image_generators` and `bmd_sg.charts` shim modules
after one release cycle (§spec:pattern-library).

**Verify:** the shim modules and their shim test are gone; nothing under
`bmd_sg/`, `examples/`, or `tests/` imports `bmd_sg.image_generators` or
`bmd_sg.charts`; the test suite passes.
