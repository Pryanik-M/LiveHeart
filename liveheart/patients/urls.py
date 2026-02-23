from django.urls import path
from . import views

app_name = "patients"

urlpatterns = [
    path("new/", views.new_patient_view, name="new_patient"),
    path("history/", views.patient_list_view, name="history"),
    path("delete/<int:patient_id>/", views.delete_patient_view, name="delete_patient"),
]
