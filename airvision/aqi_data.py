from typing import List, Dict

CITY_AQI_DATA = {
    "bhaktapur": {
        "aqi": 70,
        "pm25": 28,
        "status": "Moderate",
        "advice": "Moderate air quality. Sensitive groups should be cautious during prolonged outdoor activity."
    },
    "biratnagar": {
        "aqi": 58,
        "pm25": 24,
        "status": "Moderate",
        "advice": "Moderate air quality. Sensitive groups should be cautious."
    },
    "hetauda": {
        "aqi": 75,
        "pm25": 32,
        "status": "Moderate",
        "advice": "Moderate air quality. Sensitive groups should limit prolonged outdoor exertion."
    },
    "ilam": {
        "aqi": 50,
        "pm25": 18,
        "status": "Good",
        "advice": "Air quality is good. Enjoy outdoor activities freely."
    },
    "janakpur": {
        "aqi": 88,
        "pm25": 45,
        "status": "Moderate",
        "advice": "Moderate air quality. Sensitive groups should be cautious during prolonged activity."
    },
    "khumaltar": {
        "aqi": 95,
        "pm25": 48,
        "status": "Moderate",
        "advice": "Air quality is moderate. Limit long periods outside if you are sensitive."
    },
    "kirtipur": {
        "aqi": 62,
        "pm25": 22,
        "status": "Moderate",
        "advice": "Air quality is moderate. Stay aware of outdoor activity levels."
    },
    "mahendranagar": {
        "aqi": 55,
        "pm25": 20,
        "status": "Good",
        "advice": "Air quality is good. Outdoor activities are safe for most people."
    },
}


DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

ADVICE_MAP = {
    "good": "Air quality is satisfactory. Enjoy outdoor activities.",
    "moderate": "Sensitive groups should limit prolonged outdoor exertion.",
    "unhealthy": "Reduce outdoor activities. Wear a mask when going outside.",
}

CITY_TO_MODEL_NAME = {
    "bhaktapur": "Bhaktapur_model.pkl",
    "hetauda": "Hetauda_model.pkl",
    "ilam": "Ilam_model.pkl",
    "janakpur": "Janakpur_model.pkl",
    "khumaltar": "Khumaltar_model.pkl",
    "kirtipur": "Kirtipur_model.pkl",
    "mahendranagar": "Mahendranagar_model.pkl",
}

MODEL_CITIES = sorted(CITY_TO_MODEL_NAME.keys())


def normalize_city(city: str) -> str:
    return city.strip().lower() if city else ""


def status_class(status: str) -> str:
    if not status:
        return "moderate"
    return status.lower()


def aqi_status(aqi: int) -> str:
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Moderate"
    return "Unhealthy"


def make_forecast_item(day: str, aqi: int) -> Dict[str, object]:
    status = aqi_status(aqi)
    return {
        "day": day,
        "aqi": aqi,
        "status": status,
        "status_class": status_class(status),
    }


def enrich_forecast(forecast_list: List[Dict[str, object]]) -> List[Dict[str, object]]:
    return [
        {
            "day": item["day"],
            "aqi": item["aqi"],
            "status": item.get("status", aqi_status(item["aqi"])),
            "status_class": status_class(item.get("status", aqi_status(item["aqi"])))
        }
        for item in forecast_list
    ]


def build_city_cards() -> List[Dict[str, object]]:
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


def get_city_data(city: str) -> Dict[str, object]:
    city_lower = normalize_city(city)
    return CITY_AQI_DATA.get(city_lower, {
        "aqi": 85,
        "pm25": 40,
        "status": "Moderate",
        "advice": "Monitor air quality conditions.",
    })


