import datetime
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_GET

from accounts.models import CustomUser, Prediction, AqiRecord

from django.http import JsonResponse
from .predictor import predict_next_day, predict_pm25_forecast


# Import machine learning predictors and data helpers
from .image_predictor import predict_aqi_from_image
from .aqi_data import (
    normalize_city,
    status_class,
    aqi_status,
    pm25_to_aqi,
    make_forecast_item,
    build_city_cards,
    get_city_data,
    load_district_window,
    ADVICE_MAP,
    MODEL_CITIES,
)

User = get_user_model()

# AQI Prediction API Endpoint (GET /predict-aqi/) without login
# predict gareko result webpage ma dekhauxa 
@require_GET
def predict_aqi_ajax(request):

    try:
        x1 = float(request.GET.get("x1"))
        x2 = float(request.GET.get("x2"))
        x3 = float(request.GET.get("x3"))
        district = normalize_city(request.GET.get("district", "") or "")
        if district in ("undefined", "null"):
            district = ""
        days = _parse_int(request.GET.get("days"), 7)

        # Predict next day's PM2.5 and AQI using the district model
        prediction_pm25 = predict_next_day(x1, x2, x3, district=district or None)
        prediction = pm25_to_aqi(prediction_pm25)

        # Predict the next 7 days' PM2.5 and AQI forecast using the district model
        forecast_result = predict_pm25_forecast(district or "lalitpur", x1, x2, x3, days=days)
        forecast_values = [pm25_to_aqi(float(v)) for v in forecast_result.get('forecast_values', [])]
        labels = get_next_days_labels(days)
        forecast_items = [make_forecast_item(labels[i], v) for i, v in enumerate(forecast_values)]

        return JsonResponse({
            "success": True,
            "prediction": prediction,
            "pm25": round(prediction_pm25, 1),
            "forecast": forecast_items
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        })


# Dynamically gets the weekday names starting tomorrow (e.g. Thu, Fri, Sat...)
def get_next_7_days_labels():
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    return [weekday_names[(tomorrow + datetime.timedelta(days=i)).weekday()] for i in range(7)]

def get_next_days_labels(days):
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    return [weekday_names[(tomorrow + datetime.timedelta(days=i)).weekday()] for i in range(days)]

def _parse_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def _parse_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

# Prepares regression forecast values from input features
def _prepare_model_forecast(city, x1, x2, x3, days=7):
    city_key = normalize_city(city)
    if city_key not in MODEL_CITIES:
        return None
    try:
        result = predict_pm25_forecast(city_key, x1, x2, x3, days=days)
        raw_next = float(result.get('next_day', 0))
        forecast_values = [pm25_to_aqi(float(value)) for value in result.get('forecast_values', [])]
        labels = get_next_days_labels(days)
        return {
            'next_day': pm25_to_aqi(raw_next),
            'next_pm25': raw_next,
            'forecast': [make_forecast_item(labels[i], value) for i, value in enumerate(forecast_values[:days])],
        }
    except Exception:
        return None

# Returns dataset PM2.5 values (x1, x2, x3). GET params are ignored.
def _get_model_inputs(city):
    return load_district_window(city)

def _redirect_to_supported_city(page='aqi'):
    return redirect(f'/{page}/{MODEL_CITIES[0]}/')


# --- WEB/DJANGO CONTROLLER VIEWS ---

