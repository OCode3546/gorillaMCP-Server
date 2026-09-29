# __APP_TITLE__

__APP_DESCRIPTION__

A dependency-free web app: plain HTML, CSS and JavaScript.

## Run

Open `index.html` in a browser, or serve the folder:

```bash
python3 -m http.server 8080
# then open http://localhost:8080
```

## Structure

| File | Purpose |
| --- | --- |
| `index.html` | Page markup |
| `styles.css` | Styles; colour tokens in `:root` with a dark-mode override |
| `app.js` | State, persistence (`localStorage`) and rendering |

## Deploy

Upload the folder to any static host: GitHub Pages, Netlify, Cloudflare Pages, S3.
