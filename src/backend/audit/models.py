from django.conf import settings
from django.db import models
from django.db.models.functions import Now


# SecurityLog model to store security-related events in the database
class SecurityLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="user_id",
        related_name="+",
    )
    event_type = models.CharField(max_length=50)
    event_desc = models.BinaryField()           # encrypted details
    event_time = models.DateTimeField(db_default=Now())

    class Meta:
        db_table = "security_log"
        indexes = [models.Index(fields=["event_time"], name="security_log_time")]


# Model to store rate limit hits for various scopes (e.g., login attempts, MFA attempts)
class RateLimitHit(models.Model):
    ip_address = models.GenericIPAddressField()
    scope = models.CharField(max_length=20)
    created = models.DateTimeField(db_default=Now())

    class Meta:
        db_table = "rate_limit_hits"
        indexes = [
            models.Index(fields=["scope", "ip_address", "created"], name="rate_limit_lookup"),
        ]