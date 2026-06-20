#!/usr/bin/env bash
# =============================================================================
# Morphix â€” Production Health Check Script
# =============================================================================
# Usage: ./scripts/health_check.sh [API_BASE_URL]
# Example: ./scripts/health_check.sh https://api.morphix.com
# =============================================================================
set -euo pipefail

API_URL="${1:-https://api.morphix.com}"
PASS=0
FAIL=0

check() {
    local NAME="$1"
    local URL="$2"
    local EXPECTED="$3"

    HTTP_STATUS=$(curl -s -o /tmp/hc_response.json -w "%{http_code}" "$URL" --max-time 10)
    if [ "$HTTP_STATUS" -eq "$EXPECTED" ]; then
        echo "  âœ… $NAME â€” HTTP $HTTP_STATUS"
        PASS=$((PASS + 1))
    else
        echo "  âŒ $NAME â€” Expected $EXPECTED, got HTTP $HTTP_STATUS"
        cat /tmp/hc_response.json 2>/dev/null || true
        FAIL=$((FAIL + 1))
    fi
}

echo ""
echo "======================================================="
echo "  Morphix â€” Health Check $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Target: $API_URL"
echo "======================================================="

echo ""
echo "â”€â”€ Core Endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
check "Health Check API"        "$API_URL/api/v1/health/"        200
check "API Root"                "$API_URL/api/v1/"               200
check "Auth Endpoints"          "$API_URL/api/v1/auth/login/"    405  # POST-only, GET returns 405
check "Admin Login Page"        "$API_URL/admin/login/"          200

echo ""
echo "â”€â”€ Security Headers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
HEADERS=$(curl -sI "$API_URL/api/v1/health/" --max-time 10)
check_header() {
    local HEADER_NAME="$1"
    if echo "$HEADERS" | grep -qi "$HEADER_NAME"; then
        echo "  âœ… $HEADER_NAME header present"
        PASS=$((PASS + 1))
    else
        echo "  âŒ $HEADER_NAME header MISSING"
        FAIL=$((FAIL + 1))
    fi
}
check_header "Strict-Transport-Security"
check_header "X-Content-Type-Options"
check_header "X-Frame-Options"

echo ""
echo "â”€â”€ Infrastructure Status â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
HEALTH_BODY=$(curl -s "$API_URL/api/v1/health/" --max-time 10 || echo '{}')
DB_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('database','unknown'))" 2>/dev/null || echo "error")
REDIS_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('redis','unknown'))" 2>/dev/null || echo "error")
S3_STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('storage','unknown'))" 2>/dev/null || echo "error")

echo "  Database : $DB_STATUS"
echo "  Redis    : $REDIS_STATUS"
echo "  S3       : $S3_STATUS"

echo ""
echo "======================================================="
echo "  Results: âœ… $PASS passed  âŒ $FAIL failed"
echo "======================================================="
echo ""

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
