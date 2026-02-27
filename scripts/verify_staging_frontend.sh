#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-https://skyway-staging.yjroutdoors.com}"
ROUTE="${ROUTE:-/favorites}"
API_PATH="${API_PATH:-/api/filters/}"

EXPECT_HTML=()
EXPECT_JS=()
EXPECT_CSS=()

usage() {
  cat <<'EOF'
Usage: scripts/verify_staging_frontend.sh [options]

Options:
  --base-url URL          Staging base URL (default: https://skyway-staging.yjroutdoors.com)
  --route PATH            Frontend route to verify (default: /favorites)
  --api-path PATH         API path for health check (default: /api/filters/)
  --expect-html TEXT      Assert route HTML contains TEXT (repeatable)
  --expect-js TEXT        Assert downloaded route JS assets contain TEXT (repeatable)
  --expect-css TEXT       Assert downloaded CSS assets contain TEXT (repeatable)
  -h, --help              Show help

Examples:
  scripts/verify_staging_frontend.sh
  scripts/verify_staging_frontend.sh \
    --expect-js "data-label" \
    --expect-css "favorites-table tbody tr"
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url) BASE_URL="${2:-}"; shift 2 ;;
    --route) ROUTE="${2:-}"; shift 2 ;;
    --api-path) API_PATH="${2:-}"; shift 2 ;;
    --expect-html) EXPECT_HTML+=("${2:-}"); shift 2 ;;
    --expect-js) EXPECT_JS+=("${2:-}"); shift 2 ;;
    --expect-css) EXPECT_CSS+=("${2:-}"); shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ "$ROUTE" != /* ]]; then
  ROUTE="/$ROUTE"
fi
if [[ "$API_PATH" != /* ]]; then
  API_PATH="/$API_PATH"
fi

TMP_DIR="$(mktemp -d /tmp/skyway-staging-verify.XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT

ok() { echo "[OK] $*"; }
fail() { echo "[FAIL] $*" >&2; exit 1; }

fetch_status() {
  local url="$1"
  curl -sS -o /dev/null -w '%{http_code}' "$url" || true
}

ROUTE_URL="${BASE_URL%/}${ROUTE}"
API_URL="${BASE_URL%/}${API_PATH}"
HTML_FILE="$TMP_DIR/route.html"

route_code="$(fetch_status "$ROUTE_URL")"
[[ "$route_code" == "200" ]] || fail "Route check failed: $ROUTE_URL -> $route_code"
ok "Route reachable: $ROUTE_URL"

api_code="$(fetch_status "$API_URL")"
[[ "$api_code" == "200" ]] || fail "API check failed: $API_URL -> $api_code"
ok "API reachable: $API_URL"

curl -sS "$ROUTE_URL" > "$HTML_FILE"

if [[ "${#EXPECT_HTML[@]}" -gt 0 ]]; then
  for expected in "${EXPECT_HTML[@]}"; do
    if grep -Fq "$expected" "$HTML_FILE"; then
      ok "HTML contains expected text: $expected"
    else
      fail "HTML missing expected text: $expected"
    fi
  done
fi

CSS_LIST="$TMP_DIR/css_urls.txt"
JS_LIST="$TMP_DIR/js_urls.txt"

grep -Eo 'href="/_next/static/css/[^"]+\.css"' "$HTML_FILE" | sed -E 's/^href="//; s/"$//' | sort -u > "$CSS_LIST" || true
grep -Eo 'src="/_next/static/chunks/[^"]+\.js"' "$HTML_FILE" | sed -E 's/^src="//; s/"$//' | sort -u > "$JS_LIST" || true

css_count="$(wc -l < "$CSS_LIST" | tr -d ' ')"
js_count="$(wc -l < "$JS_LIST" | tr -d ' ')"
[[ "$css_count" -gt 0 ]] || fail "No Next.js CSS assets found on $ROUTE_URL"
[[ "$js_count" -gt 0 ]] || fail "No Next.js JS assets found on $ROUTE_URL"
ok "Found $css_count CSS assets and $js_count JS assets"

CSS_BUNDLE="$TMP_DIR/all.css"
JS_BUNDLE="$TMP_DIR/all.js"
: > "$CSS_BUNDLE"
: > "$JS_BUNDLE"

while IFS= read -r rel; do
  [[ -z "$rel" ]] && continue
  url="${BASE_URL%/}${rel}"
  code="$(fetch_status "$url")"
  [[ "$code" == "200" ]] || fail "CSS asset failed: $url -> $code"
  curl -sS "$url" >> "$CSS_BUNDLE"
  printf '\n' >> "$CSS_BUNDLE"
done < "$CSS_LIST"
ok "All CSS assets reachable"

while IFS= read -r rel; do
  [[ -z "$rel" ]] && continue
  url="${BASE_URL%/}${rel}"
  code="$(fetch_status "$url")"
  [[ "$code" == "200" ]] || fail "JS asset failed: $url -> $code"
  curl -sS "$url" >> "$JS_BUNDLE"
  printf '\n' >> "$JS_BUNDLE"
done < "$JS_LIST"
ok "All JS assets reachable"

if [[ "${#EXPECT_CSS[@]}" -gt 0 ]]; then
  for expected in "${EXPECT_CSS[@]}"; do
    if grep -Fq "$expected" "$CSS_BUNDLE"; then
      ok "CSS contains expected text: $expected"
    else
      fail "CSS missing expected text: $expected"
    fi
  done
fi

if [[ "${#EXPECT_JS[@]}" -gt 0 ]]; then
  for expected in "${EXPECT_JS[@]}"; do
    if grep -Fq "$expected" "$JS_BUNDLE"; then
      ok "JS contains expected text: $expected"
    else
      fail "JS missing expected text: $expected"
    fi
  done
fi

ok "Staging frontend verification passed"
