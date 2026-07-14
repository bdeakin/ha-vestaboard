# Prompts

## Product intent

Personal fork (**Vestaboard-x**) to make Vestaboard VBML layouts authorable from Home Assistant Automations / Developer Tools without writing escaped JSON. Users should reference sensors directly and set alignment/formatting per board region. Do not include upstream sponsorship/referral sections in the README. Branding is a black V on a white background.

## Constraints honored

- Sidebar Vestaboard-x panel hosts the VBML modal (highlight, validate, drag/drop); action fields remain available for automations.
- HA Jinja belongs in prop `template` fields; component templates use VBML `{{prop}}` only.
- Preserve simple `message` + justify/align path and raw `vbml` escape hatch.
- Priority: `vbml` > `components`/`props` > `message`.
- Default props/VBML target Stern `sensor.2026_leaderboard_*` entities.

## Future prompts

- Visual board character preview inside the VBML modal.
- ha-entity-picker in the props form (instead of free-text entity IDs).
- Live character-count validation against model width/height in the UI.
- Re-merge selected upstream releases on a regular cadence.
- Keep HACS installable without requiring GitHub Release zip assets unless/until a release pipeline is maintained on the fork.
