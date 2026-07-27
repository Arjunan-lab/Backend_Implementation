"""Reusable OpenWeatherMap current-weather service."""

import logging
from typing import Any, Dict

import requests

from app.config import settings


_LOGGER = logging.getLogger(__name__)
_CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
_REQUEST_TIMEOUT_SECONDS = 10


class WeatherServiceError(RuntimeError):
    """Raised when weather information cannot be retrieved or parsed."""


def get_weather(location: str) -> Dict[str, Any]:
    """Fetch current weather for a city, district, village, or town.

    Args:
        location: Human-readable location accepted by OpenWeatherMap.

    Returns:
        A dictionary with the resolved location, temperature in Celsius,
        humidity percentage, and rainfall in millimetres for the last hour.

    Raises:
        ValueError: If the location is empty or cannot be found.
        PermissionError: If the OpenWeatherMap API key is invalid.
        TimeoutError: If OpenWeatherMap does not respond before the timeout.
        ConnectionError: If the weather service cannot be reached.
        WeatherServiceError: If the API returns an HTTP error or unexpected data.
    """
    if not isinstance(location, str) or not location.strip():
        raise ValueError("A non-empty location is required to fetch weather.")

    api_key = settings.OPENWEATHER_API_KEY.strip()
    if not api_key:
        raise WeatherServiceError("OPENWEATHER_API_KEY is not configured.")

    try:
        response = requests.get(
            _CURRENT_WEATHER_URL,
            params={"q": location.strip(), "appid": api_key, "units": "metric"},
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
    except requests.Timeout as exc:
        _LOGGER.warning("Timed out while fetching weather for %s", location)
        raise TimeoutError("Weather service request timed out.") from exc
    except requests.ConnectionError as exc:
        _LOGGER.warning("Could not connect to weather service for %s", location)
        raise ConnectionError("Unable to connect to the weather service.") from exc
    except requests.RequestException as exc:
        _LOGGER.exception("Weather service request failed for %s", location)
        raise WeatherServiceError("Weather service request failed.") from exc

    if response.status_code == 404:
        raise ValueError(f"Location not found: {location.strip()}")
    if response.status_code in (401, 403):
        raise PermissionError("OpenWeatherMap API key is invalid or unauthorized.")

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        _LOGGER.warning(
            "Weather service returned HTTP %s for %s", response.status_code, location
        )
        raise WeatherServiceError(
            f"Weather service returned HTTP {response.status_code}."
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise WeatherServiceError("Weather service returned invalid JSON.") from exc

    if not isinstance(data, dict):
        raise WeatherServiceError("Weather service returned an unexpected response.")

    main = data.get("main")
    if not isinstance(main, dict):
        raise WeatherServiceError("Weather service response is missing weather details.")

    resolved_location = data.get("name")
    temperature = main.get("temp")
    humidity = main.get("humidity")
    if not isinstance(resolved_location, str) or not resolved_location:
        raise WeatherServiceError("Weather service response is missing the location.")
    if not isinstance(temperature, (int, float)) or isinstance(temperature, bool):
        raise WeatherServiceError("Weather service response contains an invalid temperature.")
    if not isinstance(humidity, (int, float)) or isinstance(humidity, bool):
        raise WeatherServiceError("Weather service response contains an invalid humidity.")

    rain = data.get("rain", {})
    rainfall = rain.get("1h", 0.0) if isinstance(rain, dict) else 0.0
    if not isinstance(rainfall, (int, float)) or isinstance(rainfall, bool):
        rainfall = 0.0

    return {
        "location": resolved_location,
        "temperature": float(temperature),
        "humidity": int(humidity),
        "rainfall": float(rainfall),
    }


if __name__ == "__main__":
    weather = get_weather("Bangalore")
    print(weather)
