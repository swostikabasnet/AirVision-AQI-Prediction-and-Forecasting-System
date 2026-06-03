from django.contrib import admin
from .models import CustomUser
from .models import Prediction
from .models import AqiRecord

#CustomUser and Prediction models lai admin interface ma register garna lai
admin.site.register(CustomUser)# registered users lai admin interface ma dekhauna lai
admin.site.register(Prediction) # registered predictions lai admin interface ma dekhauna lai
admin.site.register(AqiRecord) # manual AQI records for admin