# Landing / Home Page View
def landing_page(request):
    # if request.method == 'POST':
    #     image = request.FILES.get('image')
    #     if image:
    #         # Predict AQI from the sky image using MobileNet model prediction
    #         prediction = predict_aqi_from_image(image)
    #         request.session['filename'] = image.name
    #         request.session['result'] = f"AQI: {prediction['predicted_aqi']} ({prediction['status']})"
    #     return redirect('landing_page')
        
    # filename = request.session.pop('filename', None)
    # result = request.session.pop('result', None)
    
    # Renders baseline major district cards at the bottom using static values
    city_cards = build_city_cards()

    #Progress Bar Calculations(Landing Page)
    max_aqi = max(c["aqi"] for c in city_cards)

    for c in city_cards:
        c["bar_width"] = round((c["aqi"] / max_aqi) * 100)

    # Insights Calculations(Landing Page)
    worst_city = max(city_cards, key=lambda x: x["aqi"])
    best_city = min(city_cards, key=lambda x: x["aqi"])

    #To calculate the average aqi across all cities, we sum the AQI values and divide by the number of cities
    avg_aqi = round(sum(c["aqi"] for c in city_cards) / len(city_cards))
    
    return render(request, 'landing_page.html', {
        'city_cards': city_cards,
        'worst_city': worst_city,
        'best_city': best_city,
        'avg_aqi': avg_aqi,
    })

