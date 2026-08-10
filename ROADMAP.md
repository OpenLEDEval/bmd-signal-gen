# bmd-signal-gen Roadmap

Derived from [SPEC.md](SPEC.md). Sections are in build-dependency order.
New work enters at the tail; completed work is deleted.

## Pattern library extraction §road:pattern-library

`bmd_sg.image_generators` and `bmd_sg.charts` import nothing from the
device layer; they are a generic pattern/chart library carried inside
a DeckLink tool. Extract them to OpenLEDEval/display-patterns — a
numpy-only core with `charts` and `io` extras — so other tools consume
them without DeckLink baggage, then consume the package here. The
OpenLEDEval/display-patterns repository exists (LICENSE only); it
carries its own SPEC/ROADMAP.

### Spec the display-patterns split §road:spec-display-patterns

Add a SPEC.md section (`§spec:pattern-library`) recording the
extraction: what moves (`bmd_sg/image_generators/`,
`bmd_sg/charts/`), the package shape (numpy core accepting an array
namespace, `charts` and `io` extras), why the API stays value-space
agnostic (measurement drives exact integer code values), the
frame-indexed rendering signature (a pattern is a pure function of
geometry, parameters, and frame index; stills ignore the index;
playback and timing stay with consumers), the temporal-alignment
counter panel (encode + decode, ported from backlit_molecule's probe
math) as a catalog entry, and the deprecation-shim plan.
§spec:decklink-backend is the precedent.

### Extract and publish display-patterns §road:extract-display-patterns

Move the modules and their tests verbatim into the new repository,
package the core + extras split, and publish 0.1 to PyPI
(`§spec:pattern-library`, added by §road:spec-display-patterns).
Depends on §road:spec-display-patterns. Publishing needs PyPI
trusted publishing configured on the new repository (human step).

### Consume display-patterns §road:consume-display-patterns

Depend on display-patterns, point CLI and API imports at it, and
reduce `bmd_sg.image_generators` and `bmd_sg.charts` to
deprecation-warning re-export shims for one release cycle
(`§spec:pattern-library`). Depends on §road:extract-display-patterns.

**Verify:** From a fresh clone, `uv sync` succeeds; `uv run
bmd-signal-gen --mock-device checkerboard2` and `gen-chart` produce
output identical to pre-split; `import
bmd_sg.image_generators.checkerboard` still works and emits a
deprecation warning; the test suite passes.
