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
from google import genai
import os
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


# Load ML model
model = load_model(r"prediction/skin_cancer_model.h5")
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
    # print(type(request.user), request.user)  # Debug

    user = request.user
    records = Prediction.objects.filter(user=user).order_by("-timestamp")

    total_scans = records.count()
    # Updated to check if risk_level starts with "Low Risk" to handle "(benign)" suffix
    normal_results = records.filter(risk_level__startswith="Low Risk").count()
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
def upload_skin_view(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            patient_name = form.cleaned_data["patient_name"]
            scan_type = form.cleaned_data["scan_type"]
            image_file = form.cleaned_data["image_file"]
            
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

# --------------------------
# History View
# --------------------------

@login_required(login_url='login')
def history_view(request):
    filter_val = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '')
    category_val = request.GET.get('category', '')

    scans = Prediction.objects.filter(user=request.user)

    # Search by patient name
    if search_query:
        scans = scans.filter(patient_name__icontains=search_query)

    # Filter by Category (Result)
    if category_val and category_val != 'all':
        scans = scans.filter(result=category_val)

    # Existing Risk Filters
    if filter_val == 'normal':
        scans = scans.filter(risk_level__startswith='Low Risk')
    elif filter_val == 'mild':
        scans = scans.filter(risk_level__startswith='Moderate Risk')
    elif filter_val == 'high':
        # Include both High and Very High risk for 'high' filter
        scans = scans.filter(risk_level__icontains='High Risk')

    context = {
        'scans': scans.order_by('-timestamp'),
        'filter': filter_val,
        'search_query': search_query,
        'category_filter': category_val,
        'categories': class_names  # Pass the list of diagnosis categories
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'history_rows.html', {'scans': context['scans']})

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

# --------------------------
# GEMINI CHATBOT
# --------------------------

def configure_gemini():
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        return genai.Client(api_key=api_key)
    return None

@login_required(login_url="login")
@csrf_exempt
def chat_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message = data.get("message")
            scan_id = data.get("scan_id")
            
            if not message or not scan_id:
                return JsonResponse({"error": "Missing message or scan_id"}, status=400)
            
            scan = Prediction.objects.get(id=scan_id, user=request.user)
            
            client = configure_gemini()
            if not client:
                return JsonResponse({"error": "Gemini API key not configured"}, status=500)
            
            # Construct Prompt
            system_context = f"""
            You are OncoDerma AI, an advanced medical assistant for skin disease analysis. 
            The user is viewing a scan result for a patient named '{scan.patient_name}'.
            The scan diagnosis is '{scan.result}' with a risk level of '{scan.risk_level}'.
            
            Your role is to:
            1. Answer the user's question specifically about this disease/condition.
            2. Provide helpful medical context, symptoms, and general treatment advice.
            3. Be empathetic but professional.
            4. CRITICAL: Always include a disclaimer that you are an AI and this is not a substitute for professional medical advice.
            
            User Question: {message}
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=system_context
            )
            
            return JsonResponse({"response": response.text})
            
        except Prediction.DoesNotExist:
            return JsonResponse({"error": "Scan not found"}, status=404)
        except Exception as e:
            print(f"Chat Error: {e}")
            return JsonResponse({"error": "Failed to process request"}, status=500)
            
    return JsonResponse({"error": "Invalid method"}, status=405)