import json
from datetime import date, timedelta
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.openapi.docs import get_redoc_html
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from .database import Base, engine, get_db
from . import crud, schemas
from .export_service import records_to_csv, records_to_json
from .weather_service import (
    fetch_current_weather,
    fetch_default_5_day_forecast,
    fetch_forecast,
    resolve_location,
)

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Atmosphere API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)

allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
allowed_origins = [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return HTMLResponse(
        """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Atmosphere API</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Sora:wght@600;700&display=swap" rel="stylesheet">
    <style>
      body {
        margin: 0;
        font-family: "Plus Jakarta Sans", sans-serif;
        color: #0f1d2e;
        background:
          linear-gradient(to bottom, #f8fbff 0 220px, transparent 220px),
          repeating-linear-gradient(90deg, rgba(11, 92, 171, 0.04) 0 1px, transparent 1px 110px),
          #f4f6f8;
      }
      .wrap {
        width: min(1000px, 92vw);
        margin: 44px auto;
      }
      .card {
        border: 1px solid #d9e1ea;
        background: #ffffff;
        border-radius: 14px;
        padding: 28px;
        box-shadow: 0 16px 36px rgba(13, 33, 58, 0.08);
      }
      h1 {
        margin: 0;
        font-family: "Sora", sans-serif;
        font-size: clamp(1.8rem, 5vw, 3rem);
      }
      p { color: #4d5d73; line-height: 1.6; }
      .links { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 14px; }
      a {
        text-decoration: none;
        color: white;
        background: #0b5cab;
        border-radius: 12px;
        padding: 10px 14px;
        font-weight: 700;
      }
      a.alt { background: #0f766e; }
    </style>
  </head>
  <body>
    <main class="wrap">
      <section class="card">
        <h1>Atmosphere API</h1>
        <p>Real-time weather data platform with geocoding validation, forecast retrieval, CRUD persistence, and export endpoints.</p>
        <div class="links">
          <a href="/docs">Open API Console</a>
          <a class="alt" href="/health">Health Check</a>
        </div>
      </section>
    </main>
  </body>
</html>
"""
    )


@app.get("/docs", include_in_schema=False)
def custom_swagger_ui():
    return HTMLResponse(
        f"""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Atmosphere</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
    <script type="module" src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"></script>
    <style>
      :root {{
        --bg: #edf2fa;
        --panel: #ffffff;
        --panel-2: #fbfdff;
        --line: #dfe7f4;
        --text: #1a2d4a;
        --muted: #647d9f;
        --accent: #216fe9;
      }}
      * {{ box-sizing: border-box; }}
      html, body {{ margin: 0; font-family: Inter, sans-serif; background: var(--bg); color: var(--text); }}
      .wrap {{ padding: 1rem; }}
      .app {{
        max-width: 1750px;
        margin: 0 auto;
        border: 1px solid #d8e2f1;
        border-radius: 22px;
        background: #f4f8fe;
        overflow: hidden;
      }}
      .top {{
        padding: .95rem 1.15rem;
        background: linear-gradient(135deg, #041b4a, #0a2c6c);
        display: flex;
        justify-content: space-between;
        align-items: center;
      }}
      .logo {{ font-size: 2rem; font-weight: 800; color: #fff; }}
      .tabs {{ display:flex; gap:1rem; }}
      .tabs span {{ color:#b8caeb; font-weight:700; }}
      .tabs .active {{ color:#fff; border-bottom:2px solid #57adff; padding-bottom:.2rem; }}
      .badge {{ border:1px solid #3f6fb5; border-radius:999px; padding:.45rem .8rem; color:#fff; font-weight:700; background:rgba(255,255,255,.12); }}
      .search {{
        background:#fff;
        padding:.85rem 1rem;
        border-bottom:1px solid #dfe8f5;
        color:#5f7395;
        font-weight:600;
      }}
      .layout {{ display: grid; grid-template-columns: 340px 1fr; gap: 12px; padding: 12px; }}
      .catalog {{ border: 1px solid var(--line); border-radius: 14px; background: var(--panel); padding: 12px; }}
      .catalog h2 {{ margin: 0; font-size: 1rem; color: #17375f; }}
      .list {{ margin-top: 10px; display: grid; gap: 8px; }}
      .item {{
        border: 1px solid var(--line); border-radius: 10px; padding: 8px 10px; background: var(--panel-2);
        display: grid; grid-template-columns: 56px 1fr; gap: 8px; font-size: .82rem;
      }}
      .verb {{ font-weight: 800; color: #216fe9; }}
      .surface {{ border: 1px solid var(--line); border-radius: 14px; overflow: hidden; background: var(--panel); }}
      .surface-head {{ padding: 12px; border-bottom: 1px solid var(--line); display: flex; justify-content: space-between; gap: 10px; align-items: center; }}
      .surface-head h2 {{ margin: 0; font-size: 1.03rem; color: #17375f; }}
      .surface-head p {{ margin: 3px 0 0; color: var(--muted); font-size: .86rem; }}
      .cta {{ color: white; text-decoration: none; background: linear-gradient(135deg, #4ea5ff, #2f83ff); border-radius: 8px; padding: 8px 10px; font-size: .82rem; font-weight: 700; }}
      rapi-doc {{ --bg: #ffffff; --fg: #1a2d4a; --nav-bg-color: #f6f9ff; --nav-text-color: #24416a; min-height: calc(100vh - 170px); }}
      @media (max-width: 980px) {{
        .layout {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <div class="wrap">
    <div class="app">
      <header class="top">
        <div class="logo">☁ Atmosphere</div>
        <div class="tabs"><span class="active">Weather</span><span>Maps</span><span>Alerts</span><span>News</span><span>Travel</span></div>
        <span class="badge">Developer Portal</span>
      </header>
      <div class="search">Interactive API Console for current weather, forecast, CRUD records, and exports</div>
      <div class="layout">
        <aside class="catalog">
          <h2>Endpoint Catalog</h2>
          <div class="list">
            <div class="item"><span class="verb">GET</span><span>/api/weather/current</span></div>
            <div class="item"><span class="verb">GET</span><span>/api/weather/forecast</span></div>
            <div class="item"><span class="verb">POST</span><span>/api/weather-records</span></div>
            <div class="item"><span class="verb">GET</span><span>/api/weather-records</span></div>
            <div class="item"><span class="verb">PUT</span><span>/api/weather-records/{"{id}"}</span></div>
            <div class="item"><span class="verb">DELETE</span><span>/api/weather-records/{"{id}"}</span></div>
            <div class="item"><span class="verb">GET</span><span>/api/export/json</span></div>
            <div class="item"><span class="verb">GET</span><span>/api/export/csv</span></div>
          </div>
        </aside>
        <section class="surface">
          <div class="surface-head">
            <div>
              <h2>Interactive Console</h2>
              <p>Execute requests, inspect schemas, and validate responses live.</p>
            </div>
            <a class="cta" href="/health">Health Check</a>
          </div>
          <rapi-doc
            spec-url="{app.openapi_url}"
            render-style="focused"
            theme="light"
            allow-authentication="false"
            allow-server-selection="false"
            allow-try="true"
            show-method-in-nav-bar="as-colored-block"
            nav-bg-color="#f6f9ff"
            primary-color="#2f84ff"
            regular-font="Plus Jakarta Sans"
            heading-font="Sora"
            sort-endpoints-by="path"
            show-header="false"
            schema-style="table"
            schema-expand-level="2"
            persist-auth="true"
            default-api-server="http://127.0.0.1:8001"
          ></rapi-doc>
        </section>
      </div>
    </div>
    </div>
  </body>
</html>
"""
    )


@app.get("/redoc", include_in_schema=False)
def custom_redoc_ui():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title="Atmosphere API ReDoc",
    )


