# Last 3 actual PM2.5 readings from the dataset (pm 2.5.xlsx) per district.
# x1 = 3 days ago, x2 = 2 days ago, x3 = yesterday.
ACTUAL_PM25_WINDOWS = {
    "lalitpur":   (99.8, 60.8, 65.8),
    "bhaktapur":  (40.9, 34.5, 69.4),
    "kathmandu":  (19.1, 19.2,  4.4),
    "dhankuta":   (15.1, 13.1, 38.0),
    "kanchanpur":  (3.2,  4.2,  5.1),
    "dang":       (57.5, 50.3, 63.9),
}

def get_actual_pm25_window(district: str):
    return ACTUAL_PM25_WINDOWS.get(district)

def load_district_window(district: str):
    """Returns the last 3 actual PM2.5 readings from the dataset."""
    actual = get_actual_pm25_window(district)
    if actual:
        return actual
    data = get_city_data(district)
    pm25 = data['pm25']
    return pm25, pm25, pm25

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

# Builds district cards dynamically for dashboard/landing pages using dataset values
def build_city_cards():
    from .predictor import predict_next_day
    cards = []
    for city in MODEL_CITIES:
        x1, x2, x3 = load_district_window(city)
        try:
            pred_pm25 = predict_next_day(x1, x2, x3, district=city)
            aqi_val = pm25_to_aqi(pred_pm25)
        except Exception:
            aqi_val = pm25_to_aqi(x3)
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


