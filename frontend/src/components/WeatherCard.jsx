const weatherEmojiByCode = {
  0: "☀️",
  1: "🌤️",
  2: "⛅",
  3: "☁️",
  45: "🌫️",
  48: "🌫️",
  51: "🌦️",
  53: "🌦️",
  55: "🌧️",
  56: "🌧️",
  57: "🌧️",
  61: "🌧️",
  63: "🌧️",
  65: "🌧️",
  66: "🌨️",
  67: "🌨️",
  71: "🌨️",
  73: "🌨️",
  75: "❄️",
  77: "❄️",
  80: "🌦️",
  81: "🌧️",
  82: "⛈️",
  85: "🌨️",
  86: "❄️",
  95: "⛈️",
  96: "⛈️",
  99: "⛈️",
};

export default function WeatherCard({ day, date, max, min, wind, code, condition }) {
  const emoji = weatherEmojiByCode[code] || "🌡️";
  return (
    <article className="forecast-card">
      <div className="card-top">
        <h4>{day}</h4>
        <span className="emoji-pill">{emoji}</span>
      </div>
      <p className="date-label">{date}</p>
      <p className="condition">{condition}</p>
      <div className="split">
        <p>High <strong>{Math.round(max)}°</strong></p>
        <p>Low <strong>{Math.round(min)}°</strong></p>
      </div>
      <p className="wind">Wind {Math.round(wind)} km/h</p>
    </article>
  );
}
