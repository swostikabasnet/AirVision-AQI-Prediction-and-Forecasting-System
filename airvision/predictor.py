from .district_predictor import get_district_model, predict_pm25_forecast

def predict_next_day(x1, x2, x3, district=None):
    """
    Predict next day's PM2.5 value using previous 3 days, district-wise.
    """
    model = get_district_model(district or "bhaktapur")
    if model is None:
        model = get_district_model("bhaktapur")
    if model is None:
        model = get_district_model('')
    if model is None:
        raise ValueError("Model not found")

    try:
        import pandas as pd
        cols = ['PM25_Lag1', 'PM25_Lag2', 'PM25_Lag3']
        df_input = pd.DataFrame([[x1, x2, x3]], columns=cols)
        prediction = model.predict(df_input)
    except Exception:
        prediction = model.predict([[x1, x2, x3]])
        
    return round(float(prediction[0]), 2)