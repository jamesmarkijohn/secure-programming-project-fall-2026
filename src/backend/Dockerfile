# Built with the repository root as the build context (see docker-compose.yml),
# so it can copy both src/backend/ and database/seed.sql.
FROM python:3.14-slim

# No .pyc files in the image; log output appears immediately.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# An unprivileged user to run the app. If the app is compromised, the
# attacker gets this user's limited rights, not root's.
RUN useradd --create-home --uid 10001 app

WORKDIR /app

# Install dependencies before copying the code: Docker caches this layer,
# so editing code doesn't trigger a full reinstall.
COPY src/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/backend/ .
COPY database/seed.sql database/seed.sql
RUN chmod 0755 entrypoint.sh

USER app
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
