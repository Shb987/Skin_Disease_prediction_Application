from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ..models import Prediction
from ..forms import UploadForm
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
from io import BytesIO

# Load ML model
# Note: Path is relative to the project root (where manage.py is run)
try:
    model = load_model(r"prediction/skin_cancer_model.h5")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# model2 =load_model(r"unet_isic2018.h5")

class_names = [
    'Melanocytic nevi (nv)', 
    'Melanoma (mel)', 
    'Benign keratosis-like lesions (bkl)',
    'Basal cell carcinoma (bcc)',
    'Actinic keratoses (akiec)',
    'Vascular lesions (vasc)',
    'Dermatofibroma (df)'
]

risk_map = {
    'Melanocytic nevi (nv)': 'Low Risk (benign)',
    'Melanoma (mel)': 'Very High Risk (life-threatening malignant tumor)',
    'Benign keratosis-like lesions (bkl)': 'Low Risk',
    'Basal cell carcinoma (bcc)': 'High Risk (malignant but slow growing)',
    'Actinic keratoses (akiec)': 'Moderate Risk (pre-cancerous lesion)',
    'Vascular lesions (vasc)': 'Low Risk (benign)',
    'Dermatofibroma (df)': 'Low Risk (benign)'
}

# --------------------------
# UPLOAD MRI
# --------------------------

@login_required(login_url="login")
def upload_skin_view(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            patient_name = form.cleaned_data["patient_name"]
            scan_type = form.cleaned_data["scan_type"]
            image_file = form.cleaned_data["image_file"]
            
            if model is None:
                messages.error(request, "Model not loaded properly.")
                return redirect("dashboard")

            # Wrap uploaded file in BytesIO
            img_bytes = BytesIO(image_file.read())
            img = image.load_img(img_bytes, target_size=(28, 28))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            # img_array = img_array / 255.0  # Rescale to [0, 1] as done in training

            predictions = model.predict(img_array)
            predicted_index = np.argmax(predictions[0])
            print(predictions)
            result = class_names[predicted_index]
            confidence = float(predictions[0][predicted_index])
            risk_level = risk_map.get(result, "Unknown Risk")
 
            # Save prediction
            Prediction.objects.create(
                user=request.user,
                patient_name=patient_name,
                scan_type=scan_type,
                result=result,
                confidence=confidence * 100,
                risk_level=risk_level,
                image_file=image_file
            )

            # Return JSON if AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    "diagnosis": result,
                    "confidence": round(confidence*100, 2),
                    "risk_level": risk_level
                })

            messages.success(request, f"Scan analyzed: {result} ({confidence*100:.2f}%)")
            return redirect("dashboard")

        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"error": "Form invalid"}, status=400)

    else:
        form = UploadForm()

    return render(request, "upload.html", {"form": form})
