"""
OBS Gap Analysis — HTML Report Generator
Produces 2_Output/OBS_Gap_Analysis.html
Run: python obs_html_report.py
"""

import os, sys, json
sys.stdout.reconfigure(encoding="utf-8")
from rapidfuzz import fuzz

# ── reuse same data from obs_compare ────────────────────────────────────────
STANDARD_ROLES = [
    {"role": "Project Manager",                    "abbr": "PM",    "lob": "SRS+VHC", "mandatory": True},
    {"role": "Project Controller",                 "abbr": "PJC",   "lob": "SRS+VHC", "mandatory": True},
    {"role": "Project Planner",                    "abbr": "PJP",   "lob": "SRS+VHC", "mandatory": True},
    {"role": "Project Engineer",                   "abbr": "PE",    "lob": "SRS+VHC", "mandatory": True},
    {"role": "Contract Manager",                   "abbr": "CM",    "lob": "SRS+VHC", "mandatory": True},
    {"role": "Project Quality Manager",            "abbr": "PQM",   "lob": "SRS+VHC", "mandatory": True},
    {"role": "HSE Referent / HSE Manager",         "abbr": "HSE",   "lob": "SRS+VHC", "mandatory": True},
    {"role": "Project RAMS Manager",               "abbr": "PRAMS", "lob": "SRS",     "mandatory": False},
    {"role": "Supply Chain & Procurement Manager", "abbr": "SCPM",  "lob": "SRS",     "mandatory": False},
    {"role": "Construction / Installation Manager","abbr": "CONSTR","lob": "SRS",     "mandatory": False},
    {"role": "Commissioning / T&C Manager",        "abbr": "COMM",  "lob": "SRS",     "mandatory": False},
    {"role": "Warranty Manager",                   "abbr": "WM",    "lob": "SRS",     "mandatory": False},
    {"role": "Project RAM Manager",                "abbr": "RAM",   "lob": "VHC",     "mandatory": False},
    {"role": "Project Safety Manager",             "abbr": "PSM",   "lob": "VHC",     "mandatory": False},
    {"role": "Project Procurement Manager",        "abbr": "PPM",   "lob": "VHC",     "mandatory": False},
    {"role": "Test Manager",                       "abbr": "TM",    "lob": "VHC",     "mandatory": False},
    {"role": "Project Operations Manager",         "abbr": "POM",   "lob": "VHC",     "mandatory": False},
]

ROLE_KEYWORDS = {
    "Project Manager":                    ["project manager", "pm", "program manager", "programme manager"],
    "Project Controller":                 ["controller", "financial controller", "project controller", "finance"],
    "Project Planner":                    ["planner", "planning", "scheduler"],
    "Project Engineer":                   ["project engineer", "system engineering", "design authority", "pda", "pe"],
    "Contract Manager":                   ["contract manager", "contracts"],
    "Project Quality Manager":            ["quality", "qam", "qa manager", "quality assurance", "qm"],
    "HSE Referent / HSE Manager":         ["hse", "health safety", "safety manager", "wsho", "environmental"],
    "Project RAMS Manager":               ["rams", "ram manager", "rams manager"],
    "Supply Chain & Procurement Manager": ["supply chain", "procurement", "scpm", "sourcing", "pscl"],
    "Construction / Installation Manager":["construction", "installation", "deployment"],
    "Commissioning / T&C Manager":        ["commissioning", "t&c", "test and commissioning", "ivvq", "ival"],
    "Warranty Manager":                   ["warranty"],
    "Project RAM Manager":                ["ram specialist", "ram manager", "reliability"],
    "Project Safety Manager":             ["safety manager", "project safety", "system assurance", "safety architect"],
    "Project Procurement Manager":        ["procurement manager", "ppm"],
    "Test Manager":                       ["test manager"],
    "Project Operations Manager":         ["operations manager"],
}

