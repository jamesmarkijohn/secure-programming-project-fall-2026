from django.conf import settings
from django.db import models
from django.db.models.functions import Now


class SecurityLog(models.Model):
    """Append-only: a database trigger rejects UPDATE, DELETE, and TRUNCATE.

    Events with no associated user are attributed to the system account.
    """

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
