# Morphix â€” Deployment Guide

## Development (Docker Compose)

### Prerequisites
- Docker Desktop (or Docker Engine + Compose plugin)
- Git

### Start
```bash
# Clone and configure
git clone <repo-url>
cd morphix
cp .env.example .env

# Start all services
docker compose up -d

# Run migrations
docker compose exec backend python manage.py migrate

# Create admin
docker compose exec backend python manage.py createsuperuser
```

### Services
| Service | URL | Purpose |
|---|---|---|
| Frontend | http://localhost:5173 | React app |
| Backend | http://localhost:8000 | Django API |
| Swagger | http://localhost:8000/api/docs/ | API docs |
| MinIO | http://localhost:9001 | S3 console |
| Flower | http://localhost:5555 | Celery monitor |
| Redis | localhost:6379 | Message broker |
| PostgreSQL | localhost:5432 | Database |

---

## Production Deployment

### Frontend â†’ Vercel

1. Connect your GitHub repository to Vercel
2. Set root directory to `frontend/`
3. Set environment variables:
   - `VITE_API_URL` = your backend URL (e.g., `https://api.yourapp.com/api/v1`)
4. Deploy

### Backend â†’ Render

1. Create a new **Web Service** on Render
2. Set root directory to `backend/`
3. Build command: `pip install -r requirements/prod.txt && python manage.py collectstatic --noinput && python manage.py migrate`
4. Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3`
5. Add environment variables from `.env.example`
6. Create a **Background Worker** for Celery:
   - Same repo, same root
   - Start command: `celery -A config.celery worker --loglevel=info`

### Database â†’ Render/Supabase

- Create a managed PostgreSQL database
- Set `DATABASE_URL` in your backend environment

### Redis â†’ Render/Upstash

- Create a managed Redis instance
- Set `CELERY_BROKER_URL` and `REDIS_URL`

### Storage â†’ AWS S3

- Create an S3 bucket (private ACL)
- Create an IAM user with S3 access
- Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`
- Remove `AWS_S3_ENDPOINT_URL` (defaults to AWS)

---

## Environment Variables

See `.env.example` for the complete list. Critical production variables:

| Variable | Description |
|---|---|
| `DJANGO_SECRET_KEY` | Unique secret key (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`) |
| `DJANGO_DEBUG` | Set to `False` in production |
| `DATABASE_URL` | PostgreSQL connection string |
| `CELERY_BROKER_URL` | Redis URL for Celery |
| `AWS_*` | S3 storage credentials |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `CORS_ALLOWED_ORIGINS` | Frontend URL(s) |
