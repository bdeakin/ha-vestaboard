# Development narrative

## Context

Started from [natekspencer/ha-vestaboard](https://github.com/natekspencer/ha-vestaboard). Creating multi-region VBML messages required hand-written JSON and awkward Jinja escaping when injecting Home Assistant sensor values. Plain `message` already exposed alignment controls; structured VBML did not.

## Goal

Make VBML composition feel like the rest of Home Assistant: pick entities, choose alignment/size per region, and let the integration assemble VBML.

## Approach

Kept the local API and `pyvbml` rendering path. Extended `vestaboard.message` with:

- `props` object list (entity / attribute / template)
- `components` object list (template + justify/align/size/position)
- Priority `vbml` > `components` > `message`, preserving an advanced escape hatch

HA Jinja is intentionally limited to prop templates so `{{ }}` never collides with VBML prop placeholders in component templates.

## Project layout

Fork lives at `/Users/bdeakin/Documents/Cursor/ha-vestaboard` as a sibling project to Stern Insider work. Remote `upstream` tracks the original author; `origin` is `bdeakin/ha-vestaboard`.

## README tone

Framed as a personal fork for improving intuitive VBML + sensor authoring. Removed upstream support/referral copy from the README.

## Branding

HACS/integration display name is **Vestaboard-x** (domain remains `vestaboard` for Local API compatibility). Ships `custom_components/vestaboard/brand/` icons and logos: black V on white.

## HACS install

Upstream uses `zip_release` + `vestaboard.zip` on GitHub Releases. This fork ships without that flag so HACS downloads from the repository directly; otherwise downloads 404 when no release asset exists.

## VBML modal panel

Native action selectors cannot host syntax highlighting or drag-and-drop, so a sidebar panel provides a pop-out VBML modal: JSON color coding, websocket-backed validation, and prop chips that insert `{{name}}` into templates. Defaults seed eight Stern 2026 game templates (corner dots, title, player, `TOP SCORE` + `#,##0K`) wired to each game's leaderboard sensors. The panel persists templates and can copy automation YAML with live props merged into VBML.
