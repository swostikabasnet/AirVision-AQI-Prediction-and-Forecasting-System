from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .predictor import predict_pm25
from .aqi_data import normalize_city


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
        result = predict_pm25(district, x1, x2, x3)
        return JsonResponse(result)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)
