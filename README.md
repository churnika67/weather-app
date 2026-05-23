# Real-Time Weather App (Full-Stack)


## Project Title
Real-Time Weather App (Frontend + Backend)

## Project Summary
This is a complete full-stack weather application for the AI Engineer Intern technical assessment.
It uses live weather APIs (Open-Meteo), a React/Vite frontend, and a FastAPI backend with CRUD + database persistence + export endpoints.

## Features Implemented
- Weather search by city/town/zip/landmark/coordinates
- Browser geolocation weather lookup
- Current weather panel with location, temperature, condition, humidity, wind, and timestamp
- 5-day forecast visualization
- Weather icons/emoji indicators
- Frontend error handling for empty input, invalid location, API failure, and geolocation denial
- Backend location validation via geocoding API
- Date range validation for CRUD create/update
- Full CRUD on weather records
- SQLite persistence (`weather_records` table)
- Export saved records to JSON and CSV
- Map integration link (Google Maps)
- PM Accelerator informational section with candidate name

## Tech Stack
- Frontend: React + Vite + JavaScript + CSS
- Backend: FastAPI + SQLAlchemy + SQLite + Pydantic + httpx + python-dotenv + Uvicorn

## APIs Used
- Open-Meteo Geocoding API (location validation/resolution)
- Open-Meteo Forecast API (current weather and forecast)
- Google Maps link generation for location preview

## Clean Project Structure
```text
weather-app/
  backend/
    app/
      __init__.py
      main.py
      database.py
      models.py
      schemas.py
      crud.py
      weather_service.py
      export_service.py
    requirements.txt
    .env.example
  frontend/
    src/
      components/
      services/
      App.jsx
      main.jsx
      styles.css
    package.json
    vite.config.js
  README.md
  .gitignore
```

## Database Details
- Database: SQLite
- File: `backend/weather.db`
- Table: `weather_records`
- Main fields:
  - `id`
  - `location_input`
  - `resolved_location`
  - `latitude`
  - `longitude`
  - `start_date`
  - `end_date`
  - `weather_data`
  - `created_at`
  - `updated_at`

## Backend Run Commands
```bash
cd "/Users/churnika/Documents/New project/weather-app/backend"
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

## Frontend Run Commands
```bash
cd "/Users/churnika/Documents/New project/weather-app/frontend"
npm install
cp .env.example .env
echo 'VITE_API_BASE_URL=http://127.0.0.1:8001' > .env
npm run dev -- --host 127.0.0.1 --port 5173
```

## API Endpoint List (CRUD + Weather + Export)
- `GET /health`
- `GET /api/weather/current?location=`
- `GET /api/weather/forecast?location=`
- `POST /api/weather-records`
- `GET /api/weather-records`
- `GET /api/weather-records/{id}`
- `PUT /api/weather-records/{id}`
- `DELETE /api/weather-records/{id}`
- `GET /api/export/json`
- `GET /api/export/csv`

## Export Details
- `GET /api/export/json`: returns all saved weather records as JSON
- `GET /api/export/csv`: returns all saved weather records as CSV

## Testing Commands
Run these after backend is started on `8001`.

### Basic Health
```bash
curl http://127.0.0.1:8001/health
```

### Weather Endpoints
```bash
curl "http://127.0.0.1:8001/api/weather/current?location=buffalo"
curl "http://127.0.0.1:8001/api/weather/forecast?location=buffalo"
```

### CREATE
```bash
curl -X POST http://127.0.0.1:8001/api/weather-records \
  -H "Content-Type: application/json" \
  -d '{"location":"buffalo","start_date":"2026-05-22","end_date":"2026-05-26"}'
```

### READ ALL
```bash
curl http://127.0.0.1:8001/api/weather-records
```

### READ ONE
```bash
curl http://127.0.0.1:8001/api/weather-records/1
```

### UPDATE
```bash
curl -X PUT http://127.0.0.1:8001/api/weather-records/1 \
  -H "Content-Type: application/json" \
  -d '{"location":"new york","start_date":"2026-05-22","end_date":"2026-05-26"}'
```

### DELETE
```bash
curl -X DELETE http://127.0.0.1:8001/api/weather-records/1
```

### EXPORT
```bash
curl http://127.0.0.1:8001/api/export/json
curl http://127.0.0.1:8001/api/export/csv
```
