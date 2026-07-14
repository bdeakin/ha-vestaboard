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
