# Morphix â€” AWS Production Deployment Guide

This guide details the steps to deploy **Morphix** on AWS for production usage, utilizing **EC2** for compute, **S3** for temp file storage, and **CloudFront** for static asset delivery, SSL termination, and CDN caching.

---

## 1. AWS S3 Storage Setup

We use AWS S3 for hosting temporary uploaded files and converted outputs. Due to the free quota model, files are automatically pruned after 1 hour (guests) or 24 hours (registered users) using Celery lifecycle tasks.

### Create S3 Bucket
1. Go to AWS S3 Console -> Create Bucket.
2. Set Name: `prod-morphix` (must be unique).
3. Disable **Block all public access** (pre-signed URLs require public read parameters, but bucket assets should remain private by default).

### Bucket Lifecycle Policy (Abuse Prevention Guard)
To ensure no orphaned uploads persist on S3 even if the Celery task runner crashes, configure an **S3 Lifecycle Expiration Policy**:
1. Go to the S3 Bucket -> **Management** tab.
2. Click **Create lifecycle rule**.
3. Rule Name: `PruneTemporaryFilesAfter1Day`.
4. Choose: **Apply to all objects in the bucket**.
5. Tick: **Expire current versions of objects**.
6. Set **Days after object creation**: `1` day.

---

## 2. CloudFront CDN & Caching Architecture

We route static frontend assets and media through CloudFront to maximize delivery speed and cache static responses.

### Cache Policy for Frontend
1. Create CloudFront Distribution pointing to your frontend Origin (e.g. S3 Static Web Hosting or EC2).
2. Mappings:
   - `/assets/*` -> Cache HTTP headers set to max-age (1 year).
   - `/manifest.webmanifest` and `/sw.js` -> Cache bypassed (`Cache-Control: no-cache`).

### Origin Requests Policy for API
1. Map `/api/*` and `/ws/*` path behaviors to point directly to the EC2 Application Server Origin.
2. Set CloudFront behavior for `/api/*`:
   - Allowed HTTP Methods: `GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE`.
   - Cache Policy: `CachingDisabled` (forward all headers including `Authorization` and `Cookie` to Backend).

---

## 3. EC2 Application Server Setup

### Host Prerequisites
1. Launch an **Ubuntu 24.04 LTS** EC2 instance.
2. Ensure Security Groups allow:
   - `80` (HTTP) & `443` (HTTPS)
   - `22` (SSH)

### Install OS Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git nginx redis-server tesseract-ocr supervisor
```

### Setup Backend Application env
```bash
git clone <repo-url> /var/www/morphix
cd /var/www/morphix
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements/prod.txt
```

---

## 4. Nginx Reverse Proxy Config

Configure Nginx to act as the primary reverse proxy, handling static routes, routing `/api/` to Gunicorn/Daphne, and upgrading `/ws/` connections to WebSockets.

Create `/etc/nginx/sites-available/morphix`:
```nginx
server {
    listen 80;
    server_name api.morphix.com;

    # Redirect all HTTP traffic to HTTPS (managed by CloudFront or Certbot SSL)
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.morphix.com;

    ssl_certificate /etc/letsencrypt/live/api.morphix.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.morphix.com/privkey.pem;

    # API Requests
    location /api/v1/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSockets (ASGI Daphne Router)
    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400; # Keep open for 24h
    }
}
```

Enable the configuration:
```bash
sudo ln -s /etc/nginx/sites-available/morphix /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 5. Supervisor System Daemon Configuration

We run Daphne (ASGI) and Celery workers using system daemons managed by **Supervisor**.

### ASGI Daemon (Daphne / WebSockets)
Create `/etc/supervisor/conf.d/daphne.conf`:
```ini
[program:daphne]
directory=/var/www/morphix/backend
command=/var/www/morphix/.venv/bin/daphne -b 127.0.0.1 -p 8001 config.asgi:application
user=ubuntu
autostart=true
autorestart=true
stdout_logfile=/var/log/daphne.log
stderr_logfile=/var/log/daphne.err.log
```

### Celery Priority Worker Daemon
Create `/etc/supervisor/conf.d/celery_workers.conf`:
```ini
[program:celery_default]
directory=/var/www/morphix/backend
command=/var/www/morphix/.venv/bin/celery -A config worker --loglevel=INFO -Q default,priority
user=ubuntu
autostart=true
autorestart=true
stdout_logfile=/var/log/celery_default.log
stderr_logfile=/var/log/celery_default.err.log

[program:celery_heavy]
directory=/var/www/morphix/backend
command=/var/www/morphix/.venv/bin/celery -A config worker --loglevel=INFO -Q heavy -c 2
user=ubuntu
autostart=true
autorestart=true
stdout_logfile=/var/log/celery_heavy.log
stderr_logfile=/var/log/celery_heavy.err.log
```

Update Supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```
