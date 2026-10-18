# Built from the repo root (see docker-compose.yml).
# Same PostgreSQL version as database, pg_dump matches the server
FROM postgres:18-alpine

# Using age for file encryption
RUN apk add --no-cache age \
    && mkdir /backups \
    && chown postgres:postgres /backups

COPY src/backup/backup.sh /usr/local/bin/backup.sh
RUN chmod 0755 /usr/local/bin/backup.sh

# Run as the unprivileged postgres user rather than root (for file ownership)
USER postgres
ENTRYPOINT ["/usr/local/bin/backup.sh"]