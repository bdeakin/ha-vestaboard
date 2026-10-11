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

House event for October 11, 2026. Play the screens below in order on the Vestaboard, then start the sequence again every 15 minutes.

The board is 6 rows by 22 columns. Letters display in uppercase. Blue is `{67}`. White is `{69}`. A two-minute hold is `duration: 120`.

### 1. Announcement — 2 minutes

Today's event, with the date on its own line below the title, and a blue square in each corner.

```
{67}                    {67}

      DEMTOBERFEST

   OCTOBER 11TH, 2026

{67}                    {67}
```

### 2. Blue wave

A blue wave that starts in the top left and ends in the bottom right. The top left has turned white again as the middle turns blue. By the time the bottom right is blue, everything else is white.

Play it as one diagonal at a time. On step `d` (from 0 through 26), cell `(x, y)` is blue only when `x + y = d`. Every other cell is white.

- Step 0 is only the top-left cell, `(0, 0)`.
- A middle step (the diagonal through the center) is blue while the top left is already white.
- Step 26 is only the bottom-right cell, `(21, 5)`.

### 3. Re-elect — 2 minutes

"Re-elect Jon Crowley and Alyson Forbes", in an aesthetic layout. Keep the full wording, centered, with the names easy to read:

```
        RE-ELECT

      JON CROWLEY
   AND ALYSON FORBES
```

### 4. Pinball — 2 minutes

"More pinball in the basement" and, on a new line, "Watch your head going down the stairs".

```
    MORE PINBALL IN
     THE BASEMENT

    WATCH YOUR HEAD
GOING DOWN THE STAIRS
```

### 5. Instagram — 2 minutes

After the pinball message: "Follow @ahforward on Instagram".

```
   FOLLOW @AHFORWARD
     ON INSTAGRAM
```

### Repeat

Start this sequence every 15 minutes. Screens 1, 3, 4, and 5 each stay up for 2 minutes. The wave plays through once between the announcement and the re-elect screen.
