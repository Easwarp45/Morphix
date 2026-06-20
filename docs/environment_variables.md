# Cloud File Converter — Environment Variables Reference

Complete reference for all environment variables used by the Cloud File Converter platform.

---

## Django Core

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | ✅ Yes | — | 50+ character random secret. Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DJANGO_DEBUG` | ✅ Yes | `False` | Set `True` for development ONLY. Never `True` in production. |
| `DJANGO_SETTINGS_MODULE` | ✅ Yes | — | `config.settings.production` for prod, `config.settings.development` for dev |
| `DJANGO_ALLOWED_HOSTS` | ✅ Yes | — | Comma-separated hostnames, e.g. `api.example.com,example.com` |

---

## Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ Yes | — | Full PostgreSQL DSN: `postgres://user:pass@host:5432/dbname` |
| `POSTGRES_DB` | Dev only | `cloudconv` | Used by Docker Compose |
| `POSTGRES_USER` | Dev only | `cloudconv` | Used by Docker Compose |
| `POSTGRES_PASSWORD` | Dev only | `cloudconv` | Used by Docker Compose |

> **Render / Railway**: These platforms inject `DATABASE_URL` automatically when you attach a Postgres plugin.

---

## Redis & Celery

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | ✅ Yes | `redis://redis:6379/0` | Redis connection URL. Used for Django cache. |
| `CELERY_BROKER_URL` | ✅ Yes | `redis://redis:6379/0` | Celery task queue broker |
| `CELERY_RESULT_BACKEND` | ✅ Yes | `redis://redis:6379/1` | Celery result storage |

---

## AWS S3 / Storage

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | ✅ Yes | `minioadmin` (dev) | AWS IAM key ID |
| `AWS_SECRET_ACCESS_KEY` | ✅ Yes | `minioadmin` (dev) | AWS IAM secret |
| `AWS_STORAGE_BUCKET_NAME` | ✅ Yes | `cloud-file-converter` | S3 bucket name |
| `AWS_S3_REGION_NAME` | ✅ Yes | `us-east-1` | AWS region |
| `AWS_S3_ENDPOINT_URL` | Dev only | `http://minio:9000` | Override for MinIO in dev. Leave empty for production AWS. |
| `AWS_S3_CUSTOM_DOMAIN` | Optional | — | Your CloudFront domain, e.g. `dXXXX.cloudfront.net` |
| `AWS_DEFAULT_ACL` | Optional | `private` | S3 object ACL |

---

## Authentication

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Optional | `15` | Short-lived access token lifetime |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Optional | `7` | Long-lived refresh token lifetime |
| `GOOGLE_CLIENT_ID` | Optional | — | Google OAuth 2.0 client ID |
| `GOOGLE_CLIENT_SECRET` | Optional | — | Google OAuth 2.0 client secret |

---

## Email (SMTP)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EMAIL_HOST` | Prod only | — | SMTP host, e.g. `smtp.sendgrid.net` |
| `EMAIL_PORT` | Prod only | `587` | SMTP port (587 for TLS) |
| `EMAIL_HOST_USER` | Prod only | — | SMTP username (SendGrid: `apikey`) |
| `EMAIL_HOST_PASSWORD` | Prod only | — | SMTP password or API key |
| `DEFAULT_FROM_EMAIL` | Optional | — | Sender address, e.g. `noreply@example.com` |

---

## CORS & Security

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORS_ALLOWED_ORIGINS` | ✅ Yes | `http://localhost:5173` | Comma-separated frontend origins |
| `CSRF_TRUSTED_ORIGINS` | Prod only | — | Comma-separated trusted CSRF origins |

---

## AI / OCR

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Optional | — | Google Gemini API key for AI summarization. Falls back to local algorithm if absent. |

---

## Observability

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENTRY_DSN` | Optional | — | Sentry error tracking DSN. Skipped if empty. |

---

## File Limits & Quotas

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MAX_UPLOAD_SIZE_MB` | Optional | `50` | Max single file upload size in MB |
| `MAX_FILES_PER_UPLOAD` | Optional | `10` | Max files per batch upload |
| `DEFAULT_STORAGE_LIMIT_MB` | Optional | `500` | Storage quota per authenticated user |
| `GUEST_DAILY_CONVERSION_LIMIT` | Optional | `5` | Max conversions per day for guests |
| `GUEST_MAX_FILE_SIZE_MB` | Optional | `10` | Max file size for guests |

---

## File Lifecycle

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FILE_RETENTION_DAYS` | Optional | `7` | Days before auto-deletion of old files |
| `SHAREABLE_LINK_EXPIRY_DAYS` | Optional | `30` | Days before shareable links expire |

---

## Frontend (Vite)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | ✅ Yes | `http://localhost:8000/api/v1` | Backend API base URL |
| `VITE_WS_URL` | Optional | — | WebSocket server URL for real-time conversion |
| `VITE_APP_NAME` | Optional | `Cloud File Converter` | App display name |

---

## Generating Secrets

```bash
# Django SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Random password (Linux/macOS)
openssl rand -base64 32

# Random password (PowerShell)
[System.Web.Security.Membership]::GeneratePassword(32, 8)
```
