from django.contrib import admin
from .models import Prediction, UserProfile

# Register your models here.

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient_name', 'scan_type', 'result', 'confidence', 'risk_level', 'timestamp', 'image_file')
    list_filter = ('scan_type', 'result', 'risk_level', 'timestamp')
    search_fields = ('patient_name', 'result', 'scan_type')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'institution', 'email_notifications', 'research_participation')
    list_filter = ('institution', 'email_notifications', 'research_participation')
    search_fields = ('user__username', 'user__email', 'phone', 'institution')
