#!/usr/bin/env bash
set -euo pipefail
rm -f analysis.json ai-report.json kube-linter.json kube-score.json audit-report.html remediation-*.json
rm -rf ai-patches
bash scripts/run-kube-linter.sh & linter_pid=$!
bash scripts/run-kube-score.sh & score_pid=$!
wait "$linter_pid"
wait "$score_pid"
python3 scripts/consolidate.py
python3 scripts/ai-analysis.py --offline
python3 scripts/generate-report.py
python3 scripts/create-remediation-mr.py
# The demo includes an intentionally unsafe fixture. A blocked gate is the expected outcome.
if python3 scripts/workflow.py gate; then echo 'ERROR: unsafe fixture was not blocked'; exit 1; fi
echo 'PASS: real scanners completed, offline report generated, unsafe fixture blocked, no external writes.'
