# Version history

## 0.3.0

- Fork of natekspencer/ha-vestaboard focused on intuitive VBML authoring.
- Add structured `props` and `components` fields on `vestaboard.message` with entity/template selectors and per-component alignment, size, and absolute position.
- Resolve props from Home Assistant entities/attributes or Jinja templates before `pyvbml` parse.
- Keep raw `vbml` as an advanced object selector override.
- Point documentation / issue tracker at `bdeakin/ha-vestaboard`.

## Upstream baseline

- Inherited from upstream tag/commit corresponding to integration version 0.2.1 (Local API messaging, transitions, quiet hours, images).