@app.get("/api/weather/current", response_model=schemas.WeatherCurrentResponse)
async def get_current_weather(location: str = Query(..., min_length=1)):
    cleaned = location.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Location cannot be empty")

    resolved = await resolve_location(cleaned)
    current_weather = await fetch_current_weather(resolved["latitude"], resolved["longitude"])

    return {
        "location_input": cleaned,
        "resolved_location": resolved["resolved_location"],
        "latitude": resolved["latitude"],
        "longitude": resolved["longitude"],
        "current_weather": current_weather,
    }


@app.get("/api/weather/forecast", response_model=schemas.WeatherForecastResponse)
async def get_forecast_weather(
    location: str = Query(..., min_length=1),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    cleaned = location.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Location cannot be empty")

    resolved = await resolve_location(cleaned)

    if start_date is None or end_date is None:
        forecast = await fetch_default_5_day_forecast(resolved["latitude"], resolved["longitude"])
    else:
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date cannot be after end date")
        forecast = await fetch_forecast(resolved["latitude"], resolved["longitude"], start_date, end_date)

    return {
        "location_input": cleaned,
        "resolved_location": resolved["resolved_location"],
        "latitude": resolved["latitude"],
        "longitude": resolved["longitude"],
        "forecast": forecast,
    }


@app.post("/api/weather-records", response_model=schemas.WeatherRecordResponse)
async def create_weather_record(payload: schemas.WeatherRecordCreate, db: Session = Depends(get_db)):
    resolved = await resolve_location(payload.location)
    forecast = await fetch_forecast(
        resolved["latitude"],
        resolved["longitude"],
        payload.start_date,
        payload.end_date,
    )

    record = crud.create_record(
        db=db,
        location_input=payload.location,
        resolved_location=resolved["resolved_location"],
        latitude=resolved["latitude"],
        longitude=resolved["longitude"],
        start_date=payload.start_date,
        end_date=payload.end_date,
        weather_data=forecast,
    )

    output = schemas.WeatherRecordResponse.model_validate(record)
    output.weather_data = json.loads(record.weather_data)
    return output


@app.get("/api/weather-records", response_model=list[schemas.WeatherRecordResponse])
def list_weather_records(db: Session = Depends(get_db)):
    records = crud.get_records(db)
    output = []
    for record in records:
        item = schemas.WeatherRecordResponse.model_validate(record)
        item.weather_data = json.loads(record.weather_data)
        output.append(item)
    return output


@app.get("/api/weather-records/{record_id}", response_model=schemas.WeatherRecordResponse)
def get_weather_record(record_id: int, db: Session = Depends(get_db)):
    record = crud.get_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Weather record not found")

    output = schemas.WeatherRecordResponse.model_validate(record)
    output.weather_data = json.loads(record.weather_data)
    return output


@app.put("/api/weather-records/{record_id}", response_model=schemas.WeatherRecordResponse)
async def update_weather_record(record_id: int, payload: schemas.WeatherRecordUpdate, db: Session = Depends(get_db)):
    record = crud.get_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Weather record not found")

    resolved = await resolve_location(payload.location)
    forecast = await fetch_forecast(
        resolved["latitude"],
        resolved["longitude"],
        payload.start_date,
        payload.end_date,
    )

    updated = crud.update_record(
        db=db,
        record=record,
        location_input=payload.location,
        resolved_location=resolved["resolved_location"],
        latitude=resolved["latitude"],
        longitude=resolved["longitude"],
        start_date=payload.start_date,
        end_date=payload.end_date,
        weather_data=forecast,
    )

    output = schemas.WeatherRecordResponse.model_validate(updated)
    output.weather_data = json.loads(updated.weather_data)
    return output


@app.delete("/api/weather-records/{record_id}")
def delete_weather_record(record_id: int, db: Session = Depends(get_db)):
    record = crud.get_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Weather record not found")

    crud.delete_record(db, record)
    return {"message": f"Weather record {record_id} deleted successfully"}


@app.get("/api/export/json")
def export_json(db: Session = Depends(get_db)):
    records = crud.get_records(db)
    return JSONResponse(content=records_to_json(records))


@app.get("/api/export/csv")
def export_csv(db: Session = Depends(get_db)):
    records = crud.get_records(db)
    content = records_to_csv(records)
    headers = {"Content-Disposition": "attachment; filename=weather_records.csv"}
    return Response(content=content, media_type="text/csv", headers=headers)
