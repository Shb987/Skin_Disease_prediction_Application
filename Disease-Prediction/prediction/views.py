from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Prediction
from .forms import UploadForm
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
from django.contrib.auth.models import User

# Load ML model
model = load_model(r"prediction/alzheimer_cnn_model.h5")
class_names = ['Basal Cell Carcinoma', 'Melanoma', 'Benign', 'Squamous Cell Carcinoma'] # Example placeholder names for skin cancer
risk_map = {
    'Benign': 'Low Risk',
    'Basal Cell Carcinoma': 'Moderate Risk',
    'Squamous Cell Carcinoma': 'High Risk',
    'Melanoma': 'Very High Risk'
}



# --------------------------
# AUTH VIEWS
# --------------------------

def register_view(request): 
    if request.method == "POST":
        username = request.POST.get("username").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirmPassword")

        if not username or not password:
            messages.error(request, "Please fill in all required fields.")
            return render(request, "register.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "register.html")

        User.objects.create_user(username=username, password=password)
        messages.success(request, "Registration successful! You can now log in.")
        return redirect("login")

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# --------------------------
# DASHBOARD
# --------------------------

@login_required(login_url="login")
def dashboard_view(request):
    print(type(request.user), request.user)  # Debug

    user = request.user
    records = Prediction.objects.filter(user=user).order_by("-timestamp")

    total_scans = records.count()
    normal_results = records.filter(result="Benign").count()
    risk_detected = total_scans - normal_results
    recent_scans = records[:5]

    context = {
        "username_display": user.username if user.is_authenticated else "Operator",
        "stats": {
            "total_scans": total_scans,
            "normal_results": normal_results,
            "risk_detected": risk_detected,
            "recent_scans": recent_scans,
        }
    }
    return render(request, "dashboard.html", context)


# --------------------------
# UPLOAD MRI
# --------------------------

from django.http import JsonResponse
from io import BytesIO


@login_required(login_url="login")
def upload_mri_view(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            patient_name = form.cleaned_data["patient_name"]
            scan_type = form.cleaned_data["scan_type"]
            image_file = form.cleaned_data["image_file"]
            print(image_file)
            # Wrap uploaded file in BytesIO
            img_bytes = BytesIO(image_file.read())
            img = image.load_img(img_bytes, target_size=(128,128))
            img_array = image.img_to_array(img) / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            predictions = model.predict(img_array)
            print(predictions)
            predicted_index = np.argmax(predictions[0])
            print(predicted_index)
            result = class_names[predicted_index]
            print(result)
            confidence = float(predictions[0][predicted_index])
            risk_level = risk_map[result]
 
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

# --------------------------
# History View
# --------------------------

@login_required(login_url='login')
def history_view(request):
    filter_val = request.GET.get('filter', 'all')
    scans = Prediction.objects.filter(user=request.user)

    if filter_val == 'normal':
        scans = scans.filter(result__icontains='Normal')
    elif filter_val == 'mild':
        scans = scans.filter(result__icontains='Mild')
    elif filter_val == 'high':
        scans = scans.filter(result__icontains='High')

    context = {
        'scans': scans.order_by('-timestamp'),
        'filter': filter_val
    }
    return render(request, 'history.html', context)

from django.shortcuts import render, get_object_or_404

@login_required(login_url='login')
def scan_detail_view(request, scan_id):
    scan = get_object_or_404(Prediction, id=scan_id, user=request.user)
    return render(request, "scan_detail.html", {"scan": scan})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import UserProfile  # if you have extended user

@login_required(login_url="login")
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        request.user.first_name = request.POST.get("first_name", request.user.first_name)
        request.user.last_name = request.POST.get("last_name", request.user.last_name)
        request.user.email = request.POST.get("email", request.user.email)
        profile.phone = request.POST.get("phone", profile.phone)
        profile.institution = request.POST.get("institution", profile.institution)

        request.user.save()
        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(request, "profile.html", {"profile": profile})