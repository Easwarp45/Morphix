# Morphix â€” Production Launch Checklist

Use this checklist before every production deployment. All items must be âœ… before going live.

---

## ðŸ” Security

- [ ] `DJANGO_DEBUG=False` is set in production environment
- [ ] `DJANGO_SECRET_KEY` is a unique 50+ character random string (not the dev key)
- [ ] All secrets are stored in environment variables â€” **never in code or Git**
- [ ] `.env.production` is in `.gitignore`
- [ ] `ALLOWED_HOSTS` lists only your actual domain(s)
- [ ] `CORS_ALLOWED_ORIGINS` lists only your actual frontend domain(s)
- [ ] `SECURE_SSL_REDIRECT=True` (Django will redirect HTTP â†’ HTTPS)
- [ ] `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True`
- [ ] `SECURE_HSTS_SECONDS=31536000` with subdomains enabled
- [ ] Admin URL (`/admin/`) is restricted to known IPs (Nginx `allow` directive)
- [ ] Ran `python manage.py check --deploy` with no critical issues
- [ ] Dependency audit: `pip-audit` or `safety check` shows no high-severity CVEs
- [ ] S3 bucket has **public access blocked**
- [ ] S3 bucket has **server-side encryption** enabled
- [ ] IAM user has **minimum required permissions** only
- [ ] Sentry DSN is configured for error tracking

---

## ðŸ—„ï¸ Database

- [ ] PostgreSQL 15+ is running and accessible
- [ ] `python manage.py migrate --noinput` completed successfully
- [ ] Database has backups enabled (RDS automated backups or pg_dump cron)
- [ ] Connection pool configured (PgBouncer or Django DB connection settings)
- [ ] `DATABASE_URL` is correct and tested

---

## âš¡ Redis & Celery

- [ ] Redis is running and accessible
- [ ] Celery worker is running and processing tasks
- [ ] Celery Beat is running for scheduled tasks (file cleanup, etc.)
- [ ] `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` are all set
- [ ] Tested: file conversion task reaches Celery and completes
- [ ] Flower monitoring dashboard is accessible (optional)

---

## â˜ï¸ AWS S3

- [ ] S3 bucket created in correct region
- [ ] Lifecycle rules configured (auto-delete after 7 days)
- [ ] CORS configuration set for your frontend domain
- [ ] CloudFront distribution created and `AWS_S3_CUSTOM_DOMAIN` set
- [ ] Test upload/download via Django admin or API

---

## ðŸŒ Networking & DNS

- [ ] DNS A/CNAME records point to your server/load balancer
- [ ] SSL certificate issued and valid (Let's Encrypt or ACM)
- [ ] HTTPS redirect is working (HTTP â†’ HTTPS)
- [ ] `api.yourdomain.com` resolves correctly
- [ ] WebSocket `wss://` connection tested in browser

---

## ðŸ—ï¸ Backend Deployment

- [ ] Gunicorn running with Uvicorn workers (for async/WebSocket support)
- [ ] Supervisor configured and services auto-restart on failure
- [ ] `python manage.py collectstatic --noinput` completed
- [ ] Static files served via Nginx (not Django)
- [ ] Nginx config tested with `nginx -t`
- [ ] Nginx rate limiting enabled for auth and upload endpoints

---

## ðŸ–¥ï¸ Frontend Deployment

- [ ] Vite production build created: `npm run build`
- [ ] `VITE_API_URL` points to production API
- [ ] `VITE_WS_URL` points to production WebSocket
- [ ] SPA rewrites configured (all routes â†’ `index.html`)
- [ ] Security headers added in `vercel.json` or Nginx
- [ ] PWA manifest and service worker are served correctly

---

## ðŸ“ˆ Observability

- [ ] Health check endpoint `GET /api/v1/health/` returns `200 OK`
- [ ] All infrastructure checks pass (database, redis, storage)
- [ ] Sentry is receiving test events: `python manage.py shell -c "1/0"`
- [ ] Structured JSON logs are being produced
- [ ] Uptime monitoring configured (UptimeRobot, Better Uptime, or AWS CloudWatch)
- [ ] Alerts configured for downtime and error spikes

---

## ðŸ§ª Testing

- [ ] All backend unit tests pass: `pytest`
- [ ] E2E tests pass against production or staging environment
- [ ] File upload + conversion tested manually end-to-end
- [ ] OCR pipeline tested with a scanned PDF
- [ ] AI summarization tested with a document
- [ ] WebSocket real-time progress tested
- [ ] Guest conversion mode tested (no authentication)
- [ ] Shareable download links tested

---

## ðŸ“‹ Go-Live Sign-off

| Check | Status | Notes |
|-------|--------|-------|
| Security hardening | â¬œ | |
| Database migrations | â¬œ | |
| Redis + Celery healthy | â¬œ | |
| S3 + CloudFront working | â¬œ | |
| SSL valid | â¬œ | |
| Health check passing | â¬œ | |
| Frontend deployed | â¬œ | |
| Sentry connected | â¬œ | |
| All tests green | â¬œ | |

> **Sign-off Date:** ___________
> **Deployed by:** ___________
> **Version:** v1.0.0
