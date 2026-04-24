#!/usr/bin/env bash
# extract-mo-schema.sh — run ON the practice server to extract the Medical Office
# MariaDB schema into a JSON file we can ground our adapter against.
#
# NOTHING is sent anywhere. The file lands locally; David transfers via USB.
#
# Prerequisites: mariadb-client (or the bundled mysqldump that ships with MO).
#
# Usage:
#   ./extract-mo-schema.sh [HOST] [PORT] [USER] [DATABASE]
#
# Defaults assume Medical Office's local install (adjust to fit Papa's server):
#   HOST=127.0.0.1 PORT=3306 USER=root DATABASE=mediofc
#
# It will prompt for the password (never echoed, never written to disk).

set -euo pipefail

HOST="${1:-127.0.0.1}"
PORT="${2:-3306}"
USER="${3:-root}"
DATABASE="${4:-mediofc}"

OUT="mo_schema_$(date +%Y%m%d).json"

echo "Extracting schema from ${USER}@${HOST}:${PORT}/${DATABASE} → ${OUT}"
read -rsp "Password: " PASSWORD
echo

# 1. List all tables
TABLES=$(mariadb -h "$HOST" -P "$PORT" -u "$USER" -p"$PASSWORD" -D "$DATABASE" \
  -N -e "SHOW TABLES")
TABLE_COUNT=$(echo "$TABLES" | wc -l | tr -d ' ')
echo "Found $TABLE_COUNT tables."

# 2. For each table: SHOW CREATE TABLE → assemble JSON
{
  echo "{"
  echo "  \"database\": \"$DATABASE\","
  echo "  \"extracted_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
  echo "  \"table_count\": $TABLE_COUNT,"
  echo "  \"tables\": {"

  FIRST=1
  for T in $TABLES; do
    if [ $FIRST -eq 0 ]; then echo ","; fi
    FIRST=0
    DDL=$(mariadb -h "$HOST" -P "$PORT" -u "$USER" -p"$PASSWORD" -D "$DATABASE" \
          -N -e "SHOW CREATE TABLE \`$T\`" 2>/dev/null \
          | awk -F'\t' '{print $2}' \
          | python3 -c "import sys, json; print(json.dumps(sys.stdin.read()))")
    ROWCOUNT=$(mariadb -h "$HOST" -P "$PORT" -u "$USER" -p"$PASSWORD" -D "$DATABASE" \
                -N -e "SELECT COUNT(*) FROM \`$T\`" 2>/dev/null || echo "null")
    printf "    \"%s\": { \"ddl\": %s, \"row_count\": %s }" "$T" "$DDL" "$ROWCOUNT"
  done

  echo
  echo "  }"
  echo "}"
} > "$OUT"

# Clear password from environment
unset PASSWORD

SIZE=$(wc -c < "$OUT" | tr -d ' ')
echo "✓ Schema written to $OUT (${SIZE} bytes)"
echo ""
echo "Next: copy this file to David. He maps the columns into"
echo "  server/app/medical_office/mariadb.py"
echo "and the MariaDB adapter goes from stub to real."
