import { useMemo, useState } from "react";
import { getCurrentWeather, getForecastWeather } from "./services/weatherApi";

function wd(dateStr) {
  return new Date(dateStr).toLocaleDateString(undefined, { weekday: "short" });
}

function md(dateStr) {
  return new Date(dateStr).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function App() {
  const [location, setLocation] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [current, setCurrent] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [savedLocations, setSavedLocations] = useState([
    { name: "New York, USA", meta: "68°F • Partly Cloudy" },
    { name: "Tokyo, Japan", meta: "75°F • Sunny" },
    { name: "London, UK", meta: "61°F • Cloudy" },
  ]);
  const [recentSearches, setRecentSearches] = useState([
    "Paris, France",
    "Seattle, USA",
    "Chicago, USA",
  ]);

  const apiBase = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

  const nowLabel = useMemo(
    () =>
      new Date().toLocaleString(undefined, {
        weekday: "long",
        month: "long",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      }),
    [current]
  );

  const fdays = forecast
    ? forecast.time.map((time, idx) => ({
        time,
        max: forecast.temperature_2m_max?.[idx],
        min: forecast.temperature_2m_min?.[idx],
        wind: forecast.wind_speed_10m_max?.[idx],
        condition: forecast.weather_condition?.[idx] || "Unknown",
      }))
    : [];

  const queryWeather = async (q) => {
    const v = q.trim();
    if (!v) return setError("Enter a city or place.");
    try {
      setError("");
      setLoading(true);
      const [c, f] = await Promise.all([getCurrentWeather(v), getForecastWeather(v)]);
      setCurrent(c);
      setForecast(f.forecast);
      setRecentSearches((prev) => {
        const next = [c.resolved_location, ...prev.filter((x) => x !== c.resolved_location)];
        return next.slice(0, 5);
      });
    } catch (e) {
      setCurrent(null);
      setForecast(null);
      setError(e.message || "Unable to fetch weather");
    } finally {
      setLoading(false);
    }
  };

  const useCurrent = () => {
    if (!navigator.geolocation) return setError("Geolocation not supported.");
    navigator.geolocation.getCurrentPosition(
      async (p) => {
        const coords = `${p.coords.latitude},${p.coords.longitude}`;
        setLocation(coords);
        await queryWeather(coords);
      },
      () => setError("Unable to get current location.")
    );
  };

  const dl = (name, text, type) => {
    const b = new Blob([text], { type });
    const u = URL.createObjectURL(b);
    const a = document.createElement("a");
    a.href = u;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(u);
  };

  const saveSnapshotJson = () => {
    if (!current || !forecast) return setError("Run a query before exporting snapshot.");
    dl("weather_snapshot.json", JSON.stringify({ exported_at: new Date().toISOString(), current, forecast }, null, 2), "application/json");
  };

  const saveRecordsJson = async () => {
    try {
      const r = await fetch(`${apiBase}/api/export/json`);
      if (!r.ok) throw new Error("JSON export failed");
      dl("weather_records_export.json", JSON.stringify(await r.json(), null, 2), "application/json");
    } catch (e) {
      setError(e.message || "JSON export failed.");
    }
  };

  const saveRecordsCsv = async () => {
    try {
      const r = await fetch(`${apiBase}/api/export/csv`);
      if (!r.ok) throw new Error("CSV export failed");
      dl("weather_records_export.csv", await r.text(), "text/csv");
    } catch (e) {
      setError(e.message || "CSV export failed.");
    }
  };

  const saveToDb = async () => {
    const v = location.trim();
    if (!v) return setError("Enter location before saving.");
    const s = new Date();
    const e = new Date();
    e.setDate(e.getDate() + 4);
    try {
      const r = await fetch(`${apiBase}/api/weather-records`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          location: v,
          start_date: s.toISOString().slice(0, 10),
          end_date: e.toISOString().slice(0, 10),
        }),
      });
      if (!r.ok) throw new Error("Save to DB failed");
      setError("");
    } catch (x) {
      setError(x.message || "Save to DB failed");
    }
  };

  const place = current?.resolved_location || "San Francisco, California, USA";
  const temp = current ? `${Math.round(current.current_weather.temperature_2m)}°F`.replace("°F", "°") : "72°F";
  const cond = current?.current_weather.weather_condition || "Partly Cloudy";
  const errorText = (error || "").toLowerCase();
  const showLocationNotFound = errorText.includes("not found") || errorText.includes("could not");
  const showNoInternet = errorText.includes("network") || errorText.includes("internet") || errorText.includes("failed to fetch");
  const showBottomStatus = showLocationNotFound || showNoInternet;

  const openMaps = () => {
    const url = current
      ? `https://www.google.com/maps?q=${current.latitude},${current.longitude}`
      : "https://www.google.com/maps";
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const openNews = () => {
    const q = encodeURIComponent(`${location || place} weather news`);
    window.open(`https://news.google.com/search?q=${q}`, "_blank", "noopener,noreferrer");
  };

  const openTravel = () => {
    const q = encodeURIComponent(`${location || place} travel weather`);
    window.open(`https://www.google.com/search?q=${q}`, "_blank", "noopener,noreferrer");
  };

  const showAlerts = () => window.open("https://www.weather.gov/alerts", "_blank", "noopener,noreferrer");
  const showProfile = () => window.open("https://www.google.com/search?q=weather+profile+settings", "_blank", "noopener,noreferrer");
  const addSavedLocation = () => {
    if (!current) return setError("Search a location first, then click Add Location.");
    const entry = {
      name: current.resolved_location,
      meta: `${Math.round(current.current_weather.temperature_2m)}°F • ${current.current_weather.weather_condition}`,
    };
    setSavedLocations((prev) => {
      const merged = [entry, ...prev.filter((x) => x.name !== entry.name)];
      return merged.slice(0, 6);
    });
    setError("");
  };
  const tryAgainSearch = async () => {
    if (!location.trim()) return setError("Enter a location to retry.");
    await queryWeather(location);
  };
  const retryConnection = async () => {
    if (!location.trim()) return setError("Enter a location to retry connection check.");
    await queryWeather(location);
  };

  return (
    <div className="sv-wrap">
      <div className="sv-app">
        <header className="sv-header">
          <button className="logo" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>☁ Atmosphere</button>
          <nav className="tabs">
            <button className="active" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>Weather</button>
            <button onClick={openMaps}>Maps</button>
            <button onClick={showAlerts}>Alerts</button>
            <button onClick={openNews}>News</button>
            <button onClick={openTravel}>Travel</button>
          </nav>
          <div className="right-actions">
            <button className="loc" onClick={useCurrent} disabled={loading}>Use Current Location</button>
            <button className="bell" onClick={showAlerts}>🔔</button>
            <button className="jr" onClick={showProfile}>JR</button>
          </div>
        </header>

        <div className="search-row">
          <form onSubmit={(e) => { e.preventDefault(); queryWeather(location); }}>
            <input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Search for a city or place" />
            <button type="submit" disabled={loading}>{loading ? "Loading..." : "Search"}</button>
          </form>
          {error ? <p className="err">{error}</p> : null}
        </div>

        <section className="save-toolbar">
          <span>Save & Export</span>
          <div className="save-actions">
            <button onClick={saveToDb}>Save to DB</button>
            <button onClick={saveSnapshotJson}>Snapshot JSON</button>
            <button onClick={saveRecordsJson}>Records JSON</button>
            <button onClick={saveRecordsCsv}>Records CSV</button>
          </div>
        </section>

        <main className="grid">
          <section className="left">
            <article className="hero">
              <p className="place">📍 {place}</p>
              <p className="time">{current ? nowLabel : "Friday, May 23 • 10:30 AM"}</p>
              <div className="tempLine"><h1>{temp}</h1><p>{cond}</p></div>
              <p className="feels">Feels like 71°</p>
              <div className="quick-metrics">
                <div><span>Humidity</span><strong>{current ? `${current.current_weather.relative_humidity_2m}%` : "68%"}</strong></div>
                <div><span>Wind</span><strong>{current ? `${Math.round(current.current_weather.wind_speed_10m)} km/h` : "12 mph SW"}</strong></div>
                <div><span>UV Index</span><strong>6 High</strong></div>
                <div><span>Precip Chance</span><strong>10%</strong></div>
              </div>
            </article>

            <article className="block">
              <div className="bhead"><h3>5-Day Forecast</h3><span>View full forecast →</span></div>
              <div className="d5">
                {fdays.map((d) => (
                  <div key={d.time} className="dcard">
                    <p className="dw">{wd(d.time)}</p>
                    <p className="dt">{md(d.time)}</p>
                    <p className="tm">{Math.round(d.max)}° <span>{Math.round(d.min)}°</span></p>
                    <p className="pc">💧 {Math.round(d.wind)}%</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="block">
              <div className="bhead"><h3>Hourly Forecast</h3></div>
              <div className="hours">
                {fdays.slice(0, 9).map((d) => (
                  <div key={`h-${d.time}`} className="hbox"><p>{wd(d.time)}</p><strong>{Math.round(d.max)}°</strong><span>{Math.round(d.wind)}%</span></div>
                ))}
              </div>
            </article>

            {showBottomStatus ? (
              <section className="bottom-cards">
                {showLocationNotFound ? (
                  <article>
                    <h4>Location not found</h4>
                    <p>We could not find that place. Try another query.</p>
                    <button onClick={tryAgainSearch}>Try Again</button>
                  </article>
                ) : null}
                {showNoInternet ? (
                  <article>
                    <h4>No internet connection</h4>
                    <p>Retry live weather data fetch.</p>
                    <button onClick={retryConnection}>Retry</button>
                  </article>
                ) : null}
              </section>
            ) : null}
          </section>

          <aside className="right">
            <article className="mini"><h4>☀ Sunrise & Sunset</h4><p>5:48 AM</p><p>8:24 PM</p></article>
            <article className="mini"><h4>🍃 Air Quality</h4><p className="aq">42 <span>Good</span></p><p>Air quality is satisfactory and poses little or no risk.</p></article>
            <article className="mini"><h4>🌧 Precipitation</h4><p className="aq">10%</p><p>Chance of rain</p></article>
            <article className="mini"><h4>👕 What to Wear</h4><p>Light layers</p><p>Comfortable with a light jacket in the morning.</p></article>
            <article className="mini wide"><h4>✈ Travel Tip</h4><p>Great conditions for outdoor activities. Low rain chance all weekend.</p></article>
            <article className="mini wide"><h4>Location Map</h4><a href={current ? `https://www.google.com/maps?q=${current.latitude},${current.longitude}` : "https://www.openstreetmap.org"} target="_blank" rel="noreferrer">View larger map →</a></article>
            <article className="mini">
              <h4>Saved Locations</h4>
              <ul className="list">
                {savedLocations.map((item) => (
                  <li key={item.name}><strong>{item.name}</strong><span>{item.meta}</span></li>
                ))}
              </ul>
            </article>
            <article className="mini">
              <h4>Recent Searches</h4>
              <ul className="list">
                {recentSearches.map((item) => (
                  <li key={item}><strong>{item}</strong><span>Recent lookup</span></li>
                ))}
              </ul>
            </article>
            <article className="mini wide"><h4>Data Vault</h4><div className="stack"><button onClick={saveToDb}>Save to DB</button><button onClick={saveSnapshotJson}>Save Snapshot JSON</button><button onClick={saveRecordsJson}>Save Records JSON</button><button onClick={saveRecordsCsv}>Save Records CSV</button></div></article>
            <article className="mini wide"><h4>PM Accelerator</h4><p>Prepared by Marappa Reddy Churnika</p></article>
          </aside>
        </main>
      </div>
    </div>
  );
}
