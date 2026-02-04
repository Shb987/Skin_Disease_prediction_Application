from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name="login"),
    path('register/', views.register_view, name="register"),
    path('dashboard/', views.dashboard_view, name="dashboard"),
    path('logout/', views.logout_view, name="logout"),
    path('upload/', views.upload_skin_view, name="upload"),
    path('history/', views.history_view, name='history'),
    path('scan/<int:scan_id>/', views.scan_detail_view, name='scan_detail'),  # Optional detail page

    path("chat/", views.chat_view, name="chat"),

]
