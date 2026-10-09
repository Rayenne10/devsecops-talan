import json
import os
import sys
import yaml
import glob
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_json_file(path, default=None):
    if not os.path.exists(path):
        print(f"Attention : {path} introuvable, valeur par défaut utilisée.")
        return default if default is not None else {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else (default or {})
    except json.JSONDecodeError as e:
        print(f"Erreur de parsing JSON dans {path} : {e}")
        return default if default is not None else {}

def load_specific_manifests(file_paths):
    manifests = {}
    for filepath in file_paths:
        abs_path = filepath if os.path.isabs(filepath) else os.path.join(BASE_DIR, filepath)
        if not os.path.exists(abs_path):
            print(f"Attention : manifeste introuvable, ignoré : {abs_path}")
            continue
        with open(abs_path, "r", encoding="utf-8") as f:
            # Correction : Utiliser safe_load_all pour supporter les fichiers multi-documents
            docs = list(yaml.safe_load_all(f))
            # Si le fichier ne contient qu'un seul doc, on le stocke directement, sinon on stocke la liste
            manifests[filepath] = docs[0] if len(docs) == 1 else docs
    return manifests

def load_all_manifests(directory="k8s"):
    manifests = {}
    for filepath in glob.glob(os.path.join(directory, "*.yaml")):
        with open(filepath, "r", encoding="utf-8") as f:
            # Correction : Utiliser safe_load_all pour supporter les fichiers multi-documents
            docs = list(yaml.safe_load_all(f))
            manifests[filepath] = docs[0] if len(docs) == 1 else docs
    return manifests

def main():
    parser = argparse.ArgumentParser(description="Consolidate scan results for AI analysis.")
    parser.add_argument("--files", nargs="*", default=None)
    args = parser.parse_args()

    if args.files:
        print(f"Mode sélectif : {len(args.files)} fichier(s) à analyser.")
        manifest_data = load_specific_manifests(args.files)
    else:
        print("Mode complet : scan de tout le dossier k8s/")
        manifest_data = load_all_manifests(os.path.join(BASE_DIR, "k8s"))

    payload = {
        "kube_linter": load_json_file(os.path.join(BASE_DIR, "kube-linter.json"), default=[]),
        "kube_score": load_json_file(os.path.join(BASE_DIR, "kube-score.json"), default=[]),
        "renovate": load_json_file(os.path.join(BASE_DIR, "renovate.json"), default=[]),
        "manifest": manifest_data,
        "scanned_files": args.files if args.files else list(manifest_data.keys()),
    }

    output_file = os.path.join(BASE_DIR, "analysis.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print("Consolidation terminée : analysis.json généré.")

if __name__ == "__main__":
    main()