def manual_r152b_roles():
    return [
        {"title": "Singapore PM",                         "entity": "HR Singapore"},
        {"title": "Singapore Deputy PM",                  "entity": "HR Singapore"},
        {"title": "PMO",                                  "entity": "HR Singapore"},
        {"title": "Financial Controller",                 "entity": "HR Singapore"},
        {"title": "Project Design Authority (PDA)",       "entity": "HR Singapore"},
        {"title": "Interface Manager",                    "entity": "HR Singapore"},
        {"title": "Configuration Manager",                "entity": "HR Singapore"},
        {"title": "Contract Manager",                     "entity": "HR Singapore"},
        {"title": "Project Admin",                        "entity": "HR Singapore"},
        {"title": "Document Controller",                  "entity": "HR Singapore"},
        {"title": "Planner",                              "entity": "HR Singapore"},
        {"title": "System Engineering Manager",           "entity": "HR Singapore"},
        {"title": "HW Design Lead",                       "entity": "HR Singapore"},
        {"title": "Deployment Manager",                   "entity": "HR Singapore"},
        {"title": "T&C Manager (Test & Commissioning)",   "entity": "HR Singapore"},
        {"title": "Supply Chain Manager",                 "entity": "HR Singapore"},
        {"title": "Senior Supply Chain Manager",          "entity": "HR Singapore"},
        {"title": "Supply Chain Executive",               "entity": "HR Singapore"},
        {"title": "Project Procurement Manager",          "entity": "HR Singapore"},
        {"title": "PO Admin",                             "entity": "HR Singapore"},
        {"title": "Sourcing & Contracting",               "entity": "HR Singapore"},
        {"title": "Supplier Performance",                 "entity": "HR Singapore"},
        {"title": "DLP Manager",                          "entity": "HR Singapore"},
        {"title": "DLP Engineer",                         "entity": "HR Singapore"},
        {"title": "Installation Lead",                    "entity": "HR Singapore"},
        {"title": "HSE Manager",                          "entity": "HR Singapore"},
        {"title": "WSHO Officer",                         "entity": "HR Singapore"},
        {"title": "Environmental Control Officer",        "entity": "HR Singapore"},
        {"title": "Technical Safety Specialist",          "entity": "HR Singapore"},
        {"title": "Local System Assurance Manager",       "entity": "HR Singapore"},
        {"title": "DCS Lead",                             "entity": "HR Singapore"},
        {"title": "Software Engineers",                   "entity": "HR Singapore"},
        {"title": "Warranty",                             "entity": "HR Singapore"},
        {"title": "RAM Specialist",                       "entity": "HR Singapore"},
        {"title": "IVAL Specialist (IV&V)",               "entity": "HR Singapore"},
        {"title": "Safety Engineering Specialists",       "entity": "HR Singapore"},
        {"title": "Chief Safety Architect",               "entity": "HR Singapore"},
        {"title": "Safety Assurance Specialist",          "entity": "HR Singapore"},
        {"title": "Quality Assurance Manager",            "entity": "HR Singapore"},
        {"title": "France PM",                            "entity": "HR France"},
        {"title": "PMO",                                  "entity": "HR France"},
        {"title": "Financial Controller",                 "entity": "HR France"},
        {"title": "System Engineering & Software Manager","entity": "HR France"},
        {"title": "Configuration & Documentation Manager","entity": "HR France"},
        {"title": "PDA (Project Design Authority)",       "entity": "HR France"},
        {"title": "Quality Assurance Manager",            "entity": "HR France"},
        {"title": "PPM (Project Programme Manager)",      "entity": "HR France"},
        {"title": "RAMS Manager",                         "entity": "HR France"},
        {"title": "Technical Safety Specialist",          "entity": "HR France"},
        {"title": "Canada PM",                            "entity": "HR Canada"},
        {"title": "Financial Controller",                 "entity": "HR Canada"},
        {"title": "Planner",                              "entity": "HR Canada"},
        {"title": "PPM/PSCL (Programme & Supply Chain Lead)", "entity": "Programme"},
        {"title": "System Assurance Manager",             "entity": "Programme"},
        {"title": "System Engineering Manager",           "entity": "Programme"},
        {"title": "Deployment Manager",                   "entity": "Programme"},
        {"title": "Project Safety Manager",               "entity": "Programme"},
        {"title": "IVVQ Manager",                         "entity": "Programme"},
        {"title": "Project Design Authority",             "entity": "Programme"},
        {"title": "Quality Assurance Manager",            "entity": "Programme"},
        {"title": "Planner",                              "entity": "Programme"},
        {"title": "RAMS Manager",                         "entity": "Programme"},
    ]

PROJECTS = [
    {
        "id":       "r152b",
        "name":     "R152B SA1 URS",
        "subtitle": "Urban Rail Singapore — Signalling System",
        "source":   "R152B SA1 URS_Project OBSFinal (1).pdf",
        "entities": ["HR Singapore", "HR France", "HR Canada"],
        "lob":      "SRS",
        "date":     "2026-06-17",
        "roles":    manual_r152b_roles(),
    },
    # ── paste additional projects here ──────────────────────────────────────
]

# ── matching ─────────────────────────────────────────────────────────────────
S_MATCH   = "matched"
S_PARTIAL = "partial"
S_MISSING = "missing"

def match_role(standard_role, obs_roles):
    keywords = ROLE_KEYWORDS.get(standard_role, [standard_role.lower()])
    best_score, best_title, best_entity = 0, "", ""
    for obs in obs_roles:
        t = obs["title"].lower()
        for kw in keywords:
            score = 100 if kw in t else fuzz.partial_ratio(kw, t)
            if score > best_score:
                best_score, best_title, best_entity = score, obs["title"], obs["entity"]
    if best_score >= 90:
        return S_MATCH,   best_title, best_entity, best_score
    elif best_score >= 65:
        return S_PARTIAL, best_title, best_entity, best_score
    else:
        return S_MISSING, "",         "",           best_score

