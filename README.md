# ambient

An Alexa-style idle screen for your home: photos from Immich between cards for weather, scores, news, markets,
live zoo and reef cams, the sky tonight, a Chumby-style clock or two, Zoltar's fortunes, and alerts that cut in
(severe weather, rain within the hour, breaking news, the song that just started). Built for Echo Shows running
[Kiosk Satellite](https://kiosksatellite.com), but any browser in kiosk mode works: tablets, old laptops, TVs.

Each **view** is one screen (`http://<host>:8099/?show=<view>`) with its own size, photo album and set of cards.
Everything is set up on the admin page; nothing to edit by hand.

## Install

### Home Assistant app (Home Assistant OS)
1. **Settings → Apps → App store → ⋮ → Repositories**, add `https://github.com/nawagner85/ambient`.
2. Install **ambient**, start it, and turn on **Show in sidebar**.
3. Open **ambient** from the sidebar. Home Assistant is connected automatically; add Immich (photos) and the
   optional services under **Integrations**, then set up your screens under **Views**.
4. Point each screen's browser at the kiosk URL shown under the preview, e.g. `http://homeassistant.local:8099/?show=main`.

### Docker (any amd64 or arm64 host)
```sh
docker run -d --name ambient --restart unless-stopped -p 8099:8099 -e TZ=America/Los_Angeles \
  -v $PWD/ambient-data:/data ghcr.io/nawagner85/ambient:latest
```
Open `http://<host>:8099/admin`, set an admin password, and paste a Home Assistant long-lived token under Integrations.
(`docker-compose.yml` in this repo does the same.)

## Integrations (all optional)

| | Unlocks | Where to get it |
|---|---|---|
| Home Assistant | weather, calendar, commute (Waze Travel Time sensors), now playing, planes, home location | automatic in the app; otherwise a long-lived token (HA → profile → Security) |
| Immich | photos (pick an album per view) | Immich → Account settings → API keys |
| LLM, any OpenAI-compatible API | Zoltar, breaking news, this day in history, is the mountain out | Ollama on your network (`http://<host>:11434/v1`, model with vision e.g. `gemma3:12b`), OpenRouter, … |
| TMDb | new movies / TV on your streaming services | themoviedb.org → Settings → API → read access token |
| Plex | recently added | your server URL + X-Plex-Token |

Cards whose service isn't set up stay out of the rotation. Everything else (scores, schedule, news, markets,
webcams, sky, air quality, weather and rain alerts, word of the day, clocks, Emi's screen clean) needs no keys.
Keys are kept in `/data/secrets.json` and never sent to a browser.

## Cards

Photos · Weather · Commute · Calendar · Scores · Upcoming games · Top news · Breaking news · Markets · New on Plex ·
New on streaming · Now playing · Webcams (zoos, aquariums, reefs; only where it's daytime) · Is the mountain out?
(Mount Rainier from the Space Needle cam, judged by the vision model) · Air quality (only when it's bad) · Sky ·
This day in history · Word of the day · Zoltar · Fun clocks · Screen clean · Weather alerts (US, NWS) · Rain soon ·
Planes overhead (needs `extras/planes_overhead.yaml` in HA) · Daily episode.

Every card has a ⚙ settings panel (teams, calendars, players, cams, when it plays, how long).

## Kiosk tips
- **Echo Show + Kiosk Satellite:** console `http://<show-ip>:2324` → Screensaver → Website, URL = the kiosk URL.
  Turn widgets and glance off. A night schedule back to the clock screensaver works well.
- **Tablets:** Fully Kiosk Browser, start URL = the kiosk URL, screen always on.
- The layout scales to any size; the view's size only sets the admin preview.

## Writing a card
A card is `app/cards/<type>.py` (`TTL`, `META` for its settings form, `fetch(ctx, opts)` → dict or `None`) +
`app/cards/<type>.js` (`export function render(data, env)` → element) + an entry in `app/config.json`.
See the docstring at the top of `app/server.py`.

## Releasing
Bump `version` in `ambient/config.yaml`, add a line to `ambient/CHANGELOG.md`, push a tag `v<version>`;
the workflow builds and pushes the multi-arch image, and Home Assistant offers the update.
