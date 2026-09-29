# __APP_TITLE__

__APP_DESCRIPTION__

A React single-page app built with Vite.

## Develop

```bash
npm install
npm run dev
```

## Build

```bash
npm run build     # outputs dist/
npm run preview   # serve the production build locally
```

Deploy `dist/` to any static host (Vercel, Netlify, Cloudflare Pages, GitHub Pages).

## Code layout

- `src/App.jsx`: top-level state and layout
- `src/components/`: UI components
- `src/useLocalStorage.js`: persisted-state hook
- `src/index.css`: styles; colour tokens in `:root` with a dark-mode override
