# Version history

## 0.6.4

- Clarify that template sensor props stay dynamic at send time; panel Save/Send no longer persist preview snapshots into `vbml.props`, and panel Send always passes live prop bindings.
- Repair **Location Announcement** templates that were missing the `location` → `sensor.2026_leaderboard_location` prop binding.

## 0.6.3

- Display game scores as the full number with commas (e.g. `1,233,532,321`) instead of thousands/`K`.
- Split game boards so `TOP SCORE` and the score value sit on separate rows (full scores are too wide for one line).
- Ensure the rainbow **Location Announcement** template is always present first in Saved Templates (migrates legacy `high-scores-intro` id/name).

## 0.6.2

- Add seeded **Location Announcement** / High Scores Intro template: rainbow perimeter (welcome-board style) with `NOW DISPLAYING` / `HIGH SCORES FOR` / location from `sensor.2026_leaderboard_location`.

## 0.6.1

- Fix empty `template: ""` on entity-backed props (e.g. player name) skipping `entity_id` resolution, which left VBML `player` blank in the editor and on the board.
- README positions the fork around Stern Insider Connected pinball scores and credits Cursor.

## 0.6.0

- Add `vestaboard.send_template` action: pick a Vestaboard-x panel template from a dropdown and send it (props resolved live) without pasting VBML.
- Template select options refresh when templates are saved or deleted in the panel.

## 0.5.2

- Seed VBML templates for all Stern 2026 leaderboard games with their `top_player` / `top_score` entities (shared `player`/`score` props, corner-dot layout, per-game accent color).

## 0.5.1

- Elvira layout: black/red corner dots (no full color bars); title, player, then `TOP SCORE` + value on the bottom line.

## 0.5.0

- Vestaboard-x panel can save/load/delete multiple named VBML templates (persisted in Home Assistant storage).
- **Copy for automation** copies `vestaboard.message` YAML with live `props` + `vbml`.
- Message action merges structured `props` into `vbml.props` when both are provided.

## 0.4.5

- Elvira last line shows `TOP SCORE` next to the formatted score value.

## 0.4.4

- Elvira default VBML adds red (`{63}`) and black (`{70}`) color blocks: solid red header bar and alternating red/black accent above the score.

## 0.4.3

- Default VBML is a single-game layout for Elvira's House of Horrors: full title (wrapped), centered player, score on the last line (`#,##0K`).

## 0.4.2

- Default leaderboard VBML uses per-row columns: game left, player center, score right.
- Score props format as thousands with K (`#,##0K`, e.g. `1,234K`).
- Game labels: D&D, ELVIRA, GODZILLA, JAWS, X-MEN.

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
