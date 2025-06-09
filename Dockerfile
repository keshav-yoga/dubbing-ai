| **Add the folder to `PYTHONPATH` (or make it the work dir)** | Copy the code the same way, but expose it to Python. | **Dockerfile** |
|   |   | ```dockerfile
FROM python:3.12-slim      # avoid pre-release 3.13 tag
WORKDIR /app
ENV PYTHONPATH="/app/backend:${PYTHONPATH}"
COPY backend ./backend
RUN pip install --no-cache-dir -r backend/requirements.txt
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker",
     "app.main:app", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "0"]
``` |

Either approach works; choose the one that matches your preference:

* **Quickest** – just change the Gunicorn import path in `docker-compose.yml`.
* **Cleanest** – keep the shorter `app.main:app` import, but make `/app/backend`
  visible through `WORKDIR` **or** `PYTHONPATH`.

---

### Step-by-step (one-line patch)

1. Open **docker-compose.yml**.
2. Find the backend service’s `command:` (or `CMD` in the Dockerfile).
3. Replace `app.main:app` with `backend.app.main:app`.
4. `docker compose build --no-cache && docker compose up`.

---

### Extra tips

* **Pin the Python image** – `python:3-slim` now resolves to 3.13-dev; many
  packages break on it. Use `python:3.12-slim` (or 3.11) until 3.13 is stable.
* If you prefer `uvicorn` directly, the same path rule applies:  
  `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`.
* When you reorganise files later, remember the import path must always match
  what’s on `PYTHONPATH`.

Give that a try and your container should start without the “No module named 'app'” error. If you hit the next issue (e.g. missing environment variables or model files) just let me know!
::contentReference[oaicite:1]{index=1}
