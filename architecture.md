# Architecture

## Overview

`vestaboard` is a HACS Home Assistant integration that talks to Vestaboard displays over the Local API. This fork keeps the upstream device/client/coordinator stack and extends it for Stern Insider Connected pinball scoreboards: structured props/components, a Vestaboard-x template panel, and `send_template` automation actions — so layouts can be built from HA entities without authoring raw VBML JSON.

```text
Sidebar: Vestaboard-x panel
  ├─ named template library (HA Store)
  ├─ props builder
  └─ VBML modal (highlight + validate + drag/drop props)
        │  websocket: templates CRUD / validate_vbml / resolve_props
        │  refresh send_template action dropdown on save/delete
        ▼
Developer Tools / Automation UI
        │
        ├─ vestaboard.send_template  → load Store template by id → resolve props → VBML
        └─ vestaboard.message
              ├─ message (+ justify/align)     → single-component VBML
              ├─ props + components            → resolve HA → VBML props + styled regions
              └─ vbml (advanced)               → passthrough object
                    │
                    ▼
            VestaboardModel.parse_vbml (pyvbml)
                    │
                    ▼
            VestaboardCoordinator → Local API write + image entities
```

### `send_template`

Loads a named template from `vestaboard_templates` by `template_id` (or exact name), merges resolved props into the saved VBML, and reuses the same delivery path as `message` (transitions, duration, quiet hours). The automation UI select options are set via `async_set_service_schema` and refreshed after panel template save/delete.

## Message composition

| Source | When used | Notes |
| ------ | --------- | ----- |
| `vbml` | Highest priority | Raw VBML object (object selector) |
| `components` (+ optional `props`) | Preferred structured path | Flat UI fields normalized to VBML `style` |
| `message` | Fallback | Single region using top-level align/justify |

### Props resolution

Each prop requires a `name` and either:

1. Non-empty `template` — Home Assistant Jinja (`Template.async_render`), or
2. `entity_id` — entity state, optionally an `attribute`

Blank/whitespace `template` values are ignored so entity-backed props still resolve. Resolved values are stringified and injected as VBML `props` so component templates can use `{{name}}` without Jinja escaping conflicts.

### Component normalization

UI fields (`justify`, `align`, `height`, `width`, `x`, `y`) become a VBML `style` object. Absolute positioning requires both `x` and `y`.

## Unchanged upstream surfaces

- Config flow / DHCP discovery / Local API client
- Coordinator polling, quiet hours, temporary messages, transitions
- Image / sensor / binary_sensor / button platforms
- `pyvbml` board sizing forced to the discovered model dimensions

## Frontend panel

- Static assets: `custom_components/vestaboard/www/vestaboard-x-panel.js`
- Registered at `/vestaboard_static/` + sidebar path `vestaboard-x`
- Shared schema: `vbml_schema.py` used by services and websocket validation
- Default editor VBML: Elvira's House of Horrors (corner black/red dots, title, player, `TOP SCORE` + K-formatted score)
- Seeded templates also include a rainbow **High Scores Intro** (`rawCharacters` perimeter + location prop)
- Templates persisted via `helpers.storage` key `vestaboard_templates`

## Branding

- Display name: **Vestaboard-x** (`hacs.json`, `manifest.json`)
- Domain unchanged: `vestaboard`
- Local assets in `custom_components/vestaboard/brand/` (`icon.png`, `logo.png`, dark variants) take precedence over brands CDN on HA 2026.3+

## Distribution

- Personal HACS custom repository: `https://github.com/bdeakin/ha-vestaboard`
- HACS installs from the git repository (no `zip_release` / release zip required)
- Upstream remote for syncing: `natekspencer/ha-vestaboard`
