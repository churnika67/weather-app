const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function parseResponse(response) {
  if (!response.ok) {
    let message = "Something went wrong";
    try {
      const data = await response.json();
      message = data.detail || JSON.stringify(data);
    } catch {
      message = `Request failed with status ${response.status}`;
    }
    throw new Error(message);
  }
  return response.json();
}

export async function getCurrentWeather(location) {
  const response = await fetch(
    `${API_BASE_URL}/api/weather/current?location=${encodeURIComponent(location)}`
  );
  return parseResponse(response);
}

export async function getForecastWeather(location) {
  const response = await fetch(
    `${API_BASE_URL}/api/weather/forecast?location=${encodeURIComponent(location)}`
  );
  return parseResponse(response);
}
