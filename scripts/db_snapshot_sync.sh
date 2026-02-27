#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE_DEFAULT="$ROOT_DIR/scripts/db_sync.env"
SNAPSHOT_DIR_DEFAULT="$ROOT_DIR/snapshots/db"

ENV_FILE="${ENV_FILE:-$ENV_FILE_DEFAULT}"
SNAPSHOT_DIR="${SNAPSHOT_DIR:-$SNAPSHOT_DIR_DEFAULT}"

YES=0
SNAPSHOT_FILE=""

usage() {
  cat <<'EOF'
Usage: scripts/db_snapshot_sync.sh <command> [options]

Commands:
  snapshot-only
      Create a production dump snapshot only.

  snapshot-to-staging
      Create a production snapshot and restore it into staging DB.

  snapshot-to-local
      Create a production snapshot and restore it into local DB.

  restore-to-staging
      Restore an existing snapshot file into staging DB.

  restore-to-local
      Restore an existing snapshot file into local DB.

  list-snapshots
      List snapshot files in snapshots/db.

Options:
  --snapshot-file PATH    Use a specific snapshot file (restore commands), or write to PATH (snapshot-only)
  --yes                   Non-interactive confirmation for restore operations
  -h, --help              Show help

Environment:
  By default this script loads scripts/db_sync.env if present.
  Required keys are documented in scripts/db_sync.env.example.
EOF
}

log() { echo "[INFO] $*"; }
fail() { echo "[FAIL] $*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing command: $1"
}

require_env() {
  local key="$1"
  [[ -n "${!key:-}" ]] || fail "Missing required env var: $key"
}

load_env_file() {
  if [[ -f "$ENV_FILE" ]]; then
    log "Loading env from $ENV_FILE"
    set -a
    # shellcheck source=/dev/null
    source "$ENV_FILE"
    set +a
  else
    log "Env file not found at $ENV_FILE (continuing with current shell env vars)"
  fi
}

read_env_value() {
  local file="$1"
  local key="$2"
  grep -E "^${key}=" "$file" | head -n1 | sed -E "s/^${key}=//" || true
}

hydrate_local_env_from_backend_dotenv() {
  local backend_env="$ROOT_DIR/backend/.env"
  [[ -f "$backend_env" ]] || return 0

  : "${LOCAL_DB_HOST:=$(read_env_value "$backend_env" POSTGRES_HOST)}"
  : "${LOCAL_DB_PORT:=$(read_env_value "$backend_env" POSTGRES_PORT)}"
  : "${LOCAL_DB_NAME:=$(read_env_value "$backend_env" POSTGRES_DB)}"
  : "${LOCAL_DB_USER:=$(read_env_value "$backend_env" POSTGRES_USER)}"
  : "${LOCAL_DB_PASSWORD:=$(read_env_value "$backend_env" POSTGRES_PASSWORD)}"
}

snapshot_filename() {
  local ts sha
  ts="$(date +%Y%m%d-%H%M%S)"
  sha="$(git -C "$ROOT_DIR" rev-parse --short HEAD 2>/dev/null || echo "nosha")"
  echo "$SNAPSHOT_DIR/prod-${ts}-${sha}.dump"
}

build_snapshot_from_prod() {
  local output_file="$1"
  mkdir -p "$SNAPSHOT_DIR"

  require_env PROD_DB_HOST
  require_env PROD_DB_PORT
  require_env PROD_DB_NAME
  require_env PROD_DB_USER
  require_env PROD_DB_PASSWORD

  log "Creating production snapshot: $output_file"
  PGPASSWORD="$PROD_DB_PASSWORD" pg_dump \
    --host "$PROD_DB_HOST" \
    --port "$PROD_DB_PORT" \
    --username "$PROD_DB_USER" \
    --dbname "$PROD_DB_NAME" \
    --format=custom \
    --compress=9 \
    --no-owner \
    --no-privileges \
    --file "$output_file"
  log "Snapshot complete"
}

confirm_restore() {
  local target="$1"
  if [[ "$YES" -eq 1 ]]; then
    return 0
  fi
  read -r -p "This will overwrite the ${target} database. Continue? (yes/no): " answer
  [[ "$answer" == "yes" ]] || fail "Aborted"
}

restore_into_target() {
  local target="$1"
  local file="$2"
  local host_var="${target}_DB_HOST"
  local port_var="${target}_DB_PORT"
  local name_var="${target}_DB_NAME"
  local user_var="${target}_DB_USER"
  local pass_var="${target}_DB_PASSWORD"

  [[ -f "$file" ]] || fail "Snapshot file not found: $file"

  require_env "$host_var"
  require_env "$port_var"
  require_env "$name_var"
  require_env "$user_var"
  require_env "$pass_var"

  confirm_restore "$target"

  local host port name user pass
  host="${!host_var}"
  port="${!port_var}"
  name="${!name_var}"
  user="${!user_var}"
  pass="${!pass_var}"

  log "Restoring snapshot into ${target} database ${name}@${host}:${port}"
  PGPASSWORD="$pass" pg_restore \
    --host "$host" \
    --port "$port" \
    --username "$user" \
    --dbname "$name" \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    --single-transaction \
    "$file"
  log "Restore into ${target} completed"
}

list_snapshots() {
  mkdir -p "$SNAPSHOT_DIR"
  ls -1 "$SNAPSHOT_DIR"/*.dump 2>/dev/null || true
}

COMMAND="${1:-}"
[[ -n "$COMMAND" ]] || { usage; exit 1; }
shift || true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --snapshot-file)
      SNAPSHOT_FILE="${2:-}"
      shift 2
      ;;
    --yes)
      YES=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown option: $1"
      ;;
  esac
done

require_cmd pg_dump
require_cmd pg_restore
require_cmd psql
load_env_file
hydrate_local_env_from_backend_dotenv

case "$COMMAND" in
  snapshot-only)
    target_file="${SNAPSHOT_FILE:-$(snapshot_filename)}"
    build_snapshot_from_prod "$target_file"
    echo "$target_file"
    ;;
  snapshot-to-staging)
    target_file="${SNAPSHOT_FILE:-$(snapshot_filename)}"
    build_snapshot_from_prod "$target_file"
    restore_into_target "STAGING" "$target_file"
    ;;
  snapshot-to-local)
    target_file="${SNAPSHOT_FILE:-$(snapshot_filename)}"
    build_snapshot_from_prod "$target_file"
    restore_into_target "LOCAL" "$target_file"
    ;;
  restore-to-staging)
    [[ -n "$SNAPSHOT_FILE" ]] || fail "--snapshot-file is required for restore-to-staging"
    restore_into_target "STAGING" "$SNAPSHOT_FILE"
    ;;
  restore-to-local)
    [[ -n "$SNAPSHOT_FILE" ]] || fail "--snapshot-file is required for restore-to-local"
    restore_into_target "LOCAL" "$SNAPSHOT_FILE"
    ;;
  list-snapshots)
    list_snapshots
    ;;
  *)
    usage
    exit 1
    ;;
esac
