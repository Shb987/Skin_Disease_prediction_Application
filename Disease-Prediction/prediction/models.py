from django.db import models
from django.contrib.auth.models import User  # Use Django's built-in User

class Prediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    patient_name = models.CharField(max_length=100)
    scan_type = models.CharField(max_length=50)
    result = models.CharField(max_length=50)
    confidence = models.FloatField()
    risk_level = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    image_file = models.FileField(upload_to='uploads/', default='default.jpg')

    def __str__(self):
        return f"{self.patient_name} - {self.result} ({self.timestamp})"


from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True, null=True)
    institution = models.CharField(max_length=255, blank=True, null=True)
    photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)
    email_notifications = models.BooleanField(default=True)
    research_participation = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username