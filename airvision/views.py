import datetime
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from accounts.models import CustomUser, Prediction, AqiRecord

# Import machine learning predictors and data helpers
from .predictor import predict_pm25_forecast
from .image_predictor import predict_aqi_from_image
from .aqi_data import (
    normalize_city,
    status_class,
    aqi_status,
    make_forecast_item,
    build_city_cards,
    get_city_data,
    ADVICE_MAP,
    MODEL_CITIES,
)

User = get_user_model()

# --- HELPER LOGIC ---

# Dynamically gets the weekday names starting tomorrow (e.g. Thu, Fri, Sat...)
def get_next_7_days_labels():
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    return [weekday_names[(tomorrow + datetime.timedelta(days=i)).weekday()] for i in range(7)]

def _parse_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

# Prepares regression forecast values from input features
def _prepare_model_forecast(city, x1, x2, x3):
    city_key = normalize_city(city)
    if city_key not in MODEL_CITIES:
        return None
    try:
        # Call the Linear Regression predictor logic
        result = predict_pm25_forecast(city_key, x1, x2, x3)
        forecast_values = [round(float(value)) for value in result.get('forecast_7_day', [])]
        labels = get_next_7_days_labels()
        return {
            'next_day': round(float(result.get('next_day', 0))),
            'forecast': [make_forecast_item(labels[i], value) for i, value in enumerate(forecast_values[:7])],
        }
    except Exception:
        return None

# Extracts input features (x1, x2, x3) from GET query params, falling back to defaults if not provided
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


# --- WEB/DJANGO CONTROLLER VIEWS ---

# Landing / Home Page View
def landing_page(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        if image:
            # Predict AQI from the sky image using MobileNet model prediction
            prediction = predict_aqi_from_image(image)
            request.session['filename'] = image.name
            request.session['result'] = f"AQI: {prediction['predicted_aqi']} ({prediction['status']})"
        return redirect('landing_page')
        
    filename = request.session.pop('filename', None)
    result = request.session.pop('result', None)
    # Renders baseline major district cards at the bottom using static values
    city_cards = build_city_cards()
    return render(request, 'landing_page.html', {
        'filename': filename,
        'result': result,
        'city_cards': city_cards,
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
        prediction = predict_aqi_from_image(image)
        
        # Save prediction entry to the database
        Prediction.objects.create(
            user=request.user,
            image=image,
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
    aqi_status_class = (aqi_status_val or 'moderate').lower()
    
    predictions_qs = Prediction.objects.filter(user=request.user).order_by('-created_at')
    predictions_list = []
    for p in predictions_qs:
        sc = (p.status or 'moderate').lower()
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
    if not request.user.is_admin:
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
            
    users = CustomUser.objects.annotate(prediction_count=Count('prediction')).all()
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
        sc = (p.status or 'moderate').lower()
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
def delete_user(request, id):
    user = get_object_or_404(User, id=id)
    user.delete()
    return redirect('admin_dashboard')

def delete_prediction(request, id):
    prediction = get_object_or_404(Prediction, id=id)
    if not request.user.is_authenticated or not request.user.is_admin:
        return redirect('admin_dashboard')
    prediction.delete()
    return redirect('admin_dashboard')

def delete_aqi_record(request, id):
    record = get_object_or_404(AqiRecord, id=id)
    if not request.user.is_authenticated or not request.user.is_admin:
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
        
    data = get_city_data(city_lower)
    last_window = _get_last_window(request, city_lower)
    model_result = _prepare_model_forecast(city_lower, *last_window)
    x1, x2, x3 = last_window
    
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
        dynamic_advice = "The air quality index is forecasted to be " + dynamic_status.lower() + " tomorrow. " + ADVICE_MAP.get(dynamic_status_class, "")
    else:
        dynamic_aqi = data['aqi']
        dynamic_status = data['status']
        dynamic_status_class = status_class(data['status'])
        dynamic_advice = data['advice']

    return render(request, 'aqi.html', {
        'city': city.capitalize(),
        'aqi': dynamic_aqi,
        'pm25': round(x3, 2),
        'status': dynamic_status,
        'status_class': dynamic_status_class,
        'advice': dynamic_advice,
        'forecast': forecast_list,
        'next_day': next_day,
        'forecast_source': 'model',
        'x1': x1,
        'x2': x2,
        'x3': x3,
    })

# Specific City 7-Day Forecast Page View (forecast/city)
def forecast_view(request, city):
    city_lower = normalize_city(city)
    if city_lower not in MODEL_CITIES:
        return _redirect_to_supported_city('forecast')
        
    city_data = get_city_data(city_lower)
    last_window = _get_last_window(request, city_lower)
    model_result = _prepare_model_forecast(city_lower, *last_window)
    x1, x2, x3 = last_window
    
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

    return render(request, 'forecast.html', {
        'city': city.capitalize(),
        'pm25': round(x3, 2),
        'current_aqi': dynamic_aqi,
        'current_status': dynamic_status,
        'current_status_class': dynamic_status_class,
        'forecast': forecast_list,
        'next_day': next_day,
        'forecast_source': 'model',
        'x1': x1,
        'x2': x2,
        'x3': x3,
    })

# Search redirects
def search_view(request):
    city = normalize_city(request.GET.get('city', ''))
    if city not in MODEL_CITIES:
        city = MODEL_CITIES[0] if MODEL_CITIES else 'bhaktapur'
    return redirect(f'/aqi/{city}/')

# External REST API prediction query endpoint (GET /predict/)
@require_GET
def get_prediction(request):
    district = normalize_city(request.GET.get('district', ''))
    x1 = request.GET.get('x1')
    x2 = request.GET.get('x2')
    x3 = request.GET.get('x3')
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
        result = predict_pm25_forecast(district, x1, x2, x3)
        return JsonResponse(result)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)
