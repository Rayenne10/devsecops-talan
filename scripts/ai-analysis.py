#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai-analysis.py
Reads analysis.json, sends structured prompt to OpenAI, writes ai-report.json.
Now with: response_format, retry, timeout, YAML patch generation, AND Elasticsearch export.
"""
import json
import logging
import os
import requests
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Load consolidated data ──────────────────────────────────────────────
with open(os.path.join(BASE_DIR, "analysis.json"), "r") as f:
    data = json.load(f)

# ── Prompt ──────────────────────────────────────────────────────────────
prompt = f"""Tu es un expert DevSecOps Kubernetes.

Analyse les résultats suivants issus de kube-linter, kube-score et Renovate,
ainsi que le contenu des manifestes Kubernetes fournis.

Objectif :
1. Identifier les problèmes critiques
2. Expliquer les impacts réels
3. Donner des recommandations concrètes
4. **Pour chaque fichier problématique, fournir le manifeste YAML corrigé complet**
   dans le champ `patches` (clé = chemin du fichier, valeur = contenu YAML corrigé).

⚠️ REGLE DE CLASSIFICATION CRITIQUE :
Évalue la criticité générale à 'HIGH' UNIQUEMENT en cas de faille de sécurité majeure (ex: conteneur privilégié 'privileged: true', exécution en tant que root, ou escalade de privilèges).
Les simples manquements aux bonnes pratiques (comme l'absence de PodDisruptionBudget, de NetworkPolicy, de sondes liveness/readiness, ou de limites de stockage éphémère) doivent être classés au maximum en 'MEDIUM' ou 'LOW', car ils ne justifient pas de bloquer le pipeline de déploiement.

⚠️ CONSIGNES DE SYNTAXE YAML STRICTES (OBLIGATOIRES) :
1. Les manifestes retournés dans le champ 'patches' doivent être du code YAML 100% valide.
2. N'inclus JAMAIS de caractères accolades parasites (comme '}}') à la fin ou à l'intérieur du YAML.
3. Sépare obligatoirement chaque ressource Kubernetes (Deployment, PodDisruptionBudget, NetworkPolicy) par une ligne contenant uniquement trois tirets '---'.
4. Respecte scrupuleusement l'indentation standard de Kubernetes (2 espaces).

Retourne un JSON au format exact :
{{
  "criticite": "LOW|MEDIUM|HIGH",
  "resume": "string",
  "causes": ["string"],
  "impacts": ["string"],
  "corrections": ["string"],
  "patches": {{
    "k8s/fichier.yaml": "contenu YAML corrigé complet"
  }}
}}

Données :
{json.dumps(data, indent=2)}
"""

# ── API call with retry ─────────────────────────────────────────────────
@retry(
    retry=retry_if_exception_type((APITimeoutError, APIConnectionError, RateLimitError)),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    stop=stop_after_attempt(3),
    before_sleep=lambda rs: log.warning(f"Retry #{rs.attempt_number} après erreur..."),
)
def call_openai():
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Tu es un expert Kubernetes DevSecOps. Tu réponds uniquement en JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=4096,
        timeout=60,
        response_format={"type": "json_object"},
    )

def send_to_elasticsearch(payload, report):
    """Envoie le rapport d'audit et les résultats consolidés vers Elasticsearch."""
    es_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "scanned_files": payload.get("scanned_files", []),
        "criticite": report.get("criticite", "UNKNOWN"),
        "resume": report.get("resume", ""),
        "causes_count": len(report.get("causes", [])),
        "impacts_count": len(report.get("impacts", [])),
        "corrections_count": len(report.get("corrections", [])),
        "causes": report.get("causes", []),
        "impacts": report.get("impacts", []),
        "corrections": report.get("corrections", []),
        "kube_linter_errors": len(payload.get("kube_linter", [])),
        "kube_score_errors": len(payload.get("kube_score", []))
    }
    
    # URL de notre Elasticsearch dans le réseau docker (nom du conteneur)
    es_url = "http://elasticsearch:9200/devsecops-audit/_doc"
    try:
        response = requests.post(es_url, json=es_data, headers={"Content-Type": "application/json"}, timeout=5)
        if response.status_code in [200, 201]:
            log.info("✅ Audit envoyé avec succès à Elasticsearch.")
        else:
            log.error(f"❌ Erreur lors de l'envoi à Elasticsearch : {response.status_code} - {response.text}")
    except Exception as e:
        log.warning(f"⚠️ Impossible de se connecter à Elasticsearch : {e}")

log.info("Appel OpenAI en cours...")
response = call_openai()
result_text = response.choices[0].message.content

# ── Parse ───────────────────────────────────────────────────────────────
try:
    parsed = json.loads(result_text)
except json.JSONDecodeError:
    log.error("Réponse OpenAI non parsable malgré response_format=json_object")
    parsed = {
        "criticite": "UNKNOWN",
        "resume": "Réponse IA non parsable, vérification manuelle requise.",
        "causes": [], "impacts": [], "corrections": [], "patches": {},
    }

# ── Write outputs ───────────────────────────────────────────────────────
with open(os.path.join(BASE_DIR, "ai-report.json"), "w") as f:
    json.dump(parsed, f, indent=2, ensure_ascii=False)

# Sauvegarder les correctifs générés
patches = parsed.get("patches", {})
if patches:
    patches_dir = os.path.join(BASE_DIR, "ai-patches")
    os.makedirs(patches_dir, exist_ok=True)
    for filepath, content in patches.items():
        patch_out = os.path.join(patches_dir, os.path.basename(filepath))
        with open(patch_out, "w") as pf:
            pf.write(content)
        log.info(f"Patch généré : {patch_out}")

# Envoi automatique vers Elasticsearch
send_to_elasticsearch(data, parsed)

log.info("Analyse IA terminée.")
print(json.dumps(parsed, indent=2, ensure_ascii=False))
