# Prompts

## Product intent

Personal fork (**Vestaboard-x**) configured to display Stern Insider Connected pinball scores on a Vestaboard, and more generally to make VBML layouts authorable from Home Assistant without writing escaped JSON. Users should reference sensors directly and set alignment/formatting per board region. Do not include upstream sponsorship/referral sections in the README; do credit Cursor. Branding is a black V on a white background.

## Constraints honored

- Sidebar Vestaboard-x panel hosts the VBML modal (highlight, validate, drag/drop); action fields remain available for automations.
- HA Jinja belongs in prop `template` fields; component templates use VBML `{{prop}}` only.
- Preserve simple `message` + justify/align path and raw `vbml` escape hatch.
- Priority: `vbml` > `components`/`props` > `message`.
- Seed templates for each Stern 2026 game with its leaderboard sensors; unique per-game score layouts (game name, player, score only — no TOP SCORE labels); compact K/M scores when wide.
- Seed a rainbow Location Announcement template first in Saved Templates (`NOW DISPLAYING` / `HIGH SCORES FOR` / location) matching the Vestaboard welcome-board perimeter style.
- Each game has a dense multi-color pixel-art intro (≥80% board, TL→BR scan reveal) before the score board on `send_template`.
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

## Demtoberfest 2026

House event for October 11, 2026. This is the **Demtoberfest 2026** display sequence in the Vestaboard-x panel (the other sequence is **Pinball Scores**). Play the screens below in order on the Vestaboard, then start the sequence again every 15 minutes. Do not put back the screen that was showing before the sequence; the last screen stays up.

The board is 6 rows by 22 columns. Letters display in uppercase. This is a white-background Vestaboard: blue is `{67}` and the white flap is `{70}`. Each message screen holds for 15 seconds (`duration: 15`).

### 1. Announcement — 15 seconds

Today's event, with the date on its own line below the title, and a blue square in each corner.

```
{67}                    {67}

      DEMTOBERFEST

   OCTOBER 11TH, 2026

{67}                    {67}
```

### 2. Blue wave

The board starts on the white chip (character code 70), sweeps to blue (67), then sweeps back to white, as one fluid transition each way. The exact pattern is open; the board's own transitions are preferred over many small messages. It is three Local API messages: all white with no strategy (only non-white tiles move), then all blue, then all white, each with `strategy: column`, `step_size: 1`, `step_interval_ms: 200`. Each sweep waits about 14 seconds so it lands before the next message. With a strategy every tile spins through its reel, so letters and colors flicker past during both sweeps.

### 3. Re-elect — 15 seconds

"Re-elect Jon Crowley and Alyson Forbes", in an aesthetic layout. Keep the full wording, centered, with the names easy to read:

```
        RE-ELECT

      JON CROWLEY
   AND ALYSON FORBES
```

### 4. Pinball — 15 seconds

"More pinball in the basement" and, on a new line, "Watch your head going down the stairs".

```
    MORE PINBALL IN
     THE BASEMENT

    WATCH YOUR HEAD
GOING DOWN THE STAIRS
```

### 5. Instagram — 15 seconds

After the pinball message: "Follow @ahforward on Instagram".

```
   FOLLOW @AHFORWARD
     ON INSTAGRAM
```

### Repeat

Start this sequence every 15 minutes. Screens 1, 3, 4, and 5 each stay up for 15 seconds. The wave plays through once between the announcement and the re-elect screen: white, then blue radiating from the top left to the bottom right, then white following until the board is white again.
