#!/usr/bin/env bash
# =============================================================================
# Cloud File Converter — Production Deployment Script (EC2 / Ubuntu)
# =============================================================================
# Usage:
#   chmod +x scripts/deploy.sh
#   ./scripts/deploy.sh
#
# Environment:
#   Requires .env.production to be present at the repo root.
#   Run as the `ubuntu` user (not root).
# =============================================================================
set -euo pipefail

APP_DIR="/var/www/cloudfileconverter"
REPO_URL="https://github.com/YOUR_USERNAME/cloud-file-converter.git"
VENV_DIR="$APP_DIR/.venv"
BACKEND_DIR="$APP_DIR/backend"

echo "======================================================"
echo "  Cloud File Converter — Deploy $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================"

# ── 1. Pull latest code ────────────────────────────────────────────────────────
echo "▶ Pulling latest code..."
if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR" && git pull origin main
else
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# ── 2. Copy production environment ────────────────────────────────────────────
echo "▶ Setting environment..."
cp .env.production .env

# ── 3. Python virtual environment ─────────────────────────────────────────────
echo "▶ Setting up Python environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements/production.txt"

# ── 4. Django management commands ─────────────────────────────────────────────
echo "▶ Running migrations..."
cd "$BACKEND_DIR"
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check --deploy

# ── 5. Restart services ───────────────────────────────────────────────────────
echo "▶ Restarting Gunicorn + Celery..."
sudo supervisorctl restart cloudfileconverter-gunicorn
sudo supervisorctl restart cloudfileconverter-celery-worker
sudo supervisorctl restart cloudfileconverter-celery-beat

# ── 6. Reload Nginx ───────────────────────────────────────────────────────────
echo "▶ Reloading Nginx..."
sudo nginx -t && sudo systemctl reload nginx

# ── 7. Health check ───────────────────────────────────────────────────────────
echo "▶ Running health check..."
sleep 5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.cloudfileconverter.com/api/v1/health/)
if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "✅ Deploy successful! Health check returned HTTP $HTTP_STATUS"
else
    echo "❌ Health check FAILED with HTTP $HTTP_STATUS"
    exit 1
fi

echo ""
echo "======================================================"
echo "  Deployment complete! 🚀"
echo "======================================================"
