from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.contrib.auth import get_user_model

from accounts.models import CustomUser, Prediction, AqiRecord
from .aqi_data import build_city_cards, ADVICE_MAP

User = get_user_model()


def landing_page(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        if image:
            request.session['filename'] = image.name
            request.session['result'] = "AQI: 150 (Unhealthy)"
        return redirect('landing_page')

    filename = request.session.pop('filename', None)
    result = request.session.pop('result', None)
    city_cards = build_city_cards()
    return render(request, 'landing_page.html', {
        'filename': filename,
        'result': result,
        'city_cards': city_cards,
    })


@login_required
def user_dashboard(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        image_url = fs.url(filename)

        predicted_aqi = 150
        status = "Unhealthy"
        health_advice = "Reduce outdoor activities. Wear a mask when going outside."

        Prediction.objects.create(
            user=request.user,
            image=image,
            predicted_aqi=predicted_aqi,
            pm25=None,
            status=status,
            health_advice=health_advice,
        )

        request.session['image_url'] = image_url
        request.session['aqi_result'] = predicted_aqi
        request.session['aqi_status'] = status
        request.session['health_advice'] = health_advice
        return redirect('user_dashboard')

    image_url = request.session.pop('image_url', None)
    aqi_result = request.session.pop('aqi_result', None)
    aqi_status = request.session.pop('aqi_status', None)
    health_advice = request.session.pop('health_advice', None)
    aqi_status_class = (aqi_status or 'moderate').lower()

    predictions_qs = Prediction.objects.filter(
        user=request.user
    ).order_by('-created_at')

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
        'aqi_status': aqi_status,
        'aqi_status_class': aqi_status_class,
        'health_advice': health_advice,
        'predictions': predictions_list,
        'last_prediction': last_prediction,
        'city_cards': city_cards,
    }
    return render(request, 'user.html', context)


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

    users = CustomUser.objects.annotate(
        prediction_count=Count('prediction')
    ).all()
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
