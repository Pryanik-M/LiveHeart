from django.conf import settings
from django.shortcuts import redirect


def two_factor_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        if not request.session.get("is_2fa_verified"):
            return redirect("accounts:verify")

        return view_func(request, *args, **kwargs)

    return wrapper
