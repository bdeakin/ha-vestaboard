# Prompts

## Product intent

Personal fork (**Vestaboard-x**) to make Vestaboard VBML layouts authorable from Home Assistant Automations / Developer Tools without writing escaped JSON. Users should reference sensors directly and set alignment/formatting per board region. Do not include upstream sponsorship/referral sections in the README. Branding is a black V on a white background.

## Constraints honored

- Enhance `vestaboard.message` only (no custom panel/card in 0.3.0).
- HA Jinja belongs in prop `template` fields; component templates use VBML `{{prop}}` only.
- Preserve simple `message` + justify/align path and raw `vbml` escape hatch.
- Priority: `vbml` > `components`/`props` > `message`.

## Future prompts (not in this release)

- Visual board preview panel / Lovelace card.
- Live character-count validation against model width/height in the UI.
- Re-merge selected upstream releases on a regular cadence.
- Keep HACS installable without requiring GitHub Release zip assets unless/until a release pipeline is maintained on the fork.
