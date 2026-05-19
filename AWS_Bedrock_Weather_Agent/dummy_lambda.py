
import json
import os
import urllib.request
import urllib.parse
from typing import Tuple, Optional, Dict

USER_AGENT = "WeatherAssistant/1.0"

def http_get_json(url: str, headers: Optional[Dict] = None, timeout: int = 8) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def geocode_city(city: str) -> Optional[Tuple[float, float]]:
    if not city:
        return None
    params = urllib.parse.urlencode({"q": city, "format": "json", "limit": 1})
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    headers = {"User-Agent": USER_AGENT}
    try:
        results = http_get_json(url, headers=headers)
        if not results:
            return None
        return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception as e:
        print(f"[ERROR] Geocoding failed: {e}")
        return None

def get_grid_endpoints(lat: float, lon: float) -> Tuple[str, str]:
    url = f"https://api.weather.gov/points/{lat:.4f},{lon:.4f}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    data = http_get_json(url, headers=headers)
    props = data.get("properties", {})
    return props["forecast"], props["forecastHourly"]

def get_forecast(url: str) -> dict:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    return http_get_json(url, headers=headers)

def summarize_hourly_24h(hourly_json: dict) -> str:
    periods = hourly_json.get("properties", {}).get("periods", [])
    if not periods:
        return "No hourly forecast available."
    lines = []
    for p in periods[:24]:
        temp = p.get("temperature")
        unit = p.get("temperatureUnit", "F")
        short = p.get("shortForecast", "")
        wind = f"{p.get('windSpeed', '')} {p.get('windDirection', '')}".strip()
        lines.append(f"{temp}°{unit}, {short}, wind {wind}")
    return "Next 24 hours: " + " | ".join(lines[:6])

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event, default=str)}")
    api_path = event.get('apiPath', '/weather') # Extract parameters from Bedrock agent format
    http_method = event.get('httpMethod', 'GET')
    parameters = event.get('parameters', [])
    # Parse parameters
    city = None
    mode = "hourly"
    for param in parameters:
        if param['name'] == 'city':
            city = param['value']
        elif param['name'] == 'mode':
            mode = param['value']
    print(f"Parsed: city={city}, mode={mode}")
    # Validate input
    if not city:
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', 'weather_tools'),
                "apiPath": api_path,
                "httpMethod": http_method,
                "httpStatusCode": 400,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps({"error": "Missing required parameter: city"})
                    }
                }
            }
        }
    try:
        # Geocode city
        coords = geocode_city(city)
        if not coords:
            return {
                "messageVersion": "1.0",
                "response": {
                    "actionGroup": event.get('actionGroup', 'weather_tools'),
                    "apiPath": api_path,
                    "httpMethod": http_method,
                    "httpStatusCode": 404,
                    "responseBody": {
                        "application/json": {
                            "body": json.dumps({"error": f"Could not find city: {city}"})
                        }
                    }
                }
            }
        lat, lon = coords
        print(f"Geocoded '{city}' to lat={lat}, lon={lon}")
        # Get weather
        forecast_url, hourly_url = get_grid_endpoints(lat, lon)
        data = get_forecast(hourly_url if mode == "hourly" else forecast_url)
        weather_report = summarize_hourly_24h(data)
        # Return in correct Bedrock format
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', 'weather_tools'),
                "apiPath": api_path,  # CRITICAL: Must match input
                "httpMethod": http_method,
                "httpStatusCode": 200,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps({"weather_report": weather_report})
                    }
                }
            }
        }
    except Exception as e:
        print(f"[ERROR] {e}")
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', 'weather_tools'),
                "apiPath": api_path,
                "httpMethod": http_method,
                "httpStatusCode": 500,
                "responseBody": {
                    "application/json": {
                        "body": json.dumps({"error": "Weather service error"})
                    }
                }
            }
        }
