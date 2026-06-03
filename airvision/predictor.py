import os
import joblib
import numpy as np
from django.conf import settings

# Base directory where trained regression .pkl model files are saved
MODEL_DIR = os.path.join(settings.BASE_DIR, "models")

# Mapping of district/city names to their respective trained pkl file names
CITY_TO_MODEL_NAME = {
    "bhaktapur": "Bhaktapur_model.pkl",
    "hetauda": "Hetauda_model.pkl",
    "ilam": "Ilam_model.pkl",
    "janakpur": "Janakpur_model.pkl",
    "khumaltar": "Khumaltar_model.pkl",
    "kirtipur": "Kirtipur_model.pkl",
    "mahendranagar": "Mahendranagar_model.pkl",
}

# --- 1. MODEL LOADING LOGIC ---
# Loads the joblib/pkl model for the given district
def load_regression_model(city_key):
    model_filename = CITY_TO_MODEL_NAME.get(city_key)
    if not model_filename:
        raise ValueError(f"No model found for district: {city_key}")
    model_path = os.path.join(MODEL_DIR, model_filename)
    return joblib.load(model_path)

# --- 2. RECURSIVE FORECASTING LOGIC ---
# Uses the model to predict next day, then rolls the window to predict subsequent days
def run_recursive_forecast(model, last_window, days):
    predictions = []
    window = last_window.copy()
    for _ in range(days):
        # Predict the next step
        pred = model.predict([window])[0]
        predictions.append(pred)
        # Shift the window (discard the oldest value, append the new prediction)
        window = np.append(window[1:], pred)
    return predictions

# --- 3. MAIN FORECAST INTERFACE ---
# Takes district name and 3-day PM2.5 history, and returns forecasts
def predict_pm25_forecast(district, x1, x2, x3):
    district_key = district.strip().lower()
    model = load_regression_model(district_key)
    last_window = np.array([x1, x2, x3])
    
    # Predict next day (tomorrow)
    next_day = model.predict([last_window])[0]
    
    # Forecast recursively for next 3 days and 7 days
    forecast_3 = run_recursive_forecast(model, last_window, 3)
    forecast_7 = run_recursive_forecast(model, last_window, 7)
    
    return {
        "next_day": float(next_day),
        "forecast_3_day": [float(val) for val in forecast_3],
        "forecast_7_day": [float(val) for val in forecast_7],
    }
