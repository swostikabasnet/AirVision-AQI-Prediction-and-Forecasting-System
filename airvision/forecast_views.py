from django.shortcuts import render, redirect
from .aqi_data import (
    normalize_city,
    get_city_data,
    DAY_LABELS,
    make_forecast_item,
    status_class,
    CITY_TO_MODEL_NAME,
    MODEL_CITIES,
)
from .predictor import predict_pm25


def _parse_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _prepare_model_forecast(city, x1, x2, x3):
    city_key = normalize_city(city)
    if city_key not in CITY_TO_MODEL_NAME:
        return None

    try:
        result = predict_pm25(city_key, x1, x2, x3)
        forecast_values = [round(float(value)) for value in result.get('forecast_7_day', [])]
        return {
            'next_day': round(float(result.get('next_day', 0))),
            'forecast': [make_forecast_item(DAY_LABELS[i], value) for i, value in enumerate(forecast_values[:7])],
        }
    except Exception:
        return None


def _get_last_window(request, city):
    x1 = _parse_float(request.GET.get('x1'), None)
    x2 = _parse_float(request.GET.get('x2'), None)
    x3 = _parse_float(request.GET.get('x3'), None)
    if x1 is not None and x2 is not None and x3 is not None:
        return x1, x2, x3

    city_data = get_city_data(city)
    pm25 = city_data.get('pm25', 40)
    return pm25, max(pm25 - 5, 1), max(pm25 - 10, 1)


def _redirect_to_supported_city(page='aqi'):
    return redirect(f'/{page}/{MODEL_CITIES[0]}/')


def aqi_view(request, city):
    city_lower = normalize_city(city)
    if city_lower not in CITY_TO_MODEL_NAME:
        return _redirect_to_supported_city('aqi')

    data = get_city_data(city_lower)
    last_window = _get_last_window(request, city_lower)
    model_result = _prepare_model_forecast(city_lower, *last_window)
    pm25 = last_window[2]

    if not model_result:
        forecast = []
        next_day = None
    else:
        forecast = model_result['forecast']
        next_day = model_result['next_day']

    return render(request, 'aqi.html', {
        'city': city.capitalize(),
        'aqi': data['aqi'],
        'pm25': pm25,
        'status': data['status'],
        'status_class': status_class(data['status']),
        'advice': data['advice'],
        'forecast': forecast,
        'next_day': next_day,
        'forecast_source': 'model',
    })


def forecast_view(request, city):
    city_lower = normalize_city(city)
    if city_lower not in CITY_TO_MODEL_NAME:
        return _redirect_to_supported_city('forecast')

    city_data = get_city_data(city_lower)
    last_window = _get_last_window(request, city_lower)
    model_result = _prepare_model_forecast(city_lower, *last_window)
    pm25 = last_window[2]

    if not model_result:
        forecast = []
        next_day = None
    else:
        forecast = model_result['forecast']
        next_day = model_result['next_day']

    return render(request, 'forecast.html', {
        'city': city.capitalize(),
        'pm25': pm25,
        'current_aqi': city_data['aqi'],
        'current_status': city_data['status'],
        'current_status_class': status_class(city_data['status']),
        'forecast': forecast,
        'next_day': next_day,
        'forecast_source': 'model',
    })


def search_view(request):
    city = normalize_city(request.GET.get('city', ''))
    if city not in CITY_TO_MODEL_NAME:
        city = MODEL_CITIES[0] if MODEL_CITIES else 'bhaktapur'
    return redirect(f'/aqi/{city}/')