# User Dashboard View
@login_required
def user_dashboard(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        image_url = fs.url(filename)
        
        # Predict AQI from the sky image using MobileNet model prediction
        prediction = predict_aqi_from_image(fs.path(filename))
        
        if prediction.get("error"):
            messages.error(request, f"Image prediction failed: {prediction['message']}")
        else:
            Prediction.objects.create(
                user=request.user,
                image=filename,
                predicted_aqi=prediction['predicted_aqi'],
                pm25=None,
                status=prediction['status'],
                health_advice=prediction['health_advice'],
            )
            
            request.session['image_url'] = image_url
            request.session['aqi_result'] = prediction['predicted_aqi']
            request.session['aqi_status'] = prediction['status']
            request.session['health_advice'] = prediction['health_advice']
        
        return redirect('user_dashboard')
        
    image_url = request.session.pop('image_url', None)
    aqi_result = request.session.pop('aqi_result', None)
    aqi_status_val = request.session.pop('aqi_status', None)
    health_advice = request.session.pop('health_advice', None)
    aqi_status_class = status_class(aqi_status_val)
    
    predictions_qs = Prediction.objects.filter(user=request.user).order_by('-created_at')
    predictions_list = []
    for p in predictions_qs:
        sc = status_class(p.status)
        predictions_list.append({
            'id': p.id,
            'aqi': p.predicted_aqi,
            'pm25': p.pm25,
            'pm25_display': f"{p.pm25:.1f} µg/m³" if p.pm25 is not None else 'Unknown',
            'status': p.status,
            'status_class': sc,
            'created_at': p.created_at,
            'image_url': p.image.url if p.image else '',
            'health_advice': p.health_advice or ADVICE_MAP.get(sc, ''),
        })
        
    last_prediction = predictions_list[0] if predictions_list else None
    city_cards = build_city_cards()
    
    context = {
        'image_url': image_url,
        'aqi_result': aqi_result,
        'aqi_status': aqi_status_val,
        'aqi_status_class': aqi_status_class,
        'health_advice': health_advice,
        'predictions': predictions_list,
        'last_prediction': last_prediction,
        'city_cards': city_cards,
    }
    return render(request, 'user.html', context)

# Admin Dashboard View
@login_required
def admin_dashboard(request):
    if not (request.user.is_admin or request.user.is_superuser):
        return redirect('user_dashboard')
    if request.method == 'POST':
        city = request.POST.get('city', '').strip()
        location = request.POST.get('location', '').strip()
        aqi = request.POST.get('aqi', '').strip()
        status = request.POST.get('status', '').strip()
        note = request.POST.get('note', '').strip()
        if city and aqi.isdigit() and status:
            AqiRecord.objects.create(
                city=city,
                location=location,
                aqi=int(aqi),
                status=status,
                note=note,
            )
            messages.success(request, 'AQI record added successfully.')
            return redirect('admin_dashboard')
            
    users = CustomUser.objects.annotate(prediction_count=Count('prediction')).order_by('-date_joined')
    total_users = users.count()
    total_admins = CustomUser.objects.filter(is_admin=True).count()
    city_cards = build_city_cards()
    district_data = [
        {'district': card['city'], 'aqi': card['aqi'], 'status': card['status']}
        for card in city_cards
    ]
    
    aqi_records_qs = AqiRecord.objects.order_by('-created_at')
    aqi_records = []
    for record in aqi_records_qs:
        aqi_records.append({
            'id': record.id,
            'city': record.city,
            'location': record.location,
            'aqi': record.aqi,
            'status': record.status,
            'status_class': record.status.lower(),
            'note': record.note,
            'date': record.created_at.strftime('%b %d, %Y') if record.created_at else '',
        })
        
    predictions_qs = Prediction.objects.select_related('user').order_by('-created_at')
    prediction_logs = []
    for p in predictions_qs:
        sc = status_class(p.status)
        prediction_logs.append({
            'id': p.id,
            'image_url': p.image.url if p.image else '',
            'username': p.user.username,
            'aqi': p.predicted_aqi,
            'status': p.status,
            'status_class': sc,
            'date': p.created_at.strftime('%b %d, %Y') if p.created_at else '',
            'health_advice': p.health_advice or ADVICE_MAP.get(sc, ''),
        })
        
    context = {
        'users': users,
        'total_users': total_users,
        'total_admins': total_admins,
        'total_predictions': Prediction.objects.count(),
        'total_districts': len(city_cards),
        'uploaded_images': Prediction.objects.count(),
        'district_data': district_data,
        'aqi_records': aqi_records,
        'prediction_logs': prediction_logs,
    }
    return render(request, 'admin.html', context)

# Admin Operations
@login_required
def delete_user(request, id):
    if not (request.user.is_admin or request.user.is_superuser):
        return redirect('user_dashboard')
    user = get_object_or_404(User, id=id)
    user.delete()
    messages.success(request, "User deleted successfully.")
    return redirect(reverse('admin_dashboard') + '?section=users')

@login_required
def delete_prediction(request, id):
    prediction = get_object_or_404(Prediction, id=id)
    if request.user.is_admin or request.user.is_superuser:
        prediction.delete()
        messages.success(request, "Prediction deleted successfully.")
        return redirect(reverse('admin_dashboard') + '?section=logs')
    if prediction.user == request.user:
        prediction.delete()
        messages.success(request, "Prediction deleted successfully.")
        return redirect(reverse('user_dashboard') + '?section=history')
    return redirect('user_dashboard')

@login_required
def delete_aqi_record(request, id):
    record = get_object_or_404(AqiRecord, id=id)
    if not (request.user.is_admin or request.user.is_superuser):
        return redirect('admin_dashboard')
    record.delete()
    return redirect('admin_dashboard')

# Prediction Details Modal View
def prediction_detail(request, id):
    prediction = get_object_or_404(Prediction, id=id)
    sc = (prediction.status or 'moderate').lower()
    advice = prediction.health_advice or ADVICE_MAP.get(sc, '')
    return render(request, 'prediction_detail.html', {
        'prediction': prediction,
        'status_class': sc,
        'advice': advice,
        'user_is_admin': request.user.is_authenticated and request.user.is_admin,
    })

# --- DYNAMIC FORECAST & AQI VIEWS (Linear Regression Integration) ---

# Specific City AQI Page View (aqi/city)

def aqi_view(request, city):
    city_lower = normalize_city(city)
    if city_lower not in MODEL_CITIES:
        return _redirect_to_supported_city('aqi')
    
    x1, x2, x3 = _get_model_inputs(city_lower)

    data = get_city_data(city_lower)
    days = _parse_int(request.GET.get('days'), 7)

    model_result = _prepare_model_forecast(city_lower, x1, x2, x3, days=days)

    if model_result:
        forecast_list = model_result['forecast']
        next_day = model_result['next_day']
    else:
        forecast_list = []
        next_day = None

    # Calculate dynamic AQI/status from predicted PM2.5 next day value
    if next_day is not None:
        dynamic_aqi = round(next_day)
        dynamic_status = aqi_status(dynamic_aqi)
        dynamic_status_class = status_class(dynamic_status)
        dynamic_advice = ADVICE_MAP.get(dynamic_status_class, "Monitor air quality conditions.")
    else:
        pm25_val = data.get('pm25', 0)
        dynamic_aqi = pm25_to_aqi(pm25_val)
        dynamic_status = aqi_status(dynamic_aqi)
        dynamic_status_class = status_class(dynamic_status)
        dynamic_advice = ADVICE_MAP.get(dynamic_status_class, "Monitor air quality conditions.")

    return render(request, 'aqi.html', {
        'city': city.capitalize(),
        'aqi': dynamic_aqi,
        'pm25': round(model_result['next_pm25'], 2) if model_result else round(x3, 2),
        'status': dynamic_status,
        'status_class': dynamic_status_class,
        'advice': dynamic_advice,
        'forecast': forecast_list,
        'next_day': next_day,
        'forecast_source': 'model',
        'x1': x1,
        'x2': x2,
        'x3': x3,
        'days': days,
    })

# Specific City 7-Day Forecast Page View (forecast/city)

def forecast_view(request, city):
    city_lower = normalize_city(city)
    if city_lower not in MODEL_CITIES:
        return _redirect_to_supported_city('forecast')
    
    x1, x2, x3 = _get_model_inputs(city_lower)

    city_data = get_city_data(city_lower)
    days = _parse_int(request.GET.get('days'), 7)

    model_result = _prepare_model_forecast(city_lower, x1, x2, x3, days=days)

    if model_result:
        forecast_list = model_result['forecast']
        next_day = model_result['next_day']
    else:
        forecast_list = []
        next_day = None

    # Calculate dynamic AQI/status from predicted PM2.5 next day value
    if next_day is not None:
        dynamic_aqi = round(next_day)
        dynamic_status = aqi_status(dynamic_aqi)
        dynamic_status_class = status_class(dynamic_status)
    else:
        dynamic_aqi = city_data['aqi']
        dynamic_status = city_data['status']
        dynamic_status_class = status_class(city_data['status'])

    # Prepend today's AQI as the first forecast card
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    today_label = weekday_names[datetime.date.today().weekday()]
    today_item = {"day": today_label, "aqi": dynamic_aqi, "status": dynamic_status, "status_class": dynamic_status_class}
    forecast_list = [today_item] + (forecast_list[:days-1] if len(forecast_list) >= days else forecast_list)

    return render(request, 'forecast.html', {
        'city': city.capitalize(),
        'pm25': round(model_result['next_pm25'], 2) if model_result else round(x3, 2),
        'current_aqi': dynamic_aqi,
        'current_status': dynamic_status,
        'current_status_class': dynamic_status_class,
        'forecast': forecast_list,
        'next_day': next_day,
        'forecast_source': 'model',
        'x1': x1,
        'x2': x2,
        'x3': x3,
        'days': days,
    })

# Search redirects
def search_view(request):
    city = normalize_city(request.GET.get('city', ''))
    if city not in MODEL_CITIES:
        city = MODEL_CITIES[0] if MODEL_CITIES else 'lalitpur'
    return redirect(f'/aqi/{city}/')

# External REST API prediction query endpoint (GET /predict/)
@require_GET
def get_prediction(request):
    district = normalize_city(request.GET.get('district', ''))
    x1 = request.GET.get('x1')
    x2 = request.GET.get('x2')
    x3 = request.GET.get('x3')
    days = _parse_int(request.GET.get('days'), 7)
    if not district:
        return JsonResponse({"error": "district required"}, status=400)
    try:
        x1 = float(x1) if x1 is not None else 0.0
        x2 = float(x2) if x2 is not None else 0.0
        x3 = float(x3) if x3 is not None else 0.0
    except ValueError:
        return JsonResponse({"error": "x1, x2, x3 must be numeric"}, status=400)
    try:
        # Predict PM2.5 time-series recursively
        result = predict_pm25_forecast(district, x1, x2, x3, days=days)
        return JsonResponse(result)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)


