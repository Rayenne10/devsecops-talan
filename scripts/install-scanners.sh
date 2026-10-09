#!/usr/bin/env bash
set -euo pipefail
DEST=${1:-/usr/local/bin}
mkdir -p "$DEST"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -fsSL --retry 3 https://github.com/stackrox/kube-linter/releases/download/v0.8.3/kube-linter-linux -o "$tmp/kube-linter"
echo "618d299a3e2839c8ca9d86fce0db617be0fba41f0fecbbbfb7fbf1c04299fae1  $tmp/kube-linter" | sha256sum -c -
curl -fsSL --retry 3 https://github.com/zegl/kube-score/releases/download/v1.20.0/kube-score_1.20.0_linux_amd64 -o "$tmp/kube-score_1.20.0_linux_amd64"
curl -fsSL --retry 3 https://github.com/zegl/kube-score/releases/download/v1.20.0/checksums.txt -o "$tmp/checksums.txt"
(cd "$tmp" && grep ' kube-score_1.20.0_linux_amd64$' checksums.txt | sha256sum -c -)
install -m 755 "$tmp/kube-linter" "$DEST/kube-linter"
install -m 755 "$tmp/kube-score_1.20.0_linux_amd64" "$DEST/kube-score"
