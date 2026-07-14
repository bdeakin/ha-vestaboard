# Prompts

## Product intent

Personal fork (**Vestaboard-x**) configured to display Stern Insider Connected pinball scores on a Vestaboard, and more generally to make VBML layouts authorable from Home Assistant without writing escaped JSON. Users should reference sensors directly and set alignment/formatting per board region. Do not include upstream sponsorship/referral sections in the README; do credit Cursor. Branding is a black V on a white background.

## Constraints honored

- Sidebar Vestaboard-x panel hosts the VBML modal (highlight, validate, drag/drop); action fields remain available for automations.
- HA Jinja belongs in prop `template` fields; component templates use VBML `{{prop}}` only.
- Preserve simple `message` + justify/align path and raw `vbml` escape hatch.
- Priority: `vbml` > `components`/`props` > `message`.
- Seed templates for each Stern 2026 game with its leaderboard sensors; corner-dot layout; `player`/`score` props; `TOP SCORE` label then full comma-formatted score on the next row.
- Seed a rainbow Location Announcement template first in Saved Templates (`NOW DISPLAYING` / `HIGH SCORES FOR` / location) matching the Vestaboard welcome-board perimeter style.
- Support multiple saved game templates and one-click copy of automation YAML (`props` + `vbml`).
- Prefer a dedicated `vestaboard.send_template` action with a dynamic Template dropdown sourced from the panel Store, so automations do not require pasting VBML.
- Prop resolution: non-empty Jinja `template` wins; blank `template` must fall through to `entity_id` (player name sensors).
- Templates bind sensors dynamically; never rely on static values baked into `vbml.props` — resolve at every send.

## Future prompts

- Visual board character preview inside the VBML modal.
- ha-entity-picker in the props form (instead of free-text entity IDs).
- Live character-count validation against model width/height in the UI.
- Re-merge selected upstream releases on a regular cadence.
- Keep HACS installable without requiring GitHub Release zip assets unless/until a release pipeline is maintained on the fork.
