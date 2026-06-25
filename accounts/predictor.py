import os
import joblib

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "models",
    "aqi_pm25_predictor.pkl"
)

model = joblib.load(MODEL_PATH)

# Predicts next day's AQI based on current AQI, PM2.5 values
def predict_next_day(x1, x2, x3):
    prediction = model.predict([[x1, x2, x3]])
    return round(float(prediction[0]), 2)