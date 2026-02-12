from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Prediction
from .prediction_views import class_names # Import shared constants

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


@login_required(login_url='login')
def scan_detail_view(request, scan_id):
    scan = get_object_or_404(Prediction, id=scan_id, user=request.user)
    return render(request, "scan_detail.html", {"scan": scan})
