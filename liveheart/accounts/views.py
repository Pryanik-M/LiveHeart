import time
import pyotp

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render, redirect

from .decorators import two_factor_required
from .models import TOTPDevice
from .totp import generate_totp_secret, verify_totp
from .utils import generate_2fa_code, hash_code
from .utils_qr import generate_qr_code
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


def login_view(request):
    if request.method == "POST":
        # Очищаем сессию от старых данных
        request.session.flush()

        email = request.POST.get("email")
        password = request.POST.get("password")

        # Ищем пользователя (сначала по email, чтобы получить username)
        user_obj = User.objects.filter(email=email).first()
        if not user_obj:
            return render(request, "accounts/login.html", {"error": "Неверные данные"})

        # Проверяем пароль
        user = authenticate(request, username=user_obj.username, password=password)
        if not user:
            return render(request, "accounts/login.html", {"error": "Неверные данные"})

        # === ЛОГИКА РАЗДЕЛЕНИЯ (TOTP или Email) ===

        # Проверяем, включен ли TOTP у пользователя
        device = getattr(user, "totp_device", None)

        if device and device.confirmed:
            # Если есть TOTP -> СРАЗУ на ввод кода из приложения
            request.session["pre_totp_user_id"] = user.id
            return redirect("accounts:verify_totp")
        else:
            # Если TOTP нет -> отправляем на проверку Email
            request.session["pre_2fa_user_id"] = user.id
            request.session["is_2fa_verified"] = False
            return redirect("accounts:verify")

    return render(request, "accounts/login.html")


def verify_2fa_view(request):
    # Получаем ID пользователя из сессии
    user_id = request.session.get("pre_2fa_user_id")
    if not user_id:
        return redirect("accounts:login")

    user = User.objects.get(id=user_id)
    now = int(time.time())

    # Данные для кулдауна (таймера повторной отправки)
    sent_at = request.session.get("2fa_created_at")
    cooldown = max(0, 60 - (now - sent_at)) if sent_at else 0

    # === ОТПРАВКА КОДА НА ПОЧТУ ===
    if request.method == "POST" and request.POST.get("action") == "send":
        if cooldown > 0:
            return render(request, "accounts/verify.html", {
                "error": f"Подождите {cooldown} сек.",
                "code_sent": True,
                "cooldown": cooldown
            })

        # Генерируем код
        code = generate_2fa_code(settings.TWO_FACTOR_CODE_LENGTH)

        # Сохраняем хэш кода и время в сессию
        request.session["2fa_code_hash"] = hash_code(code)
        request.session["2fa_created_at"] = now

        # Отправляем письмо
        send_mail(
            "Ваш код подтверждения",
            f"Ваш код для входа: {code}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        return render(request, "accounts/verify.html", {"code_sent": True, "cooldown": 60})

    # === ПРОВЕРКА КОДА ===
    if request.method == "POST" and request.POST.get("action") == "verify":
        code = request.POST.get("code")
        stored_hash = request.session.get("2fa_code_hash")

        # Проверка 1: Код не запрашивали
        if not stored_hash:
            return render(request, "accounts/verify.html", {"error": "Сначала запросите код"})

        # Проверка 2: Истекло время жизни кода (например, 5 минут)
        if (now - request.session.get("2fa_created_at", 0)) > 300:
            return render(request, "accounts/verify.html", {"error": "Код устарел, запросите новый"})

        # Проверка 3: Код неверный
        if hash_code(code) != stored_hash:
            return render(request, "accounts/verify.html", {"error": "Неверный код", "code_sent": True})

        # === УСПЕШНЫЙ ВХОД (Email подтвержден) ===
        # Чистим временные данные
        request.session.pop("2fa_code_hash", None)
        request.session.pop("2fa_created_at", None)
        request.session.pop("pre_2fa_user_id", None)

        # Авторизуем пользователя
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        request.session["is_2fa_verified"] = True

        return redirect(settings.LOGIN_REDIRECT_URL)

    return render(request, "accounts/verify.html", {"code_sent": bool(sent_at), "cooldown": cooldown})


def verify_totp_view(request):
    # Берем ID, который мы положили в login_view
    user_id = request.session.get("pre_totp_user_id")

    # Если ID нет, значит пользователь не прошел первый этап
    if not user_id:
        return redirect("accounts:login")

    user = User.objects.get(id=user_id)
    device = getattr(user, "totp_device", None)

    # Если каким-то чудом сюда попал юзер без TOTP
    if not device or not device.confirmed:
        return redirect("accounts:login")

    if request.method == "POST":
        code = request.POST.get("code")

        if verify_totp(device.secret, code):
            # === УСПЕШНЫЙ ВХОД (TOTP подтвержден) ===
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session["is_2fa_verified"] = True

            # Чистим сессию
            request.session.pop("pre_totp_user_id", None)

            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            return render(request, "accounts/verify_totp.html", {"error": "Неверный код"})

    return render(request, "accounts/verify_totp.html")

@login_required
def totp_setup(request):
    device, created = TOTPDevice.objects.get_or_create(
        user=request.user,
        defaults={"secret": generate_totp_secret()},
    )

    if device.confirmed:
        return redirect("accounts:dashboard")

    totp = pyotp.TOTP(device.secret)
    uri = totp.provisioning_uri(
        name=request.user.email,
        issuer_name="LiveHeart",
    )

    qr_code = generate_qr_code(uri)

    if request.method == "POST":
        code = request.POST.get("code")

        if verify_totp(device.secret, code):
            device.confirmed = True
            device.save()
            return redirect("accounts:dashboard")

        return render(
            request,
            "accounts/totp_setup.html",
            {"qr_code": qr_code, "error": "Неверный код"},
        )

    return render(
        request,
        "accounts/totp_setup.html",
        {"qr_code": qr_code},
    )




@two_factor_required
def dashboard(request):
    return render(request, "accounts/dashboard1.html")


@login_required
def profile_view(request):
    user = request.user
    device = getattr(user, "totp_device", None)

    # --- смена пароля ---
    if request.method == "POST" and request.POST.get("action") == "change_password":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if not user.check_password(old_password):
            messages.error(request, "Старый пароль неверный")
        elif new_password != confirm_password:
            messages.error(request, "Пароли не совпадают")
        else:
            try:
                validate_password(new_password, user)
                user.set_password(new_password)
                user.save()
                messages.success(request, "Пароль успешно изменён")
                return redirect("accounts:login")
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)

    return render(
        request,
        "accounts/profile.html",
        {
            "user_obj": user,
            "totp_enabled": bool(device and device.confirmed),
        },
    )

@login_required
def disable_totp_view(request):
    user = request.user
    device = getattr(user, "totp_device", None)

    if not device or not device.confirmed:
        messages.error(request, "Google Authenticator не подключён")
        return redirect("accounts:profile")

    if request.method == "POST":
        code = request.POST.get("code")

        if not code:
            messages.error(request, "Введите код")
            return redirect("accounts:disable_totp")

        if not verify_totp(device.secret, code):
            messages.error(request, "Неверный код")
            return redirect("accounts:disable_totp")

        # ✅ ОТКЛЮЧАЕМ TOTP
        device.delete()

        messages.success(request, "Google Authenticator отключён")
        return redirect("accounts:profile")

    return render(request, "accounts/disable_totp.html")

def logout_view(request):
    logout(request)
    return redirect("accounts:login")