# ── build data for template ───────────────────────────────────────────────────
def build_data():
    rows = []
    for std in STANDARD_ROLES:
        row = {
            "role":      std["role"],
            "abbr":      std["abbr"],
            "lob":       std["lob"],
            "mandatory": std["mandatory"],
            "projects":  [],
        }
        for proj in PROJECTS:
            status, title, entity, score = match_role(std["role"], proj["roles"])
            row["projects"].append({
                "proj_id": proj["id"],
                "status":  status,
                "title":   title,
                "entity":  entity,
                "score":   score,
            })
        rows.append(row)

    scorecards = []
    for pi, proj in enumerate(PROJECTS):
        m = p = miss = mand_hit = 0
        mandatory_n = sum(1 for s in STANDARD_ROLES if s["mandatory"])
        for si, std in enumerate(STANDARD_ROLES):
            st = rows[si]["projects"][pi]["status"]
            if st == S_MATCH:   m += 1
            elif st == S_PARTIAL: p += 1
            else:               miss += 1
            if std["mandatory"] and st in (S_MATCH, S_PARTIAL):
                mand_hit += 1
        pct_mand  = round(mand_hit / mandatory_n * 100)
        pct_total = round((m + p) / len(STANDARD_ROLES) * 100)
        risk = "LOW" if pct_mand >= 85 else "MEDIUM" if pct_mand >= 60 else "HIGH"
        scorecards.append({
            "id":        proj["id"],
            "name":      proj["name"],
            "subtitle":  proj["subtitle"],
            "entities":  proj["entities"],
            "lob":       proj["lob"],
            "matched":   m,
            "partial":   p,
            "missing":   miss,
            "pct_mand":  pct_mand,
            "pct_total": pct_total,
            "risk":      risk,
        })

    # extra roles per project
    all_matched = {proj["id"]: set() for proj in PROJECTS}
    for row in rows:
        for pr in row["projects"]:
            if pr["title"]:
                all_matched[pr["proj_id"]].add(pr["title"].lower())

    extras_per_proj = {}
    for proj in PROJECTS:
        seen, extras = set(), []
        for r in proj["roles"]:
            key = (r["title"].lower(), r["entity"])
            if key in seen: continue
            seen.add(key)
            if r["title"].lower() not in all_matched[proj["id"]]:
                extras.append(r)
        extras_per_proj[proj["id"]] = extras

    return rows, scorecards, extras_per_proj

# ── HTML ──────────────────────────────────────────────────────────────────────
def lob_label(lob):
    return {"SRS+VHC": "Core — SRS &amp; VHC", "SRS": "SRS Only", "VHC": "VHC Only"}.get(lob, lob)

def lob_css(lob):
    return {"SRS+VHC": "lob-core", "SRS": "lob-srs", "VHC": "lob-vhc"}.get(lob, "")

def status_badge(status, title="", entity=""):
    icons = {S_MATCH: "✔", S_PARTIAL: "~", S_MISSING: "✘"}
    labels = {S_MATCH: "Matched", S_PARTIAL: "Partial", S_MISSING: "MISSING"}
    tooltip = f"{title} ({entity})" if title else "Role not found in project OBS"
    return (
        f'<div class="cell-wrap status-{status}" title="{tooltip}">'
        f'  <span class="badge badge-{status}">{icons[status]} {labels[status]}</span>'
        + (f'  <div class="matched-role">{title}<span class="entity-tag">{entity}</span></div>' if title else "")
        + f'</div>'
    )

def render_donut(matched, partial, missing, size=88):
    total = matched + partial + missing or 1
    # SVG donut — 3 segments
    cx = cy = size / 2
    r = size / 2 - 8
    circ = 2 * 3.14159 * r

    def seg(value, offset, color):
        dash = circ * value / total
        gap  = circ - dash
        return (
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="10" stroke-dasharray="{dash:.2f} {gap:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" />'
        )

    off = circ * 0.25  # start from top
    s1_len = circ * matched / total
    s2_len = circ * partial / total
    s1 = seg(matched, off, "#22c55e")
    s2 = seg(partial, off + s1_len, "#f59e0b")
    s3 = seg(missing, off + s1_len + s2_len, "#ef4444")
    pct = round((matched + partial) / total * 100)
    return f"""
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#e5e7eb" stroke-width="10"/>
  {s1}{s2}{s3}
  <text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="16" font-weight="700" fill="#1e3a5f">{pct}%</text>
</svg>"""

def render_bar(pct, color):
    return f"""
<div class="bar-outer">
  <div class="bar-inner" style="width:{pct}%;background:{color};">
    <span class="bar-label">{pct}%</span>
  </div>
</div>"""

