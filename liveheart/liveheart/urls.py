from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path("", lambda request: redirect("accounts:dashboard")),
    path("admin/", admin.site.urls),
    path("auth/", include("accounts.urls")),
    path("patients/", include("patients.urls")),

]

