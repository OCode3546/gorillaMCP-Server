# __APP_TITLE__

__APP_DESCRIPTION__

A FastAPI service with typed models, validation and auto-generated OpenAPI docs.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn main:app --reload
# docs: http://127.0.0.1:8000/docs
```

## Endpoints

| Method | Path |
| --- | --- |
| GET | `/health` |
| GET / POST | `/items` |
| GET / PATCH / DELETE | `/items/{id}` |

## Test

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -t .
```

## Docker

```bash
docker build -t __APP_NAME__ . && docker run -p 8000:8000 __APP_NAME__
```

Storage is in memory (`Repository` in `main.py`); swap it for a database for persistence.
