# Changelog

## 0.2.1
- Lighter webcams: players are freed as soon as a slide leaves, the next one pre-buffers only ~6 s ahead, and small screens (Echo Show 5) get a half-size player so YouTube sends a lighter stream.
- Low-power is never switched on automatically.
- Tip: on Echo Shows, turn off Kiosk Satellite's camera and motion sensor if you don't use them (the camera service alone used ~25% CPU on a Show 5).

## 0.2.0
- Low-power screen option per view (Echo Show 5, old tablets): no live webcams, no starfield clock, reloads every 2 h. Picking the Echo Show 5 size turns it on.

## 0.1.0
- First release: views, card settings and integrations in the sidebar admin; 25 cards.
