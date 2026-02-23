from django.conf import settings
from django.db import models


class TOTPDevice(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="totp_device",
    )
    secret = models.CharField(max_length=32)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"TOTP for {self.user}"
