from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_admin = models.BooleanField(default=False)

#Prediction model to store user predictions
class Prediction(models.Model):

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE
    )

    image = models.ImageField(
        upload_to=''
    )

    predicted_aqi = models.IntegerField()
    pm25 = models.FloatField(null=True, blank=True)

    status = models.CharField(
        max_length=50
    )
    health_advice = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"{self.user.username} - {self.predicted_aqi}"


class AqiRecord(models.Model):
    city = models.CharField(max_length=120)
    location = models.CharField(max_length=160, blank=True, default='')
    aqi = models.IntegerField()
    status = models.CharField(max_length=50)
    note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.city} - {self.aqi}"
