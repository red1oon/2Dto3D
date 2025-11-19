#!/bin/bash
# Run all audit tests for ViewportSnapshot
# Usage: ./run_audits.sh [database_path]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/../venv/bin/python"

# Default database
DB_PATH="${1:-$SCRIPT_DIR/../DatabaseFiles/Terminal1_ARC_STR.db}"

echo "=== ViewportSnapshot Audit Tests ==="
echo "Database: $DB_PATH"
echo ""

# Run audit_database.py
echo "--- Running audit_database.py ---"
$VENV_PYTHON "$SCRIPT_DIR/audit_database.py" "$DB_PATH"
AUDIT_DB_RESULT=$?

echo ""

# Run audit_viewport_truth.py
echo "--- Running audit_viewport_truth.py ---"
$VENV_PYTHON "$SCRIPT_DIR/audit_viewport_truth.py" "$DB_PATH"
AUDIT_VP_RESULT=$?

echo ""
echo "=== Audit Summary ==="
if [ $AUDIT_DB_RESULT -eq 0 ] && [ $AUDIT_VP_RESULT -eq 0 ]; then
    echo "All audits PASSED"
    exit 0
else
    echo "Some audits FAILED"
    exit 1
fi
