# --- STATIC DISTRICT BASELINE DATA & CONFIGURATION ---
CITY_AQI_DATA = {
    "lalitpur": {
        "pm25": 43,
        "aqi": 119,
        "status": "Unhealthy",
    },
    "bhaktapur": {
        "pm25": 50,
        "aqi": 128,
        "status": "Unhealthy",
    },
    "kathmandu": {
        "pm25": 53,
        "aqi": 132,
        "status": "Unhealthy",
    },
    "dhankuta": {
        "pm25": 27,
        "aqi": 82,
        "status": "Moderate",
    },
    "kanchanpur": {
        "pm25": 37,
        "aqi": 105,
        "status": "Unhealthy",
    },
    "dang": {
        "pm25": 33,
        "aqi": 95,
        "status": "Moderate",
    },
}

ADVICE_MAP = {
    "good": "Air quality is satisfactory. Enjoy outdoor activities.",
    "moderate": "Sensitive groups should limit prolonged outdoor exertion.",
    "unhealthy": "Reduce outdoor activities. Wear a mask when going outside.",
}

# The list of cities supported by the machine learning models
MODEL_CITIES = ["lalitpur", "bhaktapur", "kathmandu", "dhankuta", "kanchanpur", "dang"]

def normalize_city(city: str) -> str:
    return city.strip().lower() if city else ""

def status_class(status: str) -> str:
    if not status:
        return "moderate"
    status_lower = status.lower()
    if "unhealthy" in status_lower:
        return "unhealthy"
    if "moderate" in status_lower:
        return "moderate"
    if "good" in status_lower:
        return "good"
    return status_lower

# PM2.5 (µg/m³) to AQI conversion using EPA 24-hour breakpoints

PM25_BREAKPOINTS = [
    (0.0, 12.0, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 500.4, 301, 500),
]

# predict gareko pm2.5 lai aqi ma convert garne function
def pm25_to_aqi(pm25: float) -> int:
    if pm25 < 0:
        return 0
    if pm25 > 500.4:
        return 500
    for c_low, c_high, a_low, a_high in PM25_BREAKPOINTS:
        if c_low <= pm25 <= c_high:
            aqi_val = ((a_high - a_low) / (c_high - c_low)) * (pm25 - c_low) + a_low
            return round(aqi_val)
    return 500

# AQI status based on the AQI value
def aqi_status(aqi: int) -> str:
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    return "Unhealthy"

def make_forecast_item(day: str, aqi: int) -> dict:
    status = aqi_status(aqi)
    return {
        "day": day,
        "aqi": aqi,
        "status": status,
        "status_class": status_class(status),
    }

def enrich_forecast(forecast_list):
    return [
        {
            "day": item["day"],
            "aqi": item["aqi"],
            "status": item.get("status", aqi_status(item["aqi"])),
            "status_class": status_class(item.get("status", aqi_status(item["aqi"])))
        }
        for item in forecast_list
    ]

# Builds district cards dynamically for dashboard/landing pages using stored window + model predictions
def build_city_cards():
    from .predictor import predict_next_day
    cards = []
    for city in MODEL_CITIES:
        window = load_pm25_window(city)
        try:
            pred_pm25 = predict_next_day(window[0], window[1], window[2], district=city)
            aqi_val = pm25_to_aqi(pred_pm25)
            update_pm25_window(city, pred_pm25)
        except Exception:
            aqi_val = pm25_to_aqi(window[0])
        status = aqi_status(aqi_val)
        cards.append({
            "city": city.capitalize(),
            "aqi": aqi_val,
            "status": status,
            "status_class": status_class(status),
        })
    return cards

def get_city_data(city: str):
    city_lower = normalize_city(city)
    return CITY_AQI_DATA.get(city_lower, {
        "aqi": 85,
        "pm25": 40,
        "status": "Moderate",
        "advice": "Monitor air quality conditions.",
    })

import json
from pathlib import Path

_STORAGE_PATH = Path(__file__).parent / "pm25_windows.json"

_INITIAL_WINDOWS = {
    "lalitpur":  [43, 43, 43],
    "bhaktapur": [50, 50, 50],
    "kathmandu": [53, 53, 53],
    "dhankuta":  [27, 27, 27],
    "kanchanpur":[37, 37, 37],
    "dang":      [33, 33, 33],
}

def _ensure_storage():
    if not _STORAGE_PATH.exists():
        data = {d: {"window": w, "updated": ""} for d, w in _INITIAL_WINDOWS.items()}
        with open(_STORAGE_PATH, "w") as f:
            json.dump(data, f, indent=2)

def load_pm25_window(district: str):
    _ensure_storage()
    with open(_STORAGE_PATH) as f:
        data = json.load(f)
    entry = data.get(district)
    if entry and entry.get("window"):
        return entry["window"]
    return _INITIAL_WINDOWS.get(district, [40, 40, 40])

def update_pm25_window(district: str, new_pm25: float): # naya predict gareko value halera shift garxa 
    _ensure_storage()
    with open(_STORAGE_PATH) as f:
        data = json.load(f)
    entry = data.get(district, {})
    window = entry.get("window", _INITIAL_WINDOWS.get(district, [40, 40, 40]))
    window = [round(window[1], 1), round(window[2], 1), round(new_pm25, 1)]
    import datetime
    data[district] = {"window": window, "updated": str(datetime.date.today())}
    with open(_STORAGE_PATH, "w") as f:
        json.dump(data, f, indent=2)
