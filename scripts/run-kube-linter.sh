#!/usr/bin/env bash
set -euo pipefail

REPORT_FILE="kube-linter.json"
DEFAULT_TARGET="k8s"

# Vérifier que kube-linter est installé
if ! command -v kube-linter >/dev/null 2>&1; then
    echo "Error: kube-linter is not installed."
    exit 1
fi

# Fichiers à scanner
if [ "$#" -gt 0 ]; then
    TARGETS=("$@")
else
    TARGETS=("$DEFAULT_TARGET")
fi

echo "Running KubeLinter on: ${TARGETS[*]}"
set +e
kube-linter lint "${TARGETS[@]}" --format json > "$REPORT_FILE"
KUBELINTER_EXIT_CODE=$?
set -e

echo "KubeLinter finished with exit code: $KUBELINTER_EXIT_CODE"
exit 0
