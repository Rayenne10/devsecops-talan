#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default or {}

def print_cli_summary(report, scanned_files, build_time):
    level = report.get("criticite", "UNKNOWN")
    ansi = {"HIGH": "\033[91m", "MEDIUM": "\033[93m", "LOW": "\033[92m"}
    reset = "\033[0m"
    bold  = "\033[1m"
    dim   = "\033[2m"
    col   = ansi.get(level, "")
    sep  = "-" * 62
    dsep = "=" * 62

    print()
    print(bold + dsep + reset)
    print(bold + "  AUDIT KUBERNETES -- Plateforme DevSecOps Intelligente" + reset)
    print(dsep)
    print(dim + "  Date     : " + build_time + reset)
    print(dim + "  Fichiers : " + (", ".join(scanned_files) if scanned_files else "N/A") + reset)
    print()

    verdict_map = {
        "HIGH":   col + bold + "  [BLOQUE]  Deploiement interdit -- corrections obligatoires" + reset,
        "MEDIUM": col + bold + "  [RISQUE]  Deploiement deconseille -- revision recommandee" + reset,
        "LOW":    col + bold + "  [OK]      Aucun blocage de politique baseline -- quelques ameliorations possibles" + reset,
    }
    print(verdict_map.get(level, "  Criticite inconnue"))
    print()

    resume = report.get("resume", "")
    if resume:
        words = resume.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 > 58:
                print("  " + line)
                line = word
            else:
                line = (line + " " + word).strip()
        if line:
            print("  " + line)
        print()

    for category in ["causes", "impacts", "corrections"]:
        items = report.get(category, [])
        if items:
            print(sep)
            print(bold + f"  {category.upper()} (" + str(len(items)) + ")" + reset)
            print(sep)
            for i, item in enumerate(items, 1):
                print(f"  {dim}{str(i).zfill(2)}{reset}  {item}")
            print()
    print(dsep)

def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def make_rows(items, with_left_accent=False):
    if not items:
        return "<p style='font-size:13px;color:#888;font-style:italic;padding:10px 0;margin:0;'>Aucun element.</p>"
    accent = "border-left:3px solid #22c55e;" if with_left_accent else ""
    rows = ""
    for i, item in enumerate(items, 1):
        rows += (
            f"<div style='display:flex;gap:12px;align-items:baseline;padding:10px 14px;background:#f8f9fa;border-radius:6px;margin-bottom:6px;{accent}'>"
            f"<span style='font-size:11px;font-weight:500;color:#9ca3af;min-width:20px;flex-shrink:0;'>{str(i).zfill(2)}</span>"
            f"<span style='font-size:14px;color:#1f2937;line-height:1.6;'>{esc(item)}</span>"
            "</div>"
        )
    return rows

def generate_html(report, scanned_files, build_time, out_path):
    level       = report.get("criticite", "UNKNOWN")
    resume      = esc(report.get("resume", ""))
    causes      = report.get("causes", [])
    impacts     = report.get("impacts", [])
    corrections = report.get("corrections", [])

    level_colors = {
        "HIGH":   {"badge_bg": "#fef2f2", "badge_text": "#dc2626", "badge_border": "#fca5a5", "bar": "#ef4444", "verdict": "Deploiement bloque"},
        "MEDIUM": {"badge_bg": "#fff7ed", "badge_text": "#ea580c", "badge_border": "#fdba74", "bar": "#f97316", "verdict": "Deploiement risque"},
        "LOW":    {"badge_bg": "#f0fdf4", "badge_text": "#16a34a", "badge_border": "#86efac", "bar": "#22c55e", "verdict": "Aucun blocage de politique baseline"},
    }
    c = level_colors.get(level, {"badge_bg": "#f9fafb", "badge_text": "#6b7280", "badge_border": "#e5e7eb", "bar": "#9ca3af", "verdict": "Criticite inconnue"})

    files_html = " ".join(f"<code style='background:#f3f4f6;border:1px solid #e5e7eb;border-radius:4px;padding:2px 8px;font-size:12px;color:#374151;font-family:monospace;'>{esc(f)}</code>" for f in scanned_files)

    # Note : Toutes les accolades CSS sont maintenant doublées ({{ et }}) pour ne pas perturber l'f-string
    html = f"""<!DOCTYPE html>
<html lang='fr'>
<head>
<meta charset='UTF-8'/>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f3f4f6;color:#111827;padding:32px 16px;line-height:1.5;}}
.wrap{{max-width:820px;margin:0 auto;}}
.card{{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:24px 28px;margin-bottom:20px;}}
h2{{font-size:13px;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:.6px;margin-bottom:14px;}}
@media(max-width:600px){{body{{padding:16px 10px;}}.card{{padding:16px 14px;}}}}
</style>
</head>
<body>
<div class='wrap'>
<div class='card'>
<div style='display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:12px;'>
<div>
<p style='font-size:18px;font-weight:600;color:#111827;margin-bottom:6px;'>Audit Kubernetes</p>
<p style='font-size:13px;color:#9ca3af;'>{esc(build_time)}</p>
<div style='margin-top:10px;display:flex;flex-wrap:wrap;gap:6px;'>{files_html}</div>
</div>
<span style='background:{c["badge_bg"]};color:{c["badge_text"]};border:1px solid {c["badge_border"]};font-size:12px;font-weight:600;padding:4px 14px;border-radius:99px;'>{level}</span>
</div>
</div>
<div class='card' style='border-left:4px solid {c["bar"]};'>
<p style='font-size:16px;font-weight:600;color:{c["badge_text"]};margin-bottom:8px;'>{c["verdict"]}</p>
<p style='font-size:14px;color:#374151;line-height:1.7;'>{resume}</p>
</div>
<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px;'>
<div class='card' style='text-align:center;padding:20px 16px;'><p style='font-size:32px;font-weight:600;'>{len(causes)}</p><p style='font-size:12px;color:#9ca3af;'>Causes</p></div>
<div class='card' style='text-align:center;padding:20px 16px;'><p style='font-size:32px;font-weight:600;'>{len(impacts)}</p><p style='font-size:12px;color:#9ca3af;'>Impacts</p></div>
<div class='card' style='text-align:center;padding:20px 16px;'><p style='font-size:32px;font-weight:600;'>{len(corrections)}</p><p style='font-size:12px;color:#9ca3af;'>Corrections</p></div>
</div>
<div class='card'><h2>Causes</h2>{make_rows(causes)}</div>
<div class='card'><h2>Impacts</h2>{make_rows(impacts)}</div>
<div class='card'><h2>Corrections</h2>{make_rows(corrections, with_left_accent=True)}</div>
</div>
</body>
</html>"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("Rapport HTML généré : " + out_path)

def main():
    build_time    = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
    report_path   = os.path.join(BASE_DIR, "ai-report.json")
    analysis_path = os.path.join(BASE_DIR, "analysis.json")
    out_path      = os.path.join(BASE_DIR, "audit-report.html")

    report   = load(report_path,   {})
    analysis = load(analysis_path, {})
    scanned_files = analysis.get("scanned_files", [])

    print_cli_summary(report, scanned_files, build_time)
    generate_html(report, scanned_files, build_time, out_path)

if __name__ == "__main__":
    main()
