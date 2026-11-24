# ambient

Open **ambient** from the sidebar to set it up:

- **Views**: one per screen. Name, size, Immich album, rotation, and which cards it shows (⚙ for each card's settings).
  The kiosk URL for that screen is under the preview, e.g. `http://homeassistant.local:8099/?show=main`.
- **Integrations**: Home Assistant is connected automatically. Add Immich for photos; an OpenAI-compatible LLM
  (e.g. Ollama), TMDb and Plex are optional. The home location comes from Home Assistant unless you set one.

Screens use port **8099** (change it under the app's Network settings; the kiosk URL follows). The admin page is
only reachable from the sidebar unless you set an admin password under Integrations.

Settings live in the app's data folder and are included in Home Assistant backups.
