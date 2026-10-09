#!/usr/bin/env bash
set -euo pipefail
(( $# )) || set -- k8s
set +e
kube-linter lint "$@" --format json > kube-linter.json
status=$?
set -e
# 1 means findings. Crashes and malformed output must block consolidation.
(( status <= 1 )) || exit "$status"
python3 -c 'import json; d=json.load(open("kube-linter.json")); assert isinstance(d,dict) and "Reports" in d'
