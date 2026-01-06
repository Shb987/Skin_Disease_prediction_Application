from django import forms

class UploadForm(forms.Form):
    patient_name = forms.CharField(max_length=100)
    scan_type = forms.CharField(max_length=50)
    image_file = forms.FileField()
