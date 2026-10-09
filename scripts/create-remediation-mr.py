#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create-remediation-mr.py

Reads ai-report.json patches, commits them to a new branch,
and opens a GitLab Merge Request automatically.

Required env vars:
  GITLAB_TOKEN        — GitLab API token (scope: api)
  GITLAB_PROJECT_ID   — Numeric project ID (Settings > General)
  CI_COMMIT_SHA       — Current commit
  BUILD_NUMBER        — Jenkins build number
"""
import json
import logging
import os
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
PROJECT_ID = os.getenv("GITLAB_PROJECT_ID")
SOURCE_BRANCH = os.getenv("GIT_BRANCH", "main").replace("origin/", "")
BUILD_NUMBER = os.getenv("BUILD_NUMBER", datetime.now().strftime("%Y%m%d%H%M%S"))

if not GITLAB_TOKEN or not PROJECT_ID:
    log.error("GITLAB_TOKEN et GITLAB_PROJECT_ID sont requis.")
    sys.exit(1)

HEADERS = {"PRIVATE-TOKEN": GITLAB_TOKEN, "Content-Type": "application/json"}
API = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}"

# ── Load patches from ai-report.json ────────────────────────────────────
report_path = os.path.join(BASE_DIR, "ai-report.json")
if not os.path.exists(report_path):
    log.info("Pas de ai-report.json, rien à faire.")
    sys.exit(0)

with open(report_path, "r") as f:
    report = json.load(f)

patches = report.get("patches", {})
if not patches:
    log.info("Aucun patch dans ai-report.json — pas de MR à créer.")
    sys.exit(0)

# ── Create branch ───────────────────────────────────────────────────────
fix_branch = f"fix/devsecops-audit-{BUILD_NUMBER}"
log.info(f"Création de la branche : {fix_branch}")

resp = requests.post(
    f"{API}/repository/branches",
    headers=HEADERS,
    json={"branch": fix_branch, "ref": SOURCE_BRANCH},
)
if resp.status_code not in (200, 201):
    log.error(f"Impossible de créer la branche : {resp.status_code} {resp.text}")
    sys.exit(1)

# ── Commit all patches ──────────────────────────────────────────────────
actions = []
for filepath, content in patches.items():
    actions.append({
        "action": "update",
        "file_path": filepath,
        "content": content,
    })

commit_msg = (
    f"fix(devsecops): auto-remediation audit #{BUILD_NUMBER}\n\n"
    f"Criticité: {report.get('criticite', 'UNKNOWN')}\n"
    f"Résumé: {report.get('resume', 'N/A')}\n\n"
    f"Corrections appliquées automatiquement par la pipeline DevSecOps IA.\n"
    f"Fichiers modifiés: {', '.join(patches.keys())}"
)

log.info(f"Commit de {len(actions)} fichier(s) corrigé(s)...")
resp = requests.post(
    f"{API}/repository/commits",
    headers=HEADERS,
    json={
        "branch": fix_branch,
        "commit_message": commit_msg,
        "actions": actions,
    },
)
if resp.status_code not in (200, 201):
    log.error(f"Impossible de commiter : {resp.status_code} {resp.text}")
    sys.exit(1)

log.info(f"Commit réussi : {resp.json().get('id', '?')[:12]}")

# ── Prepare MR description fields (Correction pour éviter la SyntaxError) ──
files_corrected = ", ".join(f"`{f}`" for f in patches.keys())
causes_list = "\n".join(f"- {c}" for c in report.get("causes", []))
corrections_list = "\n".join(f"- {c}" for c in report.get("corrections", []))

mr_title = f"🔒 Auto-remediation DevSecOps — Audit #{BUILD_NUMBER} ({report.get('criticite', '?')})"
mr_description = f"""## Rapport d'audit automatique

| Champ | Valeur |
|-------|--------|
| **Criticité** | `{report.get('criticite', 'UNKNOWN')}` |
| **Build** | #{BUILD_NUMBER} |
| **Fichiers corrigés** | {files_corrected} |

### Résumé
{report.get('resume', 'N/A')}

### Causes
{causes_list}

### Corrections appliquées
{corrections_list}

---
> ⚠️ **MR générée automatiquement** par la pipeline DevSecOps IA.
> Veuillez relire les changements avant de merger.
"""

log.info("Création de la Merge Request...")
resp = requests.post(
    f"{API}/merge_requests",
    headers=HEADERS,
    json={
        "source_branch": fix_branch,
        "target_branch": SOURCE_BRANCH,
        "title": mr_title,
        "description": mr_description,
        "remove_source_branch": True,
        "labels": "devsecops,auto-remediation",
    },
)
if resp.status_code not in (200, 201):
    log.error(f"Impossible de créer la MR : {resp.status_code} {resp.text}")
    sys.exit(1)

mr_url = resp.json().get("web_url", "?")
log.info(f"✅ MR créée avec succès : {mr_url}")
print(f"REMEDIATION_MR_URL={mr_url}")
