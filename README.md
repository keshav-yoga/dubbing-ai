# Dubbing AI

This project provides a FastAPI backend and a React frontend for building a simple dubbing application.

## Running with Docker

1. Install **Docker** and **Docker Compose**.
2. From the repository root run:
   ```bash
   docker compose up --build
   ```
3. Visit `http://localhost:5173` for the web UI and `http://localhost:8000` for the API.

## Running locally

You can also run the services without Docker.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\Scripts\activate
pip install -r requirements.txt pydantic-settings
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Make sure PostgreSQL is running and matches the credentials in `backend/.env`.
