<img alt="Vestaboard-x logo" src="images/vestaboard-x-logo.png" width="450px">

# Vestaboard-x for Home Assistant

[![Release](https://img.shields.io/github/v/release/bdeakin/ha-vestaboard?style=for-the-badge)](https://github.com/bdeakin/ha-vestaboard/releases)
[![HACS Badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

Home Assistant integration for Vestaboard messaging displays (**Vestaboard-x**).

This is a personal fork of [natekspencer/ha-vestaboard](https://github.com/natekspencer/ha-vestaboard), tailored specifically to help **display Stern Insider Connected pinball scores** on a Vestaboard — top player and top score for each Stern 2026 leaderboard game, driven by live Home Assistant sensors from your Stern Insider Connected setup.

Beyond the upstream Local API integration, this fork adds:

- An intuitive **Vestaboard-x** sidebar panel for authoring VBML (props from sensors/Jinja, syntax highlighting, validation, drag-and-drop placeholders)
- A **named template library** seeded for all eight Stern 2026 leaderboard games (corner-dot layouts with per-game accent colors)
- A **`vestaboard.send_template`** automation action with a dropdown of those saved templates — no copy-pasting VBML
- Structured `props` / `components` on `vestaboard.message` so layouts stay live with sensor values

Built with [Cursor](https://cursor.com) — thank you, Cursor.

## Local API Access Required

To use this integration, you **must first request access to Vestaboard's Local API**. This is required to enable local communication with your Vestaboard device.

### How to Request Access

1. Visit [https://www.vestaboard.com/local-api](https://www.vestaboard.com/local-api).
2. Fill out the request form to apply for a Local API enablement token.
3. Once approved, you will receive a token that you'll need to configure this integration.

**Note:** The integration will not function without this token. Be sure to complete this step before proceeding with setup.

## Installation

### HACS (Recommended)

1. In HACS → Integrations → ⋮ → **Custom repositories**, add `https://github.com/bdeakin/ha-vestaboard` as an **Integration**.
2. Search for `Vestaboard-x` and download this fork (HACS installs from the repository; no GitHub Release zip is required).
3. Restart Home Assistant.

You can also use the My Home Assistant badge once the repo is public:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bdeakin&repository=ha-vestaboard&category=integration)

### Manual

1. Download or clone this repository
2. Copy the `custom_components/vestaboard` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

> Manual installation will not provide automatic update notifications. HACS installation is recommended unless you have a specific need.

## Setup

Once installed, you can set up the integration by clicking on the following badge:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=vestaboard)

Alternatively:

1. Go to [Settings > Devices & services](https://my.home-assistant.io/redirect/integrations/)
2. In the bottom-right corner, select **Add integration**
3. Type `Vestaboard-x` and select the **Vestaboard-x** integration
4. Follow the instructions to add the integration to your Home Assistant

## Options

After this integration is set up, you can configure the color of your Vestaboard to adjust the image that is generated.

|          |                                       Black                                       |                                       White                                       |
| -------- | :-------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------: |
| Flagship | <img alt="Flagship Black Connected" src="images/flagship-black.png" width="100%"> | <img alt="Flagship White Connected" src="images/flagship-white.png" width="100%"> |
| Note     |     <img alt="Note Black Connected" src="images/note-black.png" width="70%">      |     <img alt="Note White Connected" src="images/note-white.png" width="70%">      |

## Vestaboard-x panel (VBML editor)

After installing and restarting, open **Vestaboard-x** in the Home Assistant sidebar.

- Save **multiple named templates**. Seeded first: rainbow **Location Announcement** (`NOW DISPLAYING HIGH SCORES FOR` + location), then all eight Stern 2026 leaderboard games — edit, automate, or save your own variants.
- Add **props** (entity ID and/or Jinja template)
- Open the **VBML editor** modal for syntax-colored JSON
- Drag (or click) props into the markup to insert `{{prop_name}}`
- Live validation: editor border turns green when VBML is valid, red when invalid (JSON + schema + optional device parse)
- Use **`vestaboard.send_template`** in automations to pick a saved template from a dropdown (no copy-paste). **Copy for automation** remains available for raw `vestaboard.message` YAML (`props` + `vbml`).
- Send the message to a selected board from the panel

## Actions

### `vestaboard.send_template` - Send a saved panel template

[![Open your Home Assistant instance and show your service developer tools with a specific action selected.](https://my.home-assistant.io/badges/developer_call_service.svg)](https://my.home-assistant.io/redirect/developer_call_service/?service=vestaboard.send_template)

Best path for top-score boards: save/edit the layout in the Vestaboard-x panel, then in an automation choose **Send saved template** and select the game from the **Template** dropdown. The service loads that template’s VBML and prop bindings, **re-reads the Home Assistant sensors at send time** (so new top players/scores appear automatically), and sends to the board. Values you may see inside the VBML editor `props` object are preview snapshots only.

| Field                | Name                 | Required | Description |
| -------------------- | -------------------- | -------- | ----------- |
| `device_id`          | Device               | Yes      | Vestaboard device(s) to send to. |
| `template_id`        | Template             | Yes      | Saved panel template (dropdown options refresh when templates change). |
| `strategy`           | Transition Strategy  | No       | Animation style. Leave blank to use the device default. |
| `step_size`          | Step Size            | No       | Columns/rows/bits to animate together. Range: 1–132. |
| `step_interval_ms`   | Step Interval        | No       | Delay between animation steps in ms. Range: 1–3000. |
| `duration`           | Duration             | No       | Temporary display duration in seconds (10–43200). |
| `bypass_quiet_hours` | Bypass Quiet Hours   | No       | If `true`, ignore quiet hours and send immediately. |

Example:

```yaml
action: vestaboard.send_template
data:
  device_id: YOUR_DEVICE_ID
  template_id: elvira-house-of-horrors   # value from the Template dropdown
```

### `vestaboard.message` - Send a message to one or more Vestaboards

[![Open your Home Assistant instance and show your service developer tools with a specific action selected.](https://my.home-assistant.io/badges/developer_call_service.svg)](https://my.home-assistant.io/redirect/developer_call_service/?service=vestaboard.message)

#### Fields

| Field                | Name                       | Required | Description |
| -------------------- | -------------------------- | -------- | ----------- |
| `device_id`          | Device                     | Yes      | The Vestaboard device(s) to send the message to. Supports multiple devices. |
| `message`            | Message                    | No       | Plain text message. Ignored when `components` or `vbml` are set. |
| `justify` / `align`  | Justify / Align            | No       | Horizontal / vertical alignment for a simple `message`. Default: `center`. |
| `props`              | Props                      | No       | Dynamic values from entities or Jinja templates. Used with `components`. |
| `components`         | Components                 | No       | Structured VBML regions (template + formatting). Preferred over raw `vbml`. |
| `vbml`               | Vestaboard Markup Language | No       | Advanced raw VBML object. Overrides `message` and `components`. |
| `strategy`           | Transition Strategy        | No       | Animation style when a new message is sent. See [Transition Strategy](#transition-strategy). |
| `step_size`          | Step Size                  | No       | Columns/rows/bits to animate together. Range: 1–132. |
| `step_interval_ms`   | Step Interval              | No       | Delay between animation steps in ms. Range: 1–3000. |
| `duration`           | Duration                   | No       | Temporary display duration in seconds (10–43200), then restore persistent message. |
| `bypass_quiet_hours` | Bypass Quiet Hours         | No       | If `true`, ignore quiet hours and send immediately. |

Message source priority: **`vbml` > `components` (+ optional `props`) > `message`**.

#### Structured components (recommended)

Use **Props** to pull live Home Assistant values, then reference them in component templates with VBML `{{prop_name}}` syntax. Put Home Assistant Jinja in prop `template` fields—not in component templates—so the two `{{ }}` languages do not collide.

Each component supports:

- `template` — text with `{{prop}}` placeholders
- `justify` — `left`, `right`, `center`, `justified`
- `align` — `top`, `bottom`, `center`, `justified`
- `height` / `width` — region size in rows/columns
- `x` / `y` — optional absolute position (both required together)

**Props** each have a `name`, plus either:

- `entity_id` (optional `attribute`), or
- `template` (Home Assistant Jinja; non-empty template wins over `entity_id`; blank template is ignored)

##### Example — single game (title / player / score)

```yaml
action: vestaboard.message
data:
  device_id: your_device_id
  props:
    - name: player
      entity_id: sensor.2026_leaderboard_elvira_s_house_of_horrors_top_player
    - name: score
      entity_id: sensor.2026_leaderboard_elvira_s_house_of_horrors_top_score
      template: >-
        {{ '{:,.0f}'.format(states('sensor.2026_leaderboard_elvira_s_house_of_horrors_top_score')
        | float(0)) }}
  components:
    # Corner accents: {70}=black, {63}=red (other games use different accent colors)
    - template: "{70}"
      height: 1
      width: 1
      x: 0
      y: 0
    - template: "{63}"
      height: 1
      width: 1
      x: 21
      y: 0
    - template: "ELVIRA'S HOUSE\nOF HORRORS"
      justify: center
      height: 2
      width: 22
      x: 0
      y: 1
    - template: "{{player}}"
      justify: center
      height: 1
      width: 22
      x: 0
      y: 3
    - template: "TOP SCORE"
      justify: center
      height: 1
      width: 22
      x: 0
      y: 4
    - template: "{{score}}"
      justify: center
      height: 1
      width: 20
      x: 1
      y: 5
    - template: "{63}"
      height: 1
      width: 1
      x: 0
      y: 5
    - template: "{70}"
      height: 1
      width: 1
      x: 21
      y: 5
```

The panel ships a rainbow **Location Announcement** (location from `sensor.2026_leaderboard_location`) plus saved templates for every Stern 2026 leaderboard game (D&D, Elvira, Godzilla, Jaws, John Wick, Jurassic Park, Pokemon, X-Men), each wired to its `top_player` / `top_score` sensors.

#### Transition Strategy

`strategy` accepts one of the following literal values. The "Display Name" column shows how each option is labeled in the UI, but is _not_ an acceptable value you can pass; only the `strategy` column values are valid.

| `strategy`\* (accepted value) | Display Name (UI only)                  |
| ----------------------------- | --------------------------------------- |
| `classic`                     | Classic (all-at-once)                   |
| `column`                      | Wave (left-to-right)                    |
| `reverse-column`              | Drift (right-to-left)                   |
| `edges-to-center`             | Curtain (outside-in, meeting in center) |
| `row`                         | Row (top-to-bottom)                     |
| `diagonal`                    | Diagonal (top-left to bottom-right)     |
| `random`\*\*                  | Random bits                             |

\* Applies to all strategies except `classic`: every bit animates on each transition, regardless of whether the character is changing.

\*\* The `random` strategy animates individual bits rather than full rows/columns, with a delay of several seconds (up to 10) between each step. A transition must fully complete before a new message can be displayed, so a small `step_size` means many more steps are needed to animate the full board. On a Flagship Vestaboard (132 bits), this can add up to several minutes before the board accepts a new message.

---

#### More examples

**Send a simple text message:**

```yaml
action: vestaboard.message
data:
  device_id: your_device_id
  message: "Hello, world!"
  justify: center
  align: center
```

**Send a temporary message with a transition animation:**

```yaml
action: vestaboard.message
data:
  device_id: your_device_id
  message: "Dinner is ready!"
  strategy: column
  step_interval_ms: 500
  duration: 120
```

**Advanced raw VBML** (escape hatch; prefer `components` / `props` above):

```yaml
action: vestaboard.message
data:
  device_id: your_device_id
  vbml:
    props:
      hours: "07"
      minutes: "35"
    components:
      - style:
          justify: center
          align: center
        template: "{{hours}}:{{minutes}}"
```

**Send to multiple devices, bypassing quiet hours:**

```yaml
action: vestaboard.message
data:
  device_id:
    - device_id_1
    - device_id_2
  message: "Good morning!"
  bypass_quiet_hours: true
```

---

#### Notes

- Provide one of `message`, `components`, or `vbml`.
- `step_size` and `step_interval_ms` only apply when a `strategy` is specified.
- `duration` is useful for transient alerts - the board will restore its last persistent message automatically after the duration expires.
