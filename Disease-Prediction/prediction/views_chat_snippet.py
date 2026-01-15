import google.generativeai as genai
import os
import json
from django.views.decorators.csrf import csrf_exempt

# Helper for Gemini Config
def configure_gemini():
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)
        return True
    return False

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
            
            if not configure_gemini():
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
            
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(system_context)
            
            return JsonResponse({"response": response.text})
            
        except Prediction.DoesNotExist:
            return JsonResponse({"error": "Scan not found"}, status=404)
        except Exception as e:
            print(f"Chat Error: {e}")
            return JsonResponse({"error": "Failed to process request"}, status=500)
            
    return JsonResponse({"error": "Invalid method"}, status=405)
