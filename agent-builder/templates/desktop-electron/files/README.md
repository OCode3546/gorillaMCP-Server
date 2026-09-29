# __APP_TITLE__

__APP_DESCRIPTION__

A cross-platform desktop app built with Electron and packaged with electron-builder.

## Develop

```bash
npm install
npm start
```

## Package

| Target | Command | Output |
| --- | --- | --- |
| Current OS | `npm run dist` | `release/` |
| Windows installer + portable `.exe` | `npm run dist:win` (on Windows) | `release/*.exe` |
| macOS `.dmg` | `npm run dist:mac` (on macOS) | `release/*.dmg` |
| Linux AppImage | `npm run dist:linux` | `release/*.AppImage` |

To build all three, push to GitHub and run the **Build executables** workflow (or push a `v*` tag). Builds are unsigned; add code-signing certificates before distributing widely.

## Code layout

- `main.js`: main process (windows, IPC handlers, OS access)
- `preload.js`: exposes a small, safe `window.api` to the UI
- `src/`: the UI (`index.html`, `renderer.js`, `styles.css`)
- `package.json` → `build`: app id, installer targets and icons
