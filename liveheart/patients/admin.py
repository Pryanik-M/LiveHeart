from django.contrib import admin
from .models import *
admin.site.register([Patient, Examination, Aorta, AorticValve, LeftVentricle, OtherChambers, MitralValve, TricuspidValve, PulmonaryArtery, MyocardialSegment])