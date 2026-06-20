#!/usr/bin/env bash
# =============================================================================
# Morphix â€” Production Deployment Script (EC2 / Ubuntu)
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

APP_DIR="/var/www/morphix"
REPO_URL="https://github.com/YOUR_USERNAME/morphix.git"
VENV_DIR="$APP_DIR/.venv"
BACKEND_DIR="$APP_DIR/backend"

echo "======================================================"
echo "  Morphix â€” Deploy $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================"

# â”€â”€ 1. Pull latest code â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
echo "â–¶ Pulling latest code..."
if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR" && git pull origin main
else
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# â”€â”€ 2. Copy production environment â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
echo "â–¶ Setting environment..."
cp .env.production .env

# â”€â”€ 3. Python virtual environment â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
echo "â–¶ Setting up Python environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements/production.txt"

# â”€â”€ 4. Django management commands â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
echo "â–¶ Running migrations..."
cd "$BACKEND_DIR"
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check --deploy

# â”€â”€ 5. Restart services â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
echo "â–¶ Restarting Gunicorn + Celery..."
sudo supervisorctl restart morphix-gunicorn
sudo supervisorctl restart morphix-celery-worker
sudo supervisorctl restart morphix-celery-beat

# â”€â”€ 6. Reload Nginx â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
echo "â–¶ Reloading Nginx..."
sudo nginx -t && sudo systemctl reload nginx

# â”€â”€ 7. Health check â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
echo "â–¶ Running health check..."
sleep 5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.morphix.com/api/v1/health/)
if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "âœ… Deploy successful! Health check returned HTTP $HTTP_STATUS"
else
    echo "âŒ Health check FAILED with HTTP $HTTP_STATUS"
    exit 1
fi

echo ""
echo "======================================================"
echo "  Deployment complete! ðŸš€"
echo "======================================================"
