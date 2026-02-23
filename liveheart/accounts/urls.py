from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("verify/", views.verify_2fa_view, name="verify"),
    path("logout/", views.logout_view, name="logout"),
    path("totp/setup/", views.totp_setup, name="totp_setup"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("verify-totp/", views.verify_totp_view, name="verify_totp"),
    path("totp/disable/", views.disable_totp_view, name="disable_totp"),
    path("profile/", views.profile_view, name="profile"),

]
