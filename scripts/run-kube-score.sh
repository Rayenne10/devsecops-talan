#!/usr/bin/env bash
set -euo pipefail
if (( $# == 0 )); then mapfile -d '' targets < <(find k8s -name '*.yaml' -print0); set -- "${targets[@]}"; fi
(( $# )) || exit 2
set +e
kube-score score "$@" --output-format json > kube-score.json
status=$?
set -e
(( status <= 1 )) || exit "$status"
python3 -c 'import json; d=json.load(open("kube-score.json")); assert isinstance(d,list) and d'
