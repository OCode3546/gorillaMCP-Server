# __APP_TITLE__

__APP_DESCRIPTION__

A dependency-free HTML5 canvas game.

## Play

Open `index.html` in a browser, or serve the folder:

```bash
python3 -m http.server 8080
```

**Controls:** ← → or A / D to move, P or Esc to pause, Enter or Space to start. On touch screens, drag to move and tap to start.

## How the code is organised (`game.js`)

- `CONFIG`: tuning values (speeds, spawn rates, lives)
- `Player`, `Hazard`, `Pickup`: entities, each with `update(dt)` and `draw()`
- `update(dt)`: spawning, collisions, scoring and levelling
- `render()`: draws the current state (`menu`, `playing`, `paused`, `gameover`)
- `frame()`: the `requestAnimationFrame` loop with a clamped delta time

## Publish

Zip the folder and upload it to itch.io as an HTML game, or deploy it to any static host.
