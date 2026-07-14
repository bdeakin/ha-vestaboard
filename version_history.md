# Version history

## 0.4.1

- Default Vestaboard-x panel props and VBML template to the Stern 2026 leaderboard sensors (location header + top-score lines; all game sensors available as drag-and-drop props).

## 0.4.0

- Add Vestaboard-x sidebar panel with a pop-out VBML editor modal.
- Color-coded JSON editing, live VBML validation (syntax/schema/parse), and drag-and-drop (or click) prop insertion into templates.
- WebSocket helpers: `vestaboard/list_devices`, `vestaboard/validate_vbml`, `vestaboard/resolve_props`.

## 0.3.1

- Rename HACS/integration display name to **Vestaboard-x**.
- Add local brand images (`brand/`: white background, black V) that override the upstream Vestaboard CDN logos in Home Assistant 2026.3+.
- Disable HACS `zip_release` so installs work from the GitHub repo without a prebuilt release asset (upstream-style release zips caused 404s on this fork).

## 0.3.0

- Fork of natekspencer/ha-vestaboard focused on intuitive VBML authoring.
- Add structured `props` and `components` fields on `vestaboard.message` with entity/template selectors and per-component alignment, size, and absolute position.
- Resolve props from Home Assistant entities/attributes or Jinja templates before `pyvbml` parse.
- Keep raw `vbml` as an advanced object selector override.
- Point documentation / issue tracker at `bdeakin/ha-vestaboard`.
- README clarifies personal-fork intent and drops support/referral sections.

## Upstream baseline

- Inherited from upstream tag/commit corresponding to integration version 0.2.1 (Local API messaging, transitions, quiet hours, images).
