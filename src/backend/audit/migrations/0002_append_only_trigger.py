"""Makes security_log append-only at the database level.

Django has no model-level way to express a trigger, so this migration runs
raw SQL. It was created with:
    python manage.py makemigrations audit --empty --name append_only_trigger
"""
from django.db import migrations

CREATE_TRIGGERS = """
CREATE FUNCTION security_log_reject_change() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'security_log is append-only (% rejected)', TG_OP;
END;
$$;

-- Fires once per row affected by an UPDATE or DELETE.
CREATE TRIGGER security_log_no_update_delete
    BEFORE UPDATE OR DELETE ON security_log
    FOR EACH ROW EXECUTE FUNCTION security_log_reject_change();

-- TRUNCATE doesn't touch individual rows, so it needs a statement-level trigger.
CREATE TRIGGER security_log_no_truncate
    BEFORE TRUNCATE ON security_log
    FOR EACH STATEMENT EXECUTE FUNCTION security_log_reject_change();
"""

DROP_TRIGGERS = """
DROP TRIGGER IF EXISTS security_log_no_truncate ON security_log;
DROP TRIGGER IF EXISTS security_log_no_update_delete ON security_log;
DROP FUNCTION IF EXISTS security_log_reject_change();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(CREATE_TRIGGERS, reverse_sql=DROP_TRIGGERS),
    ]
