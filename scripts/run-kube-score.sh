#!/usr/bin/env bash
set -euo pipefail

REPORT_FILE="kube-score.json"
DEFAULT_TARGET="k8s"

# Vérifier que kube-score est installé
if ! command -v kube-score >/dev/null 2>&1; then
    echo "Error: kube-score is not installed."
    exit 1
fi

# Fichiers à scanner
if [ "$#" -gt 0 ]; then
    TARGETS=("$@")
else
    TARGETS=("$DEFAULT_TARGET")
fi

echo "Running Kube-Score on: ${TARGETS[*]}"
set +e
kube-score score "${TARGETS[@]}" --output-format json > "$REPORT_FILE"
KUBESCORE_EXIT_CODE=$?
set -e

echo "Kube-Score finished with exit code: $KUBESCORE_EXIT_CODE"
exit 0
