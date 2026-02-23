from django.db import models
from django.contrib.auth.models import User  # Импортируем модель пользователя


class Patient(models.Model):
    # Привязываем пациента к конкретному врачу (пользователю)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="patients")
    full_name = models.CharField(max_length=255)

    def __str__(self):
        return self.full_name


class Examination(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    # Исправляем ошибку: добавляем null=True, blank=True, чтобы дата не вызывала ошибку, если не заполнена
    exam_datetime = models.DateTimeField(null=True, blank=True)

    age = models.IntegerField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    bmi = models.FloatField(null=True, blank=True)
    bsa = models.FloatField(null=True, blank=True)
    hr = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


# Группы данных (Аорта, Клапаны и т.д.)
class Aorta(models.Model):
    examination = models.OneToOneField(Examination, on_delete=models.CASCADE)
    diameter = models.FloatField(null=True, blank=True)
    valve_opening = models.FloatField(null=True, blank=True)
    is_enabled = models.BooleanField(default=True)


class AorticValve(models.Model):
    examination = models.OneToOneField(Examination, on_delete=models.CASCADE)
    psk = models.FloatField(null=True, blank=True)
    grad_max = models.FloatField(null=True, blank=True)
    grad_mean = models.FloatField(null=True, blank=True)
    regurgitation = models.IntegerField(default=0)
    area = models.FloatField(null=True, blank=True)
    is_enabled = models.BooleanField(default=True)


class LeftVentricle(models.Model):
    examination = models.OneToOneField(Examination, on_delete=models.CASCADE)
    ivsd = models.FloatField(null=True, blank=True)
    edd = models.FloatField(null=True, blank=True)
    esd = models.FloatField(null=True, blank=True)
    pw = models.FloatField(null=True, blank=True)
    edv = models.FloatField(null=True, blank=True)
    esv = models.FloatField(null=True, blank=True)
    hr = models.IntegerField(null=True, blank=True)
    is_enabled = models.BooleanField(default=True)


class OtherChambers(models.Model):
    examination = models.OneToOneField(Examination, on_delete=models.CASCADE)
    la = models.FloatField(null=True, blank=True)
    ra = models.FloatField(null=True, blank=True)
    rv = models.FloatField(null=True, blank=True)
    lav = models.FloatField(null=True, blank=True)
    is_enabled = models.BooleanField(default=True)


class MitralValve(models.Model):
    examination = models.OneToOneField(Examination, on_delete=models.CASCADE)
    e = models.FloatField(null=True, blank=True)
    a = models.FloatField(null=True, blank=True)
    grad_max = models.FloatField(null=True, blank=True)
    dte = models.FloatField(null=True, blank=True)
    ivrt = models.FloatField(null=True, blank=True)
    reg = models.IntegerField(default=0)
    is_enabled = models.BooleanField(default=True)


class TricuspidValve(models.Model):
    examination = models.OneToOneField(Examination, on_delete=models.CASCADE)
    e = models.FloatField(null=True, blank=True)
    a = models.FloatField(null=True, blank=True)
    grad_max = models.FloatField(null=True, blank=True)
    tapse = models.FloatField(null=True, blank=True)
    reg = models.IntegerField(default=0)
    is_enabled = models.BooleanField(default=True)


class PulmonaryArtery(models.Model):
    examination = models.OneToOneField(Examination, on_delete=models.CASCADE)
    diameter = models.FloatField(null=True, blank=True)
    grad_max = models.FloatField(null=True, blank=True)
    velocity = models.FloatField(null=True, blank=True)
    at = models.FloatField(null=True, blank=True)
    et = models.FloatField(null=True, blank=True)
    reg = models.IntegerField(default=0)
    ivc = models.FloatField(null=True, blank=True)
    is_enabled = models.BooleanField(default=True)


class MyocardialSegment(models.Model):
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name="segments")
    segment_number = models.PositiveSmallIntegerField()
    state = models.PositiveSmallIntegerField(default=0)