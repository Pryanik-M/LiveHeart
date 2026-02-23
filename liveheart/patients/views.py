from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .models import *
from .utils import generate_docx, generate_xlsx, generate_pdf
from django.utils.dateparse import parse_datetime
from django.utils import timezone



def to_float(val):
    try:
        return float(val.replace(',', '.')) if val else None
    except:
        return None

def to_int(val, default=0):
    try:
        return int(val) if val and str(val).strip() else default
    except:
        return default


@login_required
def new_patient_view(request):
    if request.method == "POST":
        with transaction.atomic():
            # 1. Основные данные + ПРИВЯЗКА К ВРАЧУ (request.user)
            patient = Patient.objects.create(
                user=request.user,  # <--- ВОТ ГЛАВНОЕ ИЗМЕНЕНИЕ
                full_name=request.POST.get("full_name")
            )

            raw_date = request.POST.get("exam_datetime")
            exam_dt = parse_datetime(raw_date) if raw_date else timezone.now()

            # Если дата "наивная" (без часового пояса), делаем её осознанной
            if exam_dt and timezone.is_naive(exam_dt):
                exam_dt = timezone.make_aware(exam_dt)

            exam = Examination.objects.create(
                patient=patient,
                exam_datetime=exam_dt,
                age=request.POST.get("age") or None,
                height=to_float(request.POST.get("height")),
                weight=to_float(request.POST.get("weight")),
                bmi=to_float(request.POST.get("bmi")),
                bsa=to_float(request.POST.get("bsa")),
                hr=request.POST.get("hr") or None
            )

            # 2. Аорта
            Aorta.objects.create(
                examination=exam,
                diameter=to_float(request.POST.get("diametr_aorta")),
                valve_opening=to_float(request.POST.get("opening_aortic_valve")),
                is_enabled=request.POST.get("aorta_enabled") == "on"
            )

            # 3. Аортальный клапан
            AorticValve.objects.create(
                examination=exam,
                psk=to_float(request.POST.get("psk")),
                grad_max=to_float(request.POST.get("max_gradient")),
                grad_mean=to_float(request.POST.get("avr_gradient")),
                regurgitation=int(request.POST.get("regurgitaciya_1", 0)),
                area=to_float(request.POST.get("ploshad_open_clapana"))
            )

            # 4. Левый желудочек
            LeftVentricle.objects.create(
                examination=exam,
                ivsd=to_float(request.POST.get("mjp")),
                edd=to_float(request.POST.get("kdr")),
                esd=to_float(request.POST.get("kcr")),
                pw=to_float(request.POST.get("zclj")),
                edv=to_float(request.POST.get("kdo")),
                esv=to_float(request.POST.get("kco")),
                hr=request.POST.get("hr")
            )

            # 5. Остальные камеры
            OtherChambers.objects.create(
                examination=exam,
                la=to_float(request.POST.get("left_pred")),
                ra=to_float(request.POST.get("right_pred")),
                rv=to_float(request.POST.get("right_jel")),
                lav=to_float(request.POST.get("obem_lp"))
            )

            # 6. Митральный клапан
            MitralValve.objects.create(
                examination=exam,
                e=to_float(request.POST.get("e")),
                a=to_float(request.POST.get("a")),
                grad_max=to_float(request.POST.get("max_gradient")),
                dte=to_float(request.POST.get("dte")),
                ivrt=to_float(request.POST.get("ivrt")),
                reg=int(request.POST.get("regurgitaciya_2", 0))
            )

            # 7. Трикуспидальный клапан
            TricuspidValve.objects.create(
                examination=exam,
                e=to_float(request.POST.get("trikuspid_e")),
                a=to_float(request.POST.get("trikuspid_a")),
                grad_max=to_float(request.POST.get("trikuspid_max_gradiend")),
                tapse=to_float(request.POST.get("tapse")),
                reg=int(request.POST.get("regurgitaciya_3", 0))
            )

            # 8. Лёгочная артерия
            PulmonaryArtery.objects.create(
                examination=exam,
                diameter=to_float(request.POST.get("diametr_stvola_la")),
                grad_max=to_float(request.POST.get("max_gradient")),
                velocity=to_float(request.POST.get("speed")),
                at=to_float(request.POST.get("at")),
                et=to_float(request.POST.get("et")),
                reg=int(request.POST.get("regurgitaciya_4", 0)),
                ivc=to_float(request.POST.get("npv"))
            )

            # 9. Сегменты
            for i in range(1, 18):
                state = request.POST.get(f"segment_{i}", 0)
                MyocardialSegment.objects.create(
                    examination=exam,
                    segment_number=i,
                    state=int(state)
                )

            # ЭКСПОРТ ФАЙЛОВ
            export_type = request.POST.get('export_type')
            print(f"DEBUG: Export type is {export_type}")
            if export_type in ['docx', 'xlsx', 'pdf']:
                exam.refresh_from_db()# Получаем тип из скрытого поля
                if export_type == 'docx':
                    return generate_docx(exam)
                elif export_type == 'xlsx':
                    return generate_xlsx(exam)
                elif export_type == 'pdf':
                    return generate_pdf(exam)

        # Перенаправление в личный кабинет (dashboard)
        return redirect("accounts:dashboard")

    return render(request, "patients/new_patient.html", {"segments": range(1, 18)})


@login_required
def patient_list_view(request):
    # Получаем пациентов, привязанных ТОЛЬКО к текущему пользователю
    # select_related помогает загрузить данные быстрее одним запросом
    patients = Patient.objects.filter(user=request.user).order_by('full_name')

    # Мы можем передать список пациентов в шаблон
    return render(request, "patients/history_patient.html", {"patients": patients})


@login_required
def delete_patient_view(request, patient_id):
    if request.method == "POST":
        patient = Patient.objects.filter(
            id=patient_id,
            user=request.user  # защита: удалять можно только своих
        ).first()

        if patient:
            patient.delete()

    return redirect("patients:history")