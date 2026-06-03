import os
import joblib
import numpy as np
from django.conf import settings
from .aqi_data import CITY_TO_MODEL_NAME

MODEL_DIR = os.path.join(settings.BASE_DIR, "models")


def load_model(model_filename):
    model_path = os.path.join(MODEL_DIR, model_filename)
    return joblib.load(model_path)


# recursive forecasting
def forecast(model, last_window, days):
    predictions = []
    window = last_window.copy()

    for _ in range(days):
        pred = model.predict([window])[0]
        predictions.append(pred)
        window = np.append(window[1:], pred)

    return predictions


# main prediction function
def predict_pm25(district, x1, x2, x3):
    district_key = district.strip().lower()
    model_filename = CITY_TO_MODEL_NAME.get(district_key) #district anusar model choose garne 
    if not model_filename:
        raise ValueError(f"No model found for district '{district_key}'")

    model = load_model(model_filename)
    last_window = np.array([x1, x2, x3])

    #Actual prediction logic
    next_day = model.predict([last_window])[0]
    forecast_3 = forecast(model, last_window, 3)
    forecast_7 = forecast(model, last_window, 7)

    return {
        "next_day": float(next_day),
        "forecast_3_day": [float(value) for value in forecast_3],
        "forecast_7_day": [float(value) for value in forecast_7],
    }