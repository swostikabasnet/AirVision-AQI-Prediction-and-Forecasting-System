import os
import random
import joblib
import pandas as pd

_district_models = {}
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")

def get_district_model(district):
    district_key = (district or '').strip().lower()
    if district_key in ['', 'undefined', 'null']:
        district_key = 'lalitpur'

    if district_key not in _district_models:
        alt_keys = [district_key, district_key.replace(' ', ''), district_key.replace(' ', '_')]
        filenames = []
        for key in alt_keys:
            filenames.extend([
                f"{key}_model.pkl",
                f"{key.capitalize()}_model.pkl",
                f"{key}.pkl",
                f"{key.capitalize()}.pkl",
            ])

        model = None
        for filename in filenames:
            path = os.path.join(MODEL_DIR, filename)
            if os.path.exists(path):
                try:
                    # Loading the model from the file
                    model = joblib.load(path)  
                    break
                except Exception:
                    continue

        if model is None:
            path = os.path.join(MODEL_DIR, "lalitpur_model.pkl")
            if os.path.exists(path):
                try:
                    model = joblib.load(path)
                except Exception:
                    pass

        _district_models[district_key] = model
    return _district_models[district_key]

# Predicts the next day's PM2.5 value and a 7-day forecast for a given district using the provided lag features (x1, x2, x3).
def predict_pm25_forecast(district, x1, x2, x3, days=7):
    model = get_district_model(district or "bhaktapur")
    if model is None:
        model = get_district_model("bhaktapur")
    if model is None:
        model = get_district_model('')
    if model is None:
        raise ValueError(f"No model found for district: {district}")
    
    # Forecast the next day's PM2.5 value using the provided lag features(Model Prediction)
    try:
        cols = ['PM25_Lag1', 'PM25_Lag2', 'PM25_Lag3']
        df_input = pd.DataFrame([[x1, x2, x3]], columns=cols)

        # Predict the next day's PM2.5 value using the model
        next_day = float(model.predict(df_input)[0])

    except Exception:
        next_day = float(model.predict([[x1, x2, x3]])[0])

    forecast_values = []
    window = [x1, x2, x3]
    for _ in range(days):
        try:
            
            cols = ['PM25_Lag1', 'PM25_Lag2', 'PM25_Lag3']
            df_input = pd.DataFrame([window], columns=cols)
            # Predict 7 day forecast using the model
            pred = float(model.predict(df_input)[0])
        except Exception:
            pred = float(model.predict([window])[0])
        forecast_values.append(pred)
        window = [window[1], window[2], pred]

    return {
        'next_day': next_day,
        'forecast_values': forecast_values
    }
