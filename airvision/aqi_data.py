# --- STATIC DISTRICT BASELINE DATA & CONFIGURATION ---
CITY_AQI_DATA = {
    "bhaktapur": {
        "aqi": 70,
        "pm25": 28,
        "status": "Moderate",
        "advice": "Moderate air quality. Sensitive groups should be cautious during prolonged outdoor activity."
    },
    "kathmandu": {
        "aqi": 125,
        "pm25": 45,
        "status": "Unhealthy",
        "advice": "Reduce outdoor activities. Wear a mask when going outside."
    },
    "nepalgunj": {
        "aqi": 95,
        "pm25": 35,
        "status": "Moderate",
        "advice": "Sensitive groups should limit prolonged outdoor exertion."
    },
    "biratnagar": {
        "aqi": 58,
        "pm25": 24,
        "status": "Moderate",
        "advice": "Moderate air quality. Sensitive groups should be cautious."
    },
    "dhangadhi": {
        "aqi": 88,
        "pm25": 30,
        "status": "Moderate",
        "advice": "Moderate air quality. Stay aware of outdoor activity levels."
    },
    "surkhet": {
        "aqi": 48,
        "pm25": 15,
        "status": "Good",
        "advice": "Air quality is good. Enjoy outdoor activities freely."
    },
}

ADVICE_MAP = {
    "good": "Air quality is satisfactory. Enjoy outdoor activities.",
    "moderate": "Sensitive groups should limit prolonged outdoor exertion.",
    "unhealthy": "Reduce outdoor activities. Wear a mask when going outside.",
}

# The list of cities supported by the machine learning models
MODEL_CITIES = ["bhaktapur", "kathmandu", "nepalgunj", "biratnagar", "dhangadhi", "surkhet"]

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

# Builds district cards dynamically for dashboard/landing pages
def build_city_cards():
    cards = []
    for city in MODEL_CITIES:
        data = CITY_AQI_DATA.get(city, {
            "aqi": 85,
            "pm25": 40,
            "status": "Moderate",
            "advice": "Monitor air quality conditions.",
        })
        cards.append({
            "city": city.capitalize(),
            "aqi": data["aqi"],
            "status": data["status"],
            "status_class": status_class(data["status"]),
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