def build_html(rows, scorecards, extras_per_proj):
    # scorecard cards
    sc_html = ""
    for sc in scorecards:
        risk_cls = {"LOW": "risk-low", "MEDIUM": "risk-med", "HIGH": "risk-high"}[sc["risk"]]
        sc_html += f"""
<div class="scorecard-card" id="sc-{sc['id']}">
  <div class="sc-header">
    <div class="sc-title">{sc['name']}</div>
    <div class="sc-sub">{sc['subtitle']}</div>
    <div class="sc-meta">
      {''.join(f'<span class="entity-pill">{e}</span>' for e in sc['entities'])}
      <span class="lob-pill">{sc['lob']}</span>
    </div>
  </div>
  <div class="sc-body">
    <div class="sc-donut">{render_donut(sc['matched'], sc['partial'], sc['missing'])}</div>
    <div class="sc-stats">
      <div class="stat-row"><span class="dot dot-green"></span><b>{sc['matched']}</b> Matched</div>
      <div class="stat-row"><span class="dot dot-amber"></span><b>{sc['partial']}</b> Partial</div>
      <div class="stat-row"><span class="dot dot-red"></span><b>{sc['missing']}</b> Missing</div>
    </div>
  </div>
  <div class="sc-bars">
    <div class="bar-label-row">Mandatory roles covered</div>
    {render_bar(sc['pct_mand'],  "#22c55e" if sc['pct_mand']  >= 85 else "#f59e0b" if sc['pct_mand']  >= 60 else "#ef4444")}
    <div class="bar-label-row" style="margin-top:6px">All standard roles covered</div>
    {render_bar(sc['pct_total'], "#22c55e" if sc['pct_total'] >= 75 else "#f59e0b" if sc['pct_total'] >= 50 else "#ef4444")}
  </div>
  <div class="sc-footer">
    Risk Level <span class="risk-badge {risk_cls}">{sc['risk']}</span>
  </div>
</div>"""

    # project column headers
    proj_th = "".join(
        f'<th class="proj-th" data-proj="{p["id"]}">'
        f'  <div class="proj-name">{p["name"]}</div>'
        f'  <div class="proj-sub">{" · ".join(p["entities"][:2])}{"…" if len(p["entities"])>2 else ""}</div>'
        f'</th>'
        for p in PROJECTS
    )

    # group rows by lob section
    lob_order  = ["SRS+VHC", "SRS", "VHC"]
    lob_labels = {"SRS+VHC": "Core Roles — SRS &amp; VHC", "SRS": "SRS-Specific Roles", "VHC": "VHC-Specific Roles"}
    from itertools import groupby

    body_html = ""
    sorted_rows = sorted(rows, key=lambda r: lob_order.index(r["lob"]))
    prev_lob = None
    for row in sorted_rows:
        if row["lob"] != prev_lob:
            colspan = 5 + len(PROJECTS)
            body_html += f'<tr class="section-header"><td colspan="{colspan}">{lob_labels[row["lob"]]}</td></tr>\n'
            prev_lob = row["lob"]

        mand_cls = "mandatory-row" if row["mandatory"] else ""
        mand_badge = '<span class="mand-dot" title="Mandatory">●</span>' if row["mandatory"] else ""
        cells = "".join(status_badge(pr["status"], pr["title"], pr["entity"]) for pr in row["projects"])
        cells_td = "".join(
            f'<td class="status-cell" data-proj="{pr["proj_id"]}" data-status="{pr["status"]}">'
            f'{status_badge(pr["status"], pr["title"], pr["entity"])}'
            f'</td>'
            for pr in row["projects"]
        )

        body_html += f"""<tr class="role-row {mand_cls}" data-lob="{row['lob']}">
  <td class="abbr-cell">{row['abbr']}</td>
  <td class="role-cell">{mand_badge}{row['role']}</td>
  <td class="lob-cell"><span class="lob-tag {lob_css(row['lob'])}">{row['lob']}</span></td>
  <td class="mand-cell">{'Yes' if row['mandatory'] else '—'}</td>
  {cells_td}
</tr>\n"""

    # extras tables per project
    extras_html = ""
    for proj in PROJECTS:
        extras = extras_per_proj[proj["id"]]
        if not extras:
            extras_html += f'<p style="color:#6b7280;font-size:.9rem;">No extra roles found for {proj["name"]}.</p>'
            continue
        rows_html = "".join(
            f'<tr><td>{i+1}</td>'
            f'<td>{e["title"]}</td>'
            f'<td><span class="entity-tag">{e["entity"]}</span></td>'
            f'<td><span class="badge badge-extra">+ Extra / Legacy</span></td></tr>'
            for i, e in enumerate(extras)
        )
        extras_html += f"""
<h3 style="margin:1.5rem 0 .5rem;color:#1e3a5f;">{proj['name']}</h3>
<table class="extras-table">
  <thead><tr><th>#</th><th>Role in OBS</th><th>Entity</th><th>Classification</th></tr></thead>
  <tbody>{rows_html}</tbody>
</table>"""

    # structural highlights
    highlights = """
<div class="highlights-grid">
  <div class="hl-card hl-warn">
    <div class="hl-icon">⚠</div>
    <div>
      <b>Multiple Project Managers</b><br>
      R152B has Singapore PM, France PM, Canada PM as separate leads.
      G-TRN standard requires <b>one single PM</b>; others should be structured as WPM/WPL.
    </div>
  </div>
  <div class="hl-card hl-info">
    <div class="hl-icon">ℹ</div>
    <div>
      <b>Role Naming Mismatch</b><br>
      "Financial Controller" (OBS) → G-TRN calls this <b>"Project Controller"</b>.
      Scope and accountability should be aligned to the new standard.
    </div>
  </div>
  <div class="hl-card hl-info">
    <div class="hl-icon">ℹ</div>
    <div>
      <b>Partial Match — Construction Manager</b><br>
      "Deployment Manager" covers installation activities but is named differently.
      Consider aligning title to G-TRN "Construction / Installation Manager".
    </div>
  </div>
  <div class="hl-card hl-ok">
    <div class="hl-icon">✔</div>
    <div>
      <b>Strong Core Coverage</b><br>
      All 7 mandatory core roles are covered (100% mandatory compliance).
      All SRS-specific roles have at least a partial match.
    </div>
  </div>
  <div class="hl-card hl-neutral">
    <div class="hl-icon">📋</div>
    <div>
      <b>Legacy GTS Roles Present</b><br>
      IVVQ Manager, System Assurance Manager, PDA, DCS Lead are legacy GTS roles
      with no direct G-TRN equivalent. Retain for now; map to WPM/WPL structure in future.
    </div>
  </div>
  <div class="hl-card hl-neutral">
    <div class="hl-icon">📋</div>
    <div>
      <b>VHC Roles — Not Applicable</b><br>
      This is an SRS project. VHC-specific roles (RAM Manager, Test Manager, etc.)
      are shown for completeness but are not required.
    </div>
  </div>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>OBS Gap Analysis — G-TRN A08001 vs Projects</title>
<style>
/* ── reset & base ───────────────────────────────────────────────────────── */
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"Segoe UI",system-ui,sans-serif;background:#f1f5f9;color:#1e293b;font-size:14px;line-height:1.5}}
a{{color:#2563eb;text-decoration:none}}

/* ── page chrome ────────────────────────────────────────────────────────── */
.page-header{{background:linear-gradient(135deg,#0f2d5a 0%,#1e4d8c 60%,#1d6fa6 100%);
  color:#fff;padding:2.5rem 3rem 2rem;position:sticky;top:0;z-index:100;
  box-shadow:0 4px 20px rgba(0,0,0,.35)}}
.page-header h1{{font-size:1.65rem;font-weight:700;letter-spacing:-.01em}}
.page-header p{{font-size:.9rem;opacity:.8;margin-top:.3rem}}
.header-meta{{display:flex;gap:1.5rem;margin-top:1rem;flex-wrap:wrap}}
.meta-pill{{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.25);
  border-radius:20px;padding:.25rem .9rem;font-size:.8rem;font-weight:600}}

/* ── nav ────────────────────────────────────────────────────────────────── */
.nav-bar{{background:#fff;border-bottom:1px solid #e2e8f0;
  display:flex;gap:0;padding:0 3rem;position:sticky;top:0;z-index:99;
  box-shadow:0 1px 4px rgba(0,0,0,.06)}}
.nav-bar a{{padding:.75rem 1.25rem;font-size:.85rem;font-weight:600;color:#475569;
  border-bottom:3px solid transparent;transition:all .2s;white-space:nowrap}}
.nav-bar a:hover,.nav-bar a.active{{color:#1e4d8c;border-bottom-color:#1e4d8c}}

/* ── main wrapper ───────────────────────────────────────────────────────── */
.main{{max-width:1400px;margin:0 auto;padding:2rem 2rem 4rem}}
section{{margin-bottom:3rem}}
section h2{{font-size:1.2rem;font-weight:700;color:#0f2d5a;margin-bottom:1.25rem;
  padding-bottom:.5rem;border-bottom:2px solid #e2e8f0;display:flex;align-items:center;gap:.5rem}}
section h2::before{{content:"";display:block;width:4px;height:1.2em;
  background:linear-gradient(180deg,#1e4d8c,#1d6fa6);border-radius:2px}}

/* ── scorecard row ──────────────────────────────────────────────────────── */
.scorecard-row{{display:flex;gap:1.5rem;flex-wrap:wrap}}
.scorecard-card{{background:#fff;border-radius:14px;padding:1.5rem;
  flex:1;min-width:280px;max-width:380px;
  box-shadow:0 2px 12px rgba(0,0,0,.07);border:1px solid #e2e8f0}}
.sc-header{{margin-bottom:1rem}}
.sc-title{{font-size:1.1rem;font-weight:700;color:#0f2d5a}}
.sc-sub{{font-size:.8rem;color:#64748b;margin:.2rem 0 .6rem}}
.sc-meta{{display:flex;flex-wrap:wrap;gap:.35rem}}
.entity-pill{{background:#eff6ff;color:#1d4ed8;border-radius:10px;
  padding:.15rem .65rem;font-size:.72rem;font-weight:600}}
.lob-pill{{background:#f0fdf4;color:#16a34a;border-radius:10px;
  padding:.15rem .65rem;font-size:.72rem;font-weight:600}}
.sc-body{{display:flex;align-items:center;gap:1.25rem;margin-bottom:1rem}}
.sc-donut svg{{flex-shrink:0}}
.sc-stats{{display:flex;flex-direction:column;gap:.4rem}}
.stat-row{{display:flex;align-items:center;gap:.5rem;font-size:.85rem}}
.dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.dot-green{{background:#22c55e}}.dot-amber{{background:#f59e0b}}.dot-red{{background:#ef4444}}
.sc-bars{{margin-bottom:1rem}}
.bar-label-row{{font-size:.75rem;color:#64748b;margin-bottom:.3rem}}
.bar-outer{{background:#f1f5f9;border-radius:6px;height:22px;overflow:hidden}}
.bar-inner{{height:100%;border-radius:6px;display:flex;align-items:center;
  transition:width .6s ease;min-width:28px}}
.bar-label{{font-size:.72rem;font-weight:700;color:#fff;padding:0 .5rem}}
.sc-footer{{border-top:1px solid #f1f5f9;padding-top:.75rem;font-size:.8rem;
  color:#64748b;display:flex;align-items:center;gap:.5rem}}
.risk-badge{{padding:.2rem .75rem;border-radius:12px;font-size:.78rem;font-weight:700}}
.risk-low{{background:#dcfce7;color:#15803d}}
.risk-med{{background:#fef9c3;color:#92400e}}
.risk-high{{background:#fee2e2;color:#b91c1c}}

/* ── filter bar ─────────────────────────────────────────────────────────── */
.filter-bar{{display:flex;flex-wrap:wrap;gap:.75rem;margin-bottom:1.25rem;align-items:center}}
.filter-bar input{{flex:1;min-width:180px;padding:.55rem .9rem;border:1px solid #cbd5e1;
  border-radius:8px;font-size:.85rem;outline:none;transition:border .2s}}
.filter-bar input:focus{{border-color:#1e4d8c;box-shadow:0 0 0 3px rgba(30,77,140,.12)}}
.filter-btn{{padding:.5rem 1rem;border-radius:8px;font-size:.8rem;font-weight:600;cursor:pointer;
  border:1px solid #cbd5e1;background:#fff;color:#475569;transition:all .2s}}
.filter-btn.active,.filter-btn:hover{{border-color:#1e4d8c;background:#eff6ff;color:#1e4d8c}}
.filter-btn.btn-matched.active{{background:#dcfce7;border-color:#22c55e;color:#15803d}}
.filter-btn.btn-partial.active{{background:#fffbeb;border-color:#f59e0b;color:#92400e}}
.filter-btn.btn-missing.active{{background:#fee2e2;border-color:#ef4444;color:#b91c1c}}
.filter-count{{font-size:.8rem;color:#94a3b8}}

/* ── gap table ──────────────────────────────────────────────────────────── */
.table-wrap{{overflow-x:auto;border-radius:12px;
  box-shadow:0 2px 16px rgba(0,0,0,.08);border:1px solid #e2e8f0}}
table.gap-table{{width:100%;border-collapse:collapse;background:#fff;font-size:.84rem}}
.gap-table thead th{{background:#0f2d5a;color:#fff;font-weight:600;padding:.8rem .9rem;
  text-align:left;white-space:nowrap;position:sticky;top:0;z-index:10}}
.gap-table thead th.proj-th{{background:#1e4d8c;min-width:230px}}
.proj-name{{font-weight:700;font-size:.88rem}}
.proj-sub{{font-size:.72rem;opacity:.75;margin-top:.15rem}}

.section-header td{{background:#1e4d8c;color:#fff;font-weight:700;padding:.55rem 1rem;
  font-size:.82rem;letter-spacing:.04em;text-transform:uppercase}}
.role-row{{border-bottom:1px solid #f1f5f9;transition:background .15s}}
.role-row:hover{{background:#f8faff}}
.role-row.mandatory-row{{background:#fffdf0}}
.role-row.mandatory-row:hover{{background:#fef9c3}}
.role-row.hidden{{display:none}}

.abbr-cell{{color:#64748b;font-weight:600;font-size:.78rem;padding:.75rem .5rem .75rem .9rem;white-space:nowrap}}
.role-cell{{padding:.75rem .75rem;font-weight:500;min-width:210px}}
.lob-cell,.mand-cell{{padding:.75rem .6rem;text-align:center}}
.mand-dot{{color:#f59e0b;font-size:1rem;margin-right:.3rem;cursor:help}}
.status-cell{{padding:.5rem .6rem;vertical-align:top}}

.lob-tag{{display:inline-block;border-radius:6px;padding:.1rem .5rem;font-size:.72rem;font-weight:700}}
.lob-core{{background:#dbeafe;color:#1d4ed8}}
.lob-srs{{background:#dcfce7;color:#15803d}}
.lob-vhc{{background:#fce7f3;color:#9d174d}}

/* ── status cells ───────────────────────────────────────────────────────── */
.cell-wrap{{border-radius:8px;padding:.45rem .6rem;font-size:.8rem}}
.status-matched  .cell-wrap{{background:#f0fdf4}}
.status-partial  .cell-wrap{{background:#fffbeb}}
.status-missing  .cell-wrap{{background:#fff1f2}}
.badge{{display:inline-block;border-radius:6px;padding:.15rem .55rem;
  font-size:.72rem;font-weight:700;margin-bottom:.2rem}}
.badge-matched{{background:#dcfce7;color:#15803d}}
.badge-partial{{background:#fef9c3;color:#854d0e}}
.badge-missing{{background:#fee2e2;color:#b91c1c}}
.badge-extra{{background:#dbeafe;color:#1d4ed8}}
.matched-role{{font-size:.78rem;color:#374151;margin-top:.15rem;line-height:1.3}}
.entity-tag{{display:inline-block;margin-left:.4rem;background:#f1f5f9;color:#64748b;
  border-radius:4px;padding:.05rem .4rem;font-size:.7rem}}

/* ── highlights ─────────────────────────────────────────────────────────── */
.highlights-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1rem}}
.hl-card{{display:flex;gap:.9rem;align-items:flex-start;background:#fff;
  border-radius:12px;padding:1.1rem 1.25rem;
  box-shadow:0 1px 6px rgba(0,0,0,.06);border:1px solid #e2e8f0;font-size:.84rem;line-height:1.55}}
.hl-icon{{font-size:1.4rem;flex-shrink:0;margin-top:.05rem}}
.hl-warn{{border-left:4px solid #f59e0b}}
.hl-info{{border-left:4px solid #3b82f6}}
.hl-ok  {{border-left:4px solid #22c55e}}
.hl-neutral{{border-left:4px solid #94a3b8}}

/* ── extras table ───────────────────────────────────────────────────────── */
.extras-table{{width:100%;border-collapse:collapse;font-size:.84rem;background:#fff;
  border-radius:10px;overflow:hidden;box-shadow:0 1px 8px rgba(0,0,0,.06)}}
.extras-table th{{background:#1e4d8c;color:#fff;padding:.65rem 1rem;text-align:left;font-weight:600}}
.extras-table td{{padding:.6rem 1rem;border-bottom:1px solid #f1f5f9}}
.extras-table tr:last-child td{{border-bottom:none}}
.extras-table tr:hover td{{background:#f8faff}}

/* ── legend ─────────────────────────────────────────────────────────────── */
.legend-grid{{display:flex;flex-wrap:wrap;gap:1rem}}
.legend-item{{display:flex;align-items:center;gap:.6rem;font-size:.84rem}}
.legend-swatch{{width:28px;height:16px;border-radius:4px}}

/* ── footer ─────────────────────────────────────────────────────────────── */
.footer{{text-align:center;color:#94a3b8;font-size:.78rem;margin-top:3rem;padding:1.5rem;
  border-top:1px solid #e2e8f0}}

/* ── print ──────────────────────────────────────────────────────────────── */
@media print{{
  .nav-bar,.filter-bar,.page-header{{position:static}}
  .table-wrap{{box-shadow:none;border:1px solid #ccc}}
  body{{background:#fff}}
}}
</style>
</head>
<body>

<!-- ── HEADER ─────────────────────────────────────────────────────────── -->
<div class="page-header">
  <h1>OBS Gap Analysis</h1>
  <p>G-TRN A08001 · RSBU Project Team Organisation Standard vs Existing Project OBS</p>
  <div class="header-meta">
    <span class="meta-pill">Standard: G-TRN A08001 Rev.00 · April 2026</span>
    <span class="meta-pill">Projects compared: {len(PROJECTS)}</span>
    <span class="meta-pill">Standard roles: {len(STANDARD_ROLES)}</span>
    <span class="meta-pill">Report date: 2026-06-17</span>
  </div>
</div>

<!-- ── NAV ────────────────────────────────────────────────────────────── -->
<nav class="nav-bar">
  <a href="#scorecard" class="active">Scorecard</a>
  <a href="#highlights">Key Findings</a>
  <a href="#matrix">Gap Matrix</a>
  <a href="#extras">Extra Roles</a>
  <a href="#legend">Legend</a>
</nav>

<div class="main">

<!-- ── SCORECARD ──────────────────────────────────────────────────────── -->
<section id="scorecard">
  <h2>Compliance Scorecard</h2>
  <div class="scorecard-row">
    {sc_html}
  </div>
</section>

<!-- ── HIGHLIGHTS ─────────────────────────────────────────────────────── -->
<section id="highlights">
  <h2>Key Findings &amp; Recommendations</h2>
  {highlights}
</section>

<!-- ── GAP MATRIX ─────────────────────────────────────────────────────── -->
<section id="matrix">
  <h2>Gap Analysis Matrix</h2>
  <div class="filter-bar">
    <input type="text" id="roleSearch" placeholder="🔍  Search role name…" oninput="filterTable()"/>
    <button class="filter-btn" onclick="filterLob('all',this)">All LoB</button>
    <button class="filter-btn" onclick="filterLob('SRS+VHC',this)">Core</button>
    <button class="filter-btn" onclick="filterLob('SRS',this)">SRS</button>
    <button class="filter-btn" onclick="filterLob('VHC',this)">VHC</button>
    <button class="filter-btn btn-missing" onclick="filterStatus('missing',this)">Show gaps only</button>
    <button class="filter-btn btn-matched" onclick="filterStatus('all',this)">Show all</button>
    <span class="filter-count" id="rowCount"></span>
  </div>
  <div class="table-wrap">
    <table class="gap-table" id="gapTable">
      <thead>
        <tr>
          <th style="width:52px">Abbr</th>
          <th style="min-width:210px">G-TRN Standard Role</th>
          <th>LoB</th>
          <th>Mandatory</th>
          {proj_th}
        </tr>
      </thead>
      <tbody id="gapBody">
        {body_html}
      </tbody>
    </table>
  </div>
</section>

<!-- ── EXTRA ROLES ─────────────────────────────────────────────────────── -->
<section id="extras">
  <h2>Extra Roles in Project OBS <small style="font-weight:400;font-size:.85rem;color:#64748b">(no direct G-TRN standard equivalent)</small></h2>
  <p style="font-size:.84rem;color:#64748b;margin-bottom:1rem">
    These roles exist in the project OBS but are not part of the G-TRN A08001 standard.
    They may be legacy GTS roles, project-specific sub-roles, or support functions.
    Review each and decide: map to a WPM/WPL in the standard hierarchy, or retain as project-tailored roles.
  </p>
  {extras_html}
</section>

<!-- ── LEGEND ─────────────────────────────────────────────────────────── -->
<section id="legend">
  <h2>Legend</h2>
  <div class="legend-grid">
    <div class="legend-item"><div class="legend-swatch" style="background:#dcfce7;border:1px solid #bbf7d0"></div><b>✔ Matched</b> — Role name or keyword directly found in project OBS (score ≥ 90%)</div>
    <div class="legend-item"><div class="legend-swatch" style="background:#fef9c3;border:1px solid #fde68a"></div><b>~ Partial</b> — Similar role exists with a different name or scope — align to G-TRN naming</div>
    <div class="legend-item"><div class="legend-swatch" style="background:#fee2e2;border:1px solid #fecaca"></div><b>✘ Missing</b> — Standard role has no equivalent in OBS — this is a GAP to be addressed</div>
    <div class="legend-item"><div class="legend-swatch" style="background:#dbeafe;border:1px solid #bfdbfe"></div><b>+ Extra</b> — Role in project OBS with no G-TRN standard equivalent (legacy / project-specific)</div>
    <div class="legend-item"><div class="legend-swatch" style="background:#fffdf0;border:1px solid #fde68a"></div><b>Yellow row</b> — Mandatory core role required for ALL projects (SRS and VHC)</div>
  </div>
</section>

</div><!-- /main -->

<div class="footer">
  Generated by obs_html_report.py · Hitachi Rail — PMO · Report date: 2026-06-17
</div>

<script>
// ── nav highlight on scroll ───────────────────────────────────────────────
const sections = document.querySelectorAll('section[id]');
const navLinks  = document.querySelectorAll('.nav-bar a');
window.addEventListener('scroll', () => {{
  let current = '';
  sections.forEach(s => {{ if (window.scrollY >= s.offsetTop - 120) current = s.id; }});
  navLinks.forEach(a => {{
    a.classList.toggle('active', a.getAttribute('href') === '#' + current);
  }});
}}, {{passive: true}});

// ── smooth nav ────────────────────────────────────────────────────────────
navLinks.forEach(a => a.addEventListener('click', e => {{
  e.preventDefault();
  document.querySelector(a.getAttribute('href'))
    .scrollIntoView({{behavior:'smooth', block:'start'}});
}}));

// ── table filtering ───────────────────────────────────────────────────────
let activeStatus = 'all';
let activeLob    = 'all';

function filterTable() {{
  const q = document.getElementById('roleSearch').value.toLowerCase();
  const rows = document.querySelectorAll('#gapBody tr.role-row');
  let visible = 0;
  rows.forEach(row => {{
    const roleName  = row.querySelector('.role-cell').textContent.toLowerCase();
    const lob       = row.dataset.lob;
    const cells     = row.querySelectorAll('td.status-cell');
    const hasStatus = activeStatus === 'all'
      || Array.from(cells).some(c => c.dataset.status === activeStatus);
    const lobOk  = activeLob === 'all' || lob === activeLob;
    const textOk = q === '' || roleName.includes(q);
    const show   = lobOk && textOk && hasStatus;
    row.classList.toggle('hidden', !show);
    if (show) visible++;
  }});
  document.getElementById('rowCount').textContent =
    visible + ' role' + (visible !== 1 ? 's' : '') + ' shown';
}}

function filterLob(lob, btn) {{
  activeLob = lob;
  document.querySelectorAll('.filter-bar .filter-btn').forEach(b => {{
    if (['All LoB','Core','SRS','VHC'].includes(b.textContent)) b.classList.remove('active');
  }});
  btn.classList.add('active');
  filterTable();
}}

function filterStatus(status, btn) {{
  activeStatus = status;
  document.querySelectorAll('.filter-bar .filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  filterTable();
}}

// init count
filterTable();
</script>
</body>
</html>"""

# ── entry point ───────────────────────────────────────────────────────────────
def main():
    out_dir = r"\\spiderman\DEPARTMENTS\Project_Management_Office\Artificial_Intelligence\26_OBS Compare\2_Output"
    os.makedirs(out_dir, exist_ok=True)
    rows, scorecards, extras = build_data()
    html = build_html(rows, scorecards, extras)
    out = os.path.join(out_dir, "OBS_Gap_Analysis.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✔  Saved: {out}")

if __name__ == "__main__":
    main()
