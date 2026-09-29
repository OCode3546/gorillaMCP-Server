# __APP_TITLE__

__APP_DESCRIPTION__

A full-stack Flask app: JSON REST API + SQLite + a vanilla JavaScript front end.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/flask --app app run --debug
# open http://127.0.0.1:5000
```

The SQLite database is created at `instance/app.db` (override with the `DATABASE` environment variable).

## API

| Method | Path | Body |
| --- | --- | --- |
| GET | `/api/items` | |
| POST | `/api/items` | `{"title": "..."}` |
| PATCH | `/api/items/<id>` | `{"title"?: "...", "done"?: true}` |
| DELETE | `/api/items/<id>` | |

## Test

```bash
.venv/bin/python -m unittest discover -s tests -t .
```

## Deploy

```bash
pip install gunicorn
gunicorn "app:create_app()" --bind 0.0.0.0:8000
```
