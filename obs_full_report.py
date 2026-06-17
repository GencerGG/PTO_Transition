"""
CBTC PTO Gap Analysis — Full Executive HTML Report
Covers : 18 active execution projects vs G-TRN A08001 standard
Output : 2_Output/CBTC_PTO_Gap_Analysis.html
Run    : python obs_full_report.py
"""
import os, sys, re
sys.stdout.reconfigure(encoding="utf-8")
from rapidfuzz import fuzz

# ═══════════════════════════════════════════════════════════════════════════
# 1. G-TRN A08001 STANDARD ROLES
# ═══════════════════════════════════════════════════════════════════════════
STANDARD_ROLES = [
    {"role": "Project Manager",                     "abbr": "PM",     "lob": "SRS+VHC", "mandatory": True},
    {"role": "Project Controller",                  "abbr": "PJC",    "lob": "SRS+VHC", "mandatory": True},
    {"role": "Project Planner",                     "abbr": "PJP",    "lob": "SRS+VHC", "mandatory": True},
    {"role": "Project Engineer / SEM",              "abbr": "PE",     "lob": "SRS+VHC", "mandatory": True},
    {"role": "Contract Manager",                    "abbr": "CM",     "lob": "SRS+VHC", "mandatory": True},
    {"role": "Project Quality Manager",             "abbr": "PQM",    "lob": "SRS+VHC", "mandatory": True},
    {"role": "HSE Referent / HSE Manager",          "abbr": "HSE",    "lob": "SRS+VHC", "mandatory": True},
    {"role": "Project RAMS Manager",                "abbr": "PRAMS",  "lob": "SRS",     "mandatory": False},
    {"role": "Supply Chain & Procurement Mgr",      "abbr": "SCPM",   "lob": "SRS",     "mandatory": False},
    {"role": "Construction / Installation Mgr",     "abbr": "CONSTR", "lob": "SRS",     "mandatory": False},
    {"role": "Commissioning / T&C Manager",         "abbr": "COMM",   "lob": "SRS",     "mandatory": False},
    {"role": "Warranty Manager",                    "abbr": "WM",     "lob": "SRS",     "mandatory": False},
]

ROLE_KEYWORDS = {
    "Project Manager":                ["project manager", "programme manager", "program manager", "gpm", "general project manager", "project director"],
    "Project Controller":             ["controller", "financial controller", "project controller", "cost control", "finance"],
    "Project Planner":                ["planner", "planning manager", "planning engineer", "scheduler"],
    "Project Engineer / SEM":         ["project engineer", "system engineering", "design authority", "pda", "solution engineering manager", "sem", "technical lead"],
    "Contract Manager":               ["contract manager", "contracts", "commercial"],
    "Project Quality Manager":        ["quality", "qa manager", "quality assurance", "quality manager", "qm"],
    "HSE Referent / HSE Manager":     ["hse", "health safety", "safety manager", "wsho", "environmental", "site safety officer"],
    "Project RAMS Manager":           ["rams", "ram manager", "ram engineer", "reliability", "safety assurance"],
    "Supply Chain & Procurement Mgr": ["supply chain", "procurement manager", "scpm", "sourcing", "pscl", "procurement"],
    "Construction / Installation Mgr":["construction", "installation", "deployment manager", "deployment project"],
    "Commissioning / T&C Manager":    ["commissioning", "t&c", "test and commissioning", "ivvq", "tic manager", "t&c manager"],
    "Warranty Manager":               ["warranty", "dlp manager", "customer service manager"],
}

# Roles whose titles MUST NOT be matched to a given PTO standard role.
# Prevents fuzzy false-positives (e.g. 'ITV Manager' → 'Project Manager').
ROLE_ANTI_KEYWORDS = {
    "Project Manager": [
        "controller", "financial", "planner", "planning",
        "quality", "hse", "safety manager", "safety assurance",
        "procurement", "supply chain", "commissioning", "t&c",
        "ivvq", "itv", "warranty", "engineering manager",
        "deployment manager", "deployment project",
        "documentation", "contract manager", "project office",
        "rams manager", "ram engineer",
    ],
    "Project Planner": [
        "quality", "financial", "controller", "hse",
        "procurement", "commissioning", "safety",
        "engineering manager", "deployment", "warranty",
        "contract manager", "itv", "ivvq",
    ],
    "Project Quality Manager": [
        "controller", "financial", "planner", "planning",
        "hse", "safety engineer", "rams", "procurement",
        "commissioning", "engineering manager", "deployment",
        "itv", "ivvq",
    ],
    "HSE Referent / HSE Manager": [
        "controller", "planner", "quality", "contract manager",
        "procurement", "commissioning", "warranty",
        "engineering manager", "deployment manager",
        "itv", "ivvq",
    ],
    "Contract Manager": [
        "controller", "planner", "quality", "hse",
        "procurement", "commissioning", "warranty",
        "engineering manager", "deployment", "project manager",
        "itv", "ivvq",
    ],
    "Construction / Installation Mgr": [
        "itv", "ivvq", "quality", "hse", "contract", "financial",
        "planning", "engineering manager",
    ],
    "Commissioning / T&C Manager": [
        "itv", "ivvq", "quality", "hse", "contract", "financial",
        "planning", "engineering manager",
    ],
}

S_MATCH   = "matched"
S_PARTIAL = "partial"
S_MISSING = "missing"
S_EXTRA   = "extra"

def match_role(standard_role, obs_roles):
    keywords = ROLE_KEYWORDS.get(standard_role, [standard_role.lower()])
    anti_kws  = ROLE_ANTI_KEYWORDS.get(standard_role, [])
    best_score, best_title, best_entity = 0, "", ""
    for obs in obs_roles:
        t = obs["title"].lower()
        if any(ak in t for ak in anti_kws):          # skip roles that can’t match this standard
            continue
        for kw in keywords:
            score = 100 if kw in t else fuzz.partial_ratio(kw, t)
            if score > best_score:
                best_score, best_title, best_entity = score, obs["title"], obs["entity"]
    if best_score >= 88:  return S_MATCH,   best_title, best_entity, best_score
    elif best_score >= 62: return S_PARTIAL, best_title, best_entity, best_score
    else:                  return S_MISSING, "",         "",           best_score

def find_all_pm_roles(obs_roles):
    """Return every obs_role that semantically covers a PM / Project Director position.
    3-step logic:
      1. Whitelist: unambiguous PM titles, bypass anti-keywords (but not sub-PM overrides)
      2. Anti-keywords: skip known non-PM roles
      3. Fuzzy: limited keyword set — 'program manager' excluded to prevent
         fuzz.partial_ratio('program manager','ram manager')==100 false positive
    """
    PM_WHITELIST = [
        "project manager", "programme manager", "program manager",
        "general project manager", "project director",
        "associate project manager", "associate pm",
        "general pm", "project gm",
    ]
    # Sub-PM roles that contain a whitelist keyword but are NOT PM-level
    PM_WHITELIST_OVERRIDE = [
        "deployment project manager", "deployment programme manager",
        "procurement project manager",
        "deputy project manager", "deputy pm", "deputy programme manager",
        "ppm (project programme manager)", "project programme manager",
        "associate programme manager",
    ]
    # Fuzzy keywords: excludes "program manager" to prevent RAM Manager false positive
    FUZZY_PM_KWS = ["project manager", "programme manager", "gpm",
                    "general project manager", "project director"]
    anti_kws = ROLE_ANTI_KEYWORDS["Project Manager"]
    hits = []
    for obs in obs_roles:
        t = obs["title"].lower()
        # Step 1 — whitelist (bypass anti-keywords for unambiguous PM titles)
        if any(kw in t for kw in PM_WHITELIST):
            if not any(ok in t for ok in PM_WHITELIST_OVERRIDE):
                hits.append(obs)
            continue  # Skip steps 2+3 whether added or overridden
        # Step 2 — anti-keywords (skip non-PM roles)
        if any(ak in t for ak in anti_kws):
            continue
        # Step 3 — limited fuzzy (GPM, legacy titles)
        for kw in FUZZY_PM_KWS:
            score = 100 if kw in t else fuzz.partial_ratio(kw, t)
            if score >= 88:
                hits.append(obs)
                break
    return hits

# ═══════════════════════════════════════════════════════════════════════════
# 2. ALL PROJECT DEFINITIONS
# priority=True  → gold-highlighted in report (21 key projects per PMO list)
# pending=True   → no OBS file available yet; shown as 'Data Pending'
# ═══════════════════════════════════════════════════════════════════════════
def R(title, entity, name=""):
    return {"title": title, "entity": entity, "name": name}

PENDING = []  # roles list for projects with no OBS data yet

PROJECTS = [
    # ── AMERICAS – NORTH AMERICA ────────────────────────────────────────
    {
        "id": "crosstown", "name": "Crosstown LRT", "short": "Crosstown",
        "priority": True,
        "region": "Americas – NA", "city": "Toronto, Canada",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR Canada (Local Delivery)",
        "source": "ORG Chart Crosstown_2026_updated GLD.pdf", "date": "Apr 2026",
        "phase": "Execution",
        "rationale": "Major Canadian CBTC project. Offshore PD model with Deputy PM onshore. Multiple safety/assurance layers reflecting Toronto Metrolinx requirements. Legacy GTS structure with Project Director above PM.",
        "wf_category": "partial",
        "wf_action": "Confirm single PM accountability. Map Project Director to functional management. Formalize Project Controller role (currently Finance/Cost Controller). Align Safety Manager to RAMS scope per G-TRN.",
        "maturity": {"tech": 5, "tools": 4, "resources": 5, "customer": 5, "structure": 3},
        "roles": [
            R("General Project Manager / Project Director","HR Canada"),
            R("Deputy PM","HR Canada"),
            R("Project Cost Controller / Finance","HR Canada"),
            R("Contract Manager","HR Canada"),
            R("Procurement Project Manager","HR Canada"),
            R("Project Safety Manager","HR Canada"),
            R("PDA Systems Integration","HR Canada"),
            R("Project Design Authority (PDA)","HR Canada"),
            R("Safety Engineering","HR Canada"),
            R("Independent Validation","HR Canada"),
            R("Safety Assurance","HR Canada"),
        ],
    },
    {
        "id": "nyct", "name": "NYCT R211 ATO", "short": "NYCT R211",
        "priority": True,
        "region": "Americas – NA", "city": "New York, USA",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR USA (Local Delivery)",
        "source": "NYCT R211 Org Chart R16D00 260528.pdf", "date": "May 2026",
        "phase": "Execution",
        "rationale": "High-profile NYCT project (5G-first CBTC). Canada leads technology; US-based delivery team. Customer requirements are stringent (MTA). Complex integration environment. No dedicated Planner or RAMS visible at top-level OBS.",
        "wf_category": "action",
        "wf_action": "Formalize Project Manager accountability (currently split between Canada/USA). Add Project Planner as explicit role. Ensure RAMS coverage is documented. Project Financial Controller name change from current title.",
        "maturity": {"tech": 5, "tools": 5, "resources": 4, "customer": 5, "structure": 2},
        "roles": [
            R("Project Manager", "HR USA"),
            R("Project Director", "HR Canada"),
            R("Solutions Engineering Manager (SEM)","HR Canada"),
            R("Project Financial Controller","HR Canada"),
            R("Project Procurement Manager", "HR Canada"),
            R("Contract Manager",            "HR USA"),
            R("ITV Manager",                 "HR Canada"),
            R("Documentation Manager",       "HR USA"),
            R("Project Office",              "HR USA"),
            R("Safety Engineering",          "HR Canada"),
        ],
    },
    {
        "id": "sfmta", "name": "San Francisco TCUP (SFMTA)", "short": "SF TCUP",
        "priority": True,
        "region": "Americas – NA", "city": "San Francisco, USA",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR USA (Local Delivery)",
        "source": "SFMTA_TCUP_GTS_OBS_Rev14.pdf", "date": "Rev14",
        "phase": "Execution",
        "rationale": "GTS legacy project. Lean project team with strong deployment focus. Project Manager and Deployment PM split responsibilities. Safety Assurance present. Key gaps in financial control and RAMS visibility at top level.",
        "wf_category": "action",
        "wf_action": "Consolidate PM accountability. Add Project Controller and Planner as explicit roles. Document RAMS/Safety coverage in OBS. Map Deployment PM to Construction/Installation Manager role per G-TRN.",
        "maturity": {"tech": 4, "tools": 4, "resources": 4, "customer": 3, "structure": 2},
        "roles": [
            R("Project Manager","HR USA"),
            R("Deployment Project Manager","HR Canada"),
            R("Safety Assurance","HR Canada"),
            R("Independent Validation","HR Canada"),
            R("Site QA & CM","HR USA"),
            R("Warranty / Maintenance","HR Canada"),
        ],
    },
    {
        "id": "oewl", "name": "OEWL Project", "short": "OEWL",
        "region": "Americas – NA", "city": "Ottawa, Canada",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Lead)",
        "entity_onshore":  "HR Canada (Local)",
        "source": "OEWL OBS (April 2026).pdf", "date": "Apr 2026",
        "phase": "Execution",
        "rationale": "Canadian project led by HR Canada. Project Portfolio Director layer present. Strong project controls structure (Planner, Controller, PPM). Good alignment potential to G-TRN but naming misalignment (Portfolio Director vs PM, Financial Controller vs Project Controller).",
        "wf_category": "partial",
        "wf_action": "Rename Portfolio Director to align with PM accountability per G-TRN. Rename Financial Controller to Project Controller. PDA/SEM role covers PE function. Deployment PM maps to Construction/Installation Manager.",
        "maturity": {"tech": 4, "tools": 4, "resources": 4, "customer": 3, "structure": 3},
        "roles": [
            R("Project Portfolio Director","HR Canada"),
            R("Project Planner","HR Canada"),
            R("Project Financial Controller","HR Canada"),
            R("Contract Manager","HR Canada"),
            R("Project Procurement Manager (PPM)","HR Canada"),
            R("Quality Assurance Manager","HR Canada"),
            R("Project Design Authority (PDA)","HR Canada"),
            R("Solution Engineering Manager","HR Canada"),
            R("Deployment Project Manager","HR Canada"),
        ],
    },
    {
        "id": "blueline", "name": "Montreal Blue Line Extension", "short": "MTL Blue Line",
        "priority": True,
        "region": "Americas – NA", "city": "North America",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR Canada / Local",
        "source": "Org Chart Blue Line - 2026-04-14_V12.vsdx.pdf", "date": "Apr 2026",
        "phase": "Execution",
        "rationale": "Canada-led CBTC project. Engineering-heavy OBS with WPM-level breakdown. Portfolio Director at top. Strong engineering and software WPM structure. Missing contract management, supply chain and planner at top-level OBS.",
        "wf_category": "action",
        "wf_action": "Confirm single PM from Portfolio Director. Add explicit Contract Manager and Planner to top-level OBS. Ensure Supply Chain/Procurement and Quality roles are formally documented.",
        "maturity": {"tech": 4, "tools": 4, "resources": 4, "customer": 4, "structure": 2},
        "roles": [
            R("Projects Portfolio Director","HR Canada"),
            R("Planning Manager", "HR Canada"),
            R("Quality Manager",            "HR Canada"),
            R("System Engineering Manager", "HR Canada"),
            R("Project Design Authority (PDA)","HR Canada"),
            R("Solution Configuration Management","HR Canada"),
            R("ITV Lead",                   "HR Canada"),
        ],
    },
    # ── AMERICAS – NORTH AMERICA  (continued) ───────────────────────────
    {
        "id": "ttcl2", "name": "TTC Line 2 (Toronto)", "short": "TTC L2",
        "priority": True, "pending": True,
        "region": "Americas – NA", "city": "Toronto, Canada",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR Canada (Local Delivery)",
        "source": "OBS data pending", "date": "TBC",
        "phase": "Execution",
        "rationale": "Toronto TTC Line 2 CBTC project. OBS file not yet available in the input folder. Assessment pending OBS submission.",
        "wf_category": "action",
        "wf_action": "Request and submit current OBS. Perform full gap analysis against G-TRN A08001 once received.",
        "maturity": {"tech": 4, "tools": 4, "resources": 4, "customer": 4, "structure": 2},
        "roles": PENDING,
    },
    {
        "id": "vanbsp", "name": "Vancouver BSP", "short": "Van BSP",
        "priority": True, "pending": True,
        "region": "Americas – NA", "city": "Vancouver, Canada",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR Canada (Local Delivery)",
        "source": "OBS data pending", "date": "TBC",
        "phase": "Execution",
        "rationale": "Vancouver BSP CBTC project. OBS file not yet available in the input folder.",
        "wf_category": "action",
        "wf_action": "Request and submit current OBS. Perform full gap analysis against G-TRN A08001 once received.",
        "maturity": {"tech": 4, "tools": 4, "resources": 4, "customer": 4, "structure": 2},
        "roles": PENDING,
    },
    {
        "id": "vanomc", "name": "Vancouver OMC1 & OMC4", "short": "Van OMC",
        "priority": True, "pending": True,
        "region": "Americas – NA", "city": "Vancouver, Canada",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR Canada (Local Delivery)",
        "source": "OBS data pending", "date": "TBC",
        "phase": "Execution",
        "rationale": "Vancouver OMC1 & OMC4 CBTC project. OBS file not yet available.",
        "wf_category": "action",
        "wf_action": "Request and submit current OBS. Perform full gap analysis against G-TRN A08001 once received.",
        "maturity": {"tech": 4, "tools": 3, "resources": 4, "customer": 4, "structure": 2},
        "roles": PENDING,
    },
    {
        "id": "vansls", "name": "Vancouver SLS", "short": "Van SLS",
        "priority": True, "pending": True,
        "region": "Americas – NA", "city": "Vancouver, Canada",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR Canada (Local Delivery)",
        "source": "SLS_OBS_v.03_Core_Jan 2026.vsd (PDF export required)", "date": "Jan 2026",
        "phase": "Execution",
        "rationale": "Vancouver SLS project. VSD source file present in input folder but PDF extraction required for full analysis. Partial OBS data available.",
        "wf_category": "action",
        "wf_action": "Export SLS_OBS_v.03_Core_Jan 2026.vsd to PDF and re-run extraction. Perform full gap analysis.",
        "maturity": {"tech": 4, "tools": 3, "resources": 4, "customer": 4, "structure": 2},
        "roles": PENDING,
    },
    {
        "id": "stmsei", "name": "Montreal STM-SEI Interlocking", "short": "MTL STM-SEI",
        "priority": True,
        "region": "Americas – NA", "city": "Montreal, Canada",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR Canada (Local Delivery)",
        "source": "STM Org chart (Eng) - 2025-09-14.pptx", "date": "Sep 2025",
        "phase": "Execution",
        "rationale": "Montreal STM SEI Interlocking project. HR Canada–led structure. Engineering-heavy OBS with strong SEM and software delivery teams. Project Director (Portfolio Director) above PM. Good controls team (Planner, Controller, Contracts). RAMS and Safety present. Deployment PM explicit.",
        "wf_category": "partial",
        "wf_action": "Rename Portfolio Director (Julie Molinaro) to align to functional management, confirm PM (Thomas Delevacque) as single accountable leader. Rename Cost Controller to Project Controller. SEM/PDA covers PE function. Deployment PM maps to Construction/Installation Manager. Warranty role present.",
        "maturity": {"tech": 5, "tools": 4, "resources": 5, "customer": 4, "structure": 3},
        "roles": [
            R("Project Manager",                    "HR Canada"),
            R("Director, Project Portfolio",         "HR Canada"),
            R("Project Design Authority (PDA)",      "HR Canada"),
            R("Solution Engineering Manager (SEM)",  "HR Canada"),
            R("Project Planner",                     "HR Canada"),
            R("Project Cost Controller",              "HR Canada"),
            R("Project Contract Manager",             "HR Canada"),
            R("Project Coordinator",                  "HR Canada"),
            R("Quality Assurance",                    "HR Canada"),
            R("Configuration Management",             "HR Canada"),
            R("Deployment Project Manager",           "HR Canada"),
            R("Safety Assurance",                     "HR Canada"),
            R("Safety Engineering & RAM",             "HR Canada"),
            R("Independent Validator",                "HR Canada"),
            R("Procurement Manager",                  "HR Canada"),
            R("Site Quality / HSE",                   "HR Canada"),
            R("Warranty",                             "HR Canada"),
        ],
    },
    # ── APAC – SOUTH-EAST ASIA ──────────────────────────────────────────
    {
        "id": "r152b", "name": "R152B SA1 URS (Singapore)", "short": "R152B SG",
        "priority": True,
        "region": "APAC – SE Asia", "city": "Singapore",
        "lob": "SRS", "legacy": "Legacy GTS (Multi-entity)",
        "entity_offshore": "HR Canada + HR France (Technology)",
        "entity_onshore":  "HR Singapore (Lead Delivery)",
        "source": "R152B SA1 URS_Project OBSFinal (1).pdf", "date": "2025",
        "phase": "Execution",
        "rationale": "Three-entity CBTC project: Singapore leads delivery, Canada provides CBTC technology, France provides system integration. Three PMs across entities (legacy GTS model). Richest OBS in portfolio — all key roles present but distributed across entities.",
        "wf_category": "partial",
        "wf_action": "Designate single accountable PM (Singapore PM). Canada and France PMs transition to WPL/WPM roles. Rename Financial Controllers to Project Controller. Align PPM/PSCL to Supply Chain & Procurement Manager. APAC designated as pilot for PM maturity assessment.",
        "maturity": {"tech": 5, "tools": 4, "resources": 4, "customer": 5, "structure": 3},
        "roles": [
            # ── HR Singapore (Lead Delivery) ──
            R("Singapore Project Manager",              "HR Singapore"),
            R("Singapore Deputy Project Manager",       "HR Singapore"),
            R("PMO",                                    "HR Singapore"),
            R("Financial Controller",                   "HR Singapore"),
            R("Project Design Authority (PDA)",         "HR Singapore"),
            R("Interface Manager",                      "HR Singapore"),
            R("Configuration Manager",                  "HR Singapore"),
            R("Contract Manager",                       "HR Singapore"),
            R("Planner",                                "HR Singapore"),
            R("System Engineering Manager",             "HR Singapore"),
            R("Deployment Manager",                     "HR Singapore"),
            R("T&C Manager (Test & Commissioning)",     "HR Singapore"),
            R("Supply Chain Manager",                   "HR Singapore"),
            R("Project Procurement Manager",            "HR Singapore"),
            R("HSE Manager",                            "HR Singapore"),
            R("WSHO Officer",                           "HR Singapore"),
            R("Environmental Control Officer",          "HR Singapore"),
            R("Quality Assurance Manager",              "HR Singapore"),
            # ── HR France (System Integration) ──
            R("France Project Manager",                 "HR France"),
            R("Financial Controller",                   "HR France"),
            R("System Engineering & Software Manager",  "HR France"),
            R("PPM (Project Programme Manager)",        "HR France"),
            R("RAMS Manager",                           "HR France"),
            # ── HR Canada (CBTC Technology) ──
            R("Canada Project Manager",                 "HR Canada"),
            # ── Programme Level ──
            R("PPM/PSCL (Supply Chain Lead)",           "Programme"),
            R("System Assurance Manager",               "Programme"),
            R("Project Safety Manager",                 "Programme"),
            R("IVVQ Manager",                           "Programme"),
        ],
    },
    {
        "id": "singapore_eng", "name": "HR Canada – Singapore Engineering Hub", "short": "SG Eng Hub",
        "region": "APAC – SE Asia", "city": "Singapore",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Owner)",
        "entity_onshore":  "HR Singapore (Engineering Execution)",
        "source": "OrgChart _Singapore-Rev15_OBS_20260320- Copy.pdf", "date": "Mar 2026",
        "phase": "Execution",
        "rationale": "Engineering support structure for Singapore CBTC projects, managed from Canada. Focused on system engineering, RAM, safety and T&C. No formal PM/Controller/Planner visible – this is a functional/WP-level view, not a full PTO.",
        "wf_category": "action",
        "wf_action": "This is an engineering work-package structure, not a full PTO. Integrate into the R152B or parent project OBS as WPM/WPL layers. Define PM accountability at top level. Formalize PTO per G-TRN with PM as single accountable leader.",
        "maturity": {"tech": 5, "tools": 4, "resources": 5, "customer": 5, "structure": 2},
        "roles": [
            R("T&C Manager (SAT)",      "HR Singapore"),
            R("Quality Assurance",      "HR Singapore"),
            R("Configuration Manager",  "HR Singapore"),
            R("RAM Engineering",        "HR Canada"),
            R("System Engineering",     "HR Canada"),
            R("Software Engineering",   "HR Canada"),
            R("Hardware Engineering",   "HR Canada"),
            R("Safety Authority",       "HR Canada"),
            R("Cyber Security Advisor", "HR Canada"),
        ],
    },
    {
        "id": "klmidlife", "name": "KL Midlife Upgrade (URS)", "short": "KL Midlife",
        "region": "APAC – SE Asia", "city": "Kuala Lumpur, Malaysia",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (CBTC Technology)",
        "entity_onshore":  "HR Singapore (Delivery)",
        "source": "KLMIDLIFE_URS_OBS_Rev02d3.pdf", "date": "Rev2",
        "phase": "Execution",
        "rationale": "Malaysia midlife upgrade project. Canada/Singapore dual-entity model. Strong technical roles (PDA, SEM, Safety). Deployment PM present. Gap in financial control visibility and formal Contract Manager.",
        "wf_category": "partial",
        "wf_action": "Confirm single PM from General PM role. Add Project Controller and Contract Manager to top-level OBS. Deployment PM maps to Construction/Installation Manager. Warranty role present (DLP).",
        "maturity": {"tech": 4, "tools": 3, "resources": 3, "customer": 4, "structure": 3},
        "roles": [
            R("General Project Manager",           "HR Canada"),
            R("Project Design Authority (PDA)",    "HR Canada"),
            R("Solution Engineering Manager (SEM)","HR Canada"),
            R("Global Quality Assurance Manager",  "HR Canada"),
            R("Safety Assurance",                  "HR Canada"),
            R("Deployment Project Manager",        "HR Singapore"),
            R("SID Lead",                          "HR Singapore"),
            R("Operations & Maintenance Training", "HR Singapore"),
            R("Warranty / DLP",                    "HR Singapore"),
        ],
    },
    {
        "id": "hktme", "name": "HK DUAT — Hong Kong Driverless Urban Autonomous Transit (C1552)", "short": "HK DUAT",
        "priority": True,
        "region": "APAC – SE Asia", "city": "Hong Kong",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology)",
        "entity_onshore":  "HR Hong Kong (Delivery)",
        "source": "C1552-HKTME-Project-OBS-Consolidated_2026-01-19.pdf", "date": "Jan 2026",
        "phase": "Execution",
        "rationale": "Hong Kong DUAT (Driverless Urban Autonomous Transit) project — contract C1552. 5G-enabled CBTC for Hong Kong metro. Multi-entity structure (Hitachi Rail Canada + HK local). Strong deployment and test teams. Project Planner and T&C Manager present. HSE Manager present. Financial controller/planner roles less visible at top level.",
        "wf_category": "partial",
        "wf_action": "Confirm single PM accountability. Add explicit Project Controller. PDA/System Design Lead covers PE function. T&C Manager aligned to Commissioning Manager. Procurement Manager maps to Supply Chain & Procurement Manager.",
        "maturity": {"tech": 5, "tools": 4, "resources": 3, "customer": 4, "structure": 3},
        "roles": [
            R("Project Planner",        "HR Hong Kong"),
            R("System Design Lead",     "HR Canada"),
            R("T&C Manager",            "HR Hong Kong"),
            R("HSE Manager",            "HR Hong Kong"),
            R("Procurement Manager",    "HR Hong Kong"),
            R("DCS Lead",               "HR Canada"),
            R("ITV Lead",               "HR Canada"),
            R("PMO Engineer",           "HR Hong Kong"),
            R("Quality Assurance",      "HR Hong Kong"),
            R("Configuration Manager",  "HR Canada"),
        ],
    },
    # ── APAC – SOUTH-EAST ASIA  (continued) ─────────────────────────────
    {
        "id": "sgbricklands", "name": "Singapore Bricklands", "short": "SG Bricklands",
        "priority": True, "pending": True,
        "region": "APAC – SE Asia", "city": "Singapore",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR Singapore (Local Delivery)",
        "source": "OBS data pending", "date": "TBC",
        "phase": "Execution",
        "rationale": "Singapore Bricklands CBTC project. OBS file not yet available in input folder.",
        "wf_category": "action",
        "wf_action": "Request and submit current OBS. Perform full gap analysis against G-TRN A08001 once received.",
        "maturity": {"tech": 4, "tools": 3, "resources": 4, "customer": 5, "structure": 2},
        "roles": PENDING,
    },
    {
        "id": "sgcal2tel", "name": "Singapore CAL2tEL", "short": "SG CAL2tEL",
        "priority": True, "pending": True,
        "region": "APAC – SE Asia", "city": "Singapore",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR Singapore (Local Delivery)",
        "source": "OBS data pending", "date": "TBC",
        "phase": "Execution",
        "rationale": "Singapore CAL2tEL CBTC project. OBS file not yet available in input folder.",
        "wf_category": "action",
        "wf_action": "Request and submit current OBS. Perform full gap analysis against G-TRN A08001 once received.",
        "maturity": {"tech": 4, "tools": 3, "resources": 4, "customer": 5, "structure": 2},
        "roles": PENDING,
    },
    {
        "id": "kjnet", "name": "KJNET", "short": "KJNET",
        "priority": True, "pending": True,
        "region": "APAC – SE Asia", "city": "TBC",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "Local Entity (TBC)",
        "source": "OBS data pending", "date": "TBC",
        "phase": "Execution",
        "rationale": "KJNET project. OBS file not yet available in input folder. Region and entity structure TBC.",
        "wf_category": "action",
        "wf_action": "Confirm project region and entity structure. Request and submit OBS. Perform gap analysis.",
        "maturity": {"tech": 3, "tools": 3, "resources": 3, "customer": 3, "structure": 2},
        "roles": PENDING,
    },
    # ── APAC – OTHER ────────────────────────────────────────────────────
    {
        "id": "hyderabad", "name": "Hyderabad Metro", "short": "Hyderabad",
        "region": "APAC – Other", "city": "Hyderabad, India",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR India (Local Delivery)",
        "source": "Hyderabad OBS February 2026 R2.pdf", "date": "Feb 2026",
        "phase": "Execution",
        "rationale": "India metro project. Canada-led technology with local India delivery. Project Director layer above PM. PDA and SEM present. Project Safety Manager present. Supervisory Committee (VP/CFO) indicates high governance oversight. Portfolio Director present.",
        "wf_category": "partial",
        "wf_action": "Remove Project Director layer; confirm single PM per G-TRN. Add Project Controller (currently implied in Portfolio Director role). Planner present. Procurement Manager present. SEM covers PE function.",
        "maturity": {"tech": 3, "tools": 2, "resources": 3, "customer": 3, "structure": 3},
        "roles": [
            R("Project Manager",                "HR India"),
            R("Portfolio Director",             "HR Canada"),
            R("Project Design Authority (PDA)", "HR Canada"),
            R("PDA Systems Integration",        "HR Canada"),
            R("Project Safety Manager",         "HR Canada"),
            R("Solutions Engineering Manager",  "HR Canada"),
            R("Quality Assurance",              "HR India"),
            R("Planner",                        "HR India"),
            R("Project Procurement Manager",    "HR India"),
            R("Systems Design",                 "HR Canada"),
        ],
    },
    {
        "id": "taiwan", "name": "Taiwan Xidong", "short": "Taiwan Xidong",
        "priority": True,
        "region": "APAC – Other", "city": "Taiwan",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR Taiwan (Local Delivery)",
        "source": "Taiwan-Xidong OBS-Rev27.pdf", "date": "Rev27",
        "phase": "Execution",
        "rationale": "Taiwan CBTC project (Rev27 indicates mature project in execution). Project Portfolio Director at top. Strong project controls presence (Planner, Cost Control, Procurement). PDA and Safety Manager present.",
        "wf_category": "partial",
        "wf_action": "Map Portfolio Director to PM accountability. Rename Project Cost Control to Project Controller. PDA covers PE function. Safety Manager maps to RAMS per G-TRN scope alignment. Contract Manager and Procurement Manager present.",
        "maturity": {"tech": 4, "tools": 3, "resources": 4, "customer": 4, "structure": 4},
        "roles": [
            R("Project Portfolio Director",   "HR Canada"),
            R("Project Planner",              "HR Taiwan"),
            R("Project Cost Control",         "HR Canada"),
            R("Contract Manager",             "HR Taiwan"),
            R("Procurement Manager",          "HR Canada"),
            R("Quality Assurance Specialist", "HR Taiwan"),
            R("Safety Assurance",             "HR Canada"),
            R("Project Safety Manager",       "HR Canada"),
            R("Project Design Authority",     "HR Canada"),
            R("IVAL (Independent Validation)","HR Canada"),
        ],
    },
    # ── MIDDLE EAST & AFRICA ────────────────────────────────────────────
    {
        "id": "abouqir", "name": "Abou Qir URS (Egypt)", "short": "Abou Qir",
        "priority": True,
        "region": "MEA", "city": "Cairo, Egypt",
        "lob": "SRS", "legacy": "Legacy GTS (URS)",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "URS Cairo Office (Local Delivery)",
        "source": "Abou Qir URS OBS Dec 2025.pdf", "date": "Dec 2025",
        "phase": "Execution",
        "rationale": "Egypt CBTC project under URS legacy brand. Project Director layer. Canada leads technology (SEM, PDA, RAM Manager, Safety Authority). Cairo office manages local delivery. Project Coordinator is a non-standard role bridging entities.",
        "wf_category": "action",
        "wf_action": "Formalize Project Manager as single accountable lead per G-TRN (remove or redefine Project Director). Add Project Controller. Project Coordinator role to be mapped to WPL. RAM Manager maps to Project RAMS Manager. Safety Authority is independent – not in PM PTO scope.",
        "maturity": {"tech": 3, "tools": 2, "resources": 2, "customer": 3, "structure": 2},
        "roles": [
            R("Project Director",              "HR Canada"),
            R("Project Manager",               "URS Cairo"),
            R("Solution Engineering Manager",  "HR Canada"),
            R("Project Coordinator",           "HR Canada"),
            R("Project Procurement Manager",   "HR Canada"),
            R("Contract Manager",              "URS Cairo"),
            R("Quality Assurance",             "URS Cairo"),
            R("Safety Engineering",            "HR Canada"),
            R("RAM Manager",                   "HR Canada"),
            R("Project Design Authority",      "HR Canada"),
            R("Safety Authority",              "HR Canada"),
        ],
    },
    {
        "id": "cml1", "name": "Cairo Metro Line 1 (CBTC)", "short": "CML1 Cairo",
        "priority": True,
        "region": "MEA", "city": "Cairo, Egypt",
        "lob": "SRS", "legacy": "Legacy GTS (URS)",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "URS Cairo Office (Local Delivery)",
        "source": "CML1 CBTC OBS Mar 2026.pdf", "date": "Mar 2026",
        "phase": "Execution",
        "rationale": "Cairo Metro L1 – same structure as Abou Qir (sister project, same Project Director). URS Cairo model with Canada technology delivery. Project Director layer not aligned with G-TRN single PM principle.",
        "wf_category": "action",
        "wf_action": "Same transition actions as Abou Qir. Shared Project Director across two Egypt projects should be transitioned to a Portfolio Director role (functional), with each project having its own single PM per G-TRN.",
        "maturity": {"tech": 3, "tools": 2, "resources": 2, "customer": 3, "structure": 2},
        "roles": [
            R("Project Director",              "HR Canada"),
            R("Project Manager",               "URS Cairo"),
            R("Solution Engineering Manager",  "HR Canada"),
            R("Project Coordinator",           "HR Canada"),
            R("Project Procurement Manager",   "HR Canada"),
            R("Contract Manager",              "URS Cairo"),
            R("Quality Assurance",             "URS Cairo"),
            R("Safety Engineering",            "HR Canada"),
            R("RAM Manager",                   "HR Canada"),
            R("Project Design Authority",      "HR Canada"),
        ],
    },
    {
        "id": "duat", "name": "DUAT (Dubai Automated Transit)", "short": "DUAT Dubai",
        "region": "MEA", "city": "Dubai, UAE",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR Canada (Delivery)",
        "source": "DUAT Option C - CA Org Chart _07 May_ 2026.pdf", "date": "May 2026",
        "phase": "Execution",
        "rationale": "Dubai automated transit CBTC project. Canada-only structure. Lean team. Financial Controller and Planner present. Significant gaps in Quality, HSE, RAMS, Commissioning, and Contract Management visibility at top level.",
        "wf_category": "action",
        "wf_action": "Add Project Quality Manager, HSE, Contract Manager, and RAMS roles to OBS. Confirm Deployment Manager covers Construction/Installation role. Expand team structure to reflect full G-TRN core team.",
        "maturity": {"tech": 4, "tools": 3, "resources": 4, "customer": 3, "structure": 2},
        "roles": [
            R("Project Director (PM)",              "HR Canada"),
            R("Project Financial Controller",        "HR Canada"),
            R("Configuration Manager",               "HR Canada"),
            R("Training & Manuals Manager",          "HR Canada"),
            R("Project Office Manager / Project Planner","HR Canada"),
            R("Project Admin Assistant",             "HR Canada"),
            R("Associate PM / Data Manager",         "HR Canada"),
        ],
    },
    {
        "id": "mmmp", "name": "MMMP Ph2 Revamp (Saudi Arabia)", "short": "MMMP Saudi",
        "region": "MEA", "city": "Saudi Arabia",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "Saudi Arabia Railways (Local Delivery)",
        "source": "MMMP Ph2 Revamp_HRC_OBS_May_2026_consolidated-Draft.pdf", "date": "May 2026",
        "phase": "Execution (Draft)",
        "rationale": "Saudi Arabia railway project (Draft OBS). Joint delivery with Saudi Arabia Railways. Program Manager layer present. Site QA and Contract Manager present. HSE present as Site Safety Officer. Missing RAMS and Supply Chain/Procurement at top level.",
        "wf_category": "action",
        "wf_action": "Finalize OBS structure from Draft status. Confirm PM as single accountable leader. Add Project Controller (no finance/control visible). Add RAMS / Safety role. Align Program Manager to WPM structure per G-TRN.",
        "maturity": {"tech": 3, "tools": 2, "resources": 3, "customer": 3, "structure": 2},
        "roles": [
            R("Project Manager",               "Saudi Arabia Railways"),
            R("Program Manager",               "HR Canada"),
            R("Contract Manager",              "HR Canada"),
            R("Site QA Manager",               "HR Canada"),
            R("Project Planner",               "HR Canada"),
            R("Site Safety Officer",           "HR Canada"),
            R("Customer Service Manager (DLP)","HR Canada"),
            R("Training Manager",              "HR Canada"),
            R("System Design",                 "HR Canada"),
        ],
    },
    {
        "id": "istanbul", "name": "Istanbul CBTC (Turkey IKP)", "short": "Istanbul IKP",
        "priority": True,
        "region": "MEA", "city": "Istanbul, Turkey",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR Turkey (Local Delivery)",
        "source": "OBS Turkey-Istanbul KP March 2026 (006).pdf", "date": "Mar 2026",
        "phase": "Execution",
        "rationale": "Turkey CBTC project. Canada leads technology with Turkey local team. Project Manager and strong project controls present. PDA and Systems Design cover PE function. Project Safety present. Good alignment base.",
        "wf_category": "partial",
        "wf_action": "Rename Financial Controller to Project Controller. PDA/Systems Design maps to PE. Add explicit RAMS/Safety as separate role from Project Safety. Ensure Supply Chain and Commissioning roles are documented.",
        "maturity": {"tech": 3, "tools": 3, "resources": 3, "customer": 3, "structure": 3},
        "roles": [
            R("Project Manager",               "HR Canada"),
            R("Project Financial Controller",  "HR Canada"),
            R("Project Design Authority",      "HR Canada"),
            R("Contract Manager",              "HR Turkey"),
            R("Quality Assurance Manager",     "HR Canada"),
            R("Configuration Manager",         "HR Canada"),
            R("Systems Design",                "HR Canada"),
            R("Project Safety Manager",        "HR Canada"),
            R("Safety Assurance",              "HR Canada"),
        ],
    },
    # ── SE & LATAM ───────────────────────────────────────────────────────
    {
        "id": "santiago", "name": "Santiago Line 6 Extension", "short": "Santiago L6",
        "priority": True,
        "region": "SE & LATAM", "city": "Santiago, Chile",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "HR Canada (Technology Lead)",
        "entity_onshore":  "HR Local / Chile (Delivery)",
        "source": "Org Chart _Santiago- March 2026.pptx", "date": "Mar 2026",
        "phase": "Execution",
        "rationale": "Santiago Chile Line 6 Extension CBTC project. Canada leads technology. Project Director layer present above PM. Associate PM role visible. Strong controls (Financial Controller, Contract Manager). RAM and Safety well-represented. Planner and QA present. Good baseline for G-TRN transition.",
        "wf_category": "partial",
        "wf_action": "Remove Project Director from PTO (move to functional management). Confirm Associate PM as single PM (Gunay Gencer) per G-TRN. Rename Financial Controller to Project Controller. PDA covers PE function. Add Supply Chain & Procurement role. RAMS Manager present (RAM Manager = Project RAMS Manager).",
        "maturity": {"tech": 3, "tools": 3, "resources": 3, "customer": 3, "structure": 3},
        "roles": [
            R("Project Director",            "HR Canada"),
            R("Project Portfolio Director",   "HR Canada"),
            R("Associate Project Manager",    "HR Canada"),
            R("Project Financial Controller", "HR Canada"),
            R("Contract Manager",             "HR Canada"),
            R("Project Design Authority",     "HR Canada"),
            R("Quality Assurance Manager",    "HR Canada"),
            R("Safety Assurance Manager",     "HR Canada"),
            R("RAM Manager",                  "HR Canada"),
            R("Safety Engineering Manager",   "HR Canada"),
            R("Project Safety",               "HR Canada"),
            R("Planner",                      "HR Canada"),
            R("Project Coordinator",          "HR Canada"),
        ],
    },
    # ── EUROPE ──────────────────────────────────────────────────────────
    {
        "id": "dlr", "name": "DLR – RSRP/SU/AZLM", "short": "DLR UK",
        "priority": True,
        "region": "Europe – UK", "city": "London, UK",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "N/A (UK-only delivery)",
        "entity_onshore":  "HR UK (Lead)",
        "source": "20260521 DLR org.pdf", "date": "May 2026",
        "phase": "Execution",
        "rationale": "UK CBTC multi-package programme (DLR). Single-entity UK delivery. Senior Project Manager model (legacy GTS title, not G-TRN PM). Delivery Manager role straddles PM/PE boundary. Strong controls (Controller, Finance, Quality). No dedicated RAMS or Deployment roles visible.",
        "wf_category": "partial",
        "wf_action": "Rename Senior Project Manager to Project Manager per G-TRN. Clarify Delivery Manager – either consolidate into PE (if technical lead) or map to Construction/Installation Manager. Add RAMS coverage. TIC/T&C Manager = Commissioning Manager.",
        "maturity": {"tech": 4, "tools": 4, "resources": 4, "customer": 3, "structure": 2},
        "roles": [
            R("Senior Project Manager",     "HR UK"),
            R("Delivery Manager",           "HR UK"),
            R("Project Controller",         "HR UK"),
            R("Finance",                    "HR UK"),
            R("Commercial / Contracts",     "HR UK"),
            R("Quality Assurance",          "HR UK"),
            R("TIC / T&C Manager",          "HR UK"),
        ],
    },
    {
        "id": "gscs4", "name": "4GSCS UK (4G Signalling Communication System)", "short": "4GSCS UK",
        "priority": True,
        "region": "Europe – UK", "city": "London, UK",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "N/A (UK-only delivery)",
        "entity_onshore":  "HR UK (Lead)",
        "source": "4GSCS GTS OBS_Rev 9_20260505.pdf", "date": "May 2026",
        "phase": "Execution",
        "rationale": "UK 4G signalling project. Same programme structure as DLR (same PM, same team). Legacy GTS Senior PM model. Good controls structure but title alignment needed per G-TRN.",
        "wf_category": "partial",
        "wf_action": "Same transition actions as DLR (shared programme team). Align to G-TRN as part of DLR programme transition. Single PM with Delivery Manager restructured.",
        "maturity": {"tech": 4, "tools": 4, "resources": 4, "customer": 3, "structure": 2},
        "roles": [
            R("Senior Project Manager",  "HR UK"),
            R("Delivery Manager",        "HR UK"),
            R("Project Controller",      "HR UK"),
            R("Finance",                 "HR UK"),
            R("Commercial / Contracts",  "HR UK"),
            R("Quality Assurance",       "HR UK"),
            R("TIC / T&C Manager",       "HR UK"),
        ],
    },
    {
        "id": "4lm", "name": "4LM (Four Lines Modernisation – London)", "short": "4LM UK",
        "priority": True,
        "region": "Europe – UK", "city": "London, UK",
        "lob": "SRS", "legacy": "Legacy GTS",
        "entity_offshore": "N/A (UK-only delivery)",
        "entity_onshore":  "HR UK (Lead)",
        "source": "PPTX Transition Plan Slide 54-55 (VSD not yet available as PDF)", "date": "2026",
        "phase": "Execution",
        "rationale": "London Underground Four Lines Modernisation (4LM) – UK CBTC project. Part of UK programme alongside DLR/4GSCS. Referenced in PPTX transition plan. VSD OBS available but not yet exported to PDF. Structure expected to match UK programme model.",
        "wf_category": "partial",
        "wf_action": "Export Hitachi - 5G_OBS VSD to PDF and extract full OBS. Align to G-TRN as part of UK programme transition (same actions as DLR/4GSCS). Confirm single PM structure.",
        "maturity": {"tech": 4, "tools": 4, "resources": 4, "customer": 5, "structure": 2},
        "roles": [
            R("Senior Project Manager",  "HR UK"),
            R("Delivery Manager",        "HR UK"),
            R("Project Controller",      "HR UK"),
            R("Finance",                 "HR UK"),
            R("Commercial / Contracts",  "HR UK"),
            R("Quality Assurance",       "HR UK"),
            R("TIC / T&C Manager",       "HR UK"),
        ],
    },
]

# ═══════════════════════════════════════════════════════════════════════════
# 3. DATA BUILDER
# ═══════════════════════════════════════════════════════════════════════════
MANDATORY_N = sum(1 for s in STANDARD_ROLES if s["mandatory"])
TOTAL_N     = len(STANDARD_ROLES)
REGIONS     = ["Americas – NA", "APAC – SE Asia", "APAC – Other", "MEA", "SE & LATAM", "Europe – UK"]
REGION_ICONS = {
    "Americas – NA":  "🌎",
    "APAC – SE Asia": "🌏",
    "APAC – Other":   "🌏",
    "MEA":            "🌍",
    "SE & LATAM":     "🌎",
    "Europe – UK":    "🌍",
}

def build_project_results():
    results = []
    for proj in PROJECTS:
        is_pending = proj.get("pending", False)
        if is_pending:
            # pending projects: show as all-missing but flag them specially
            mat  = proj["maturity"]
            mat_avg = round(sum(mat.values()) / len(mat), 1)
            role_results = [{"std": std, "status": S_MISSING,
                             "title": "", "entity": "", "score": 0}
                            for std in STANDARD_ROLES]
            results.append({**proj,
                            "role_results": role_results,
                            "matched": 0, "partial": 0, "missing": TOTAL_N,
                            "pct_mand": 0, "pct_total": 0,
                            "risk": "PENDING", "mat_avg": mat_avg, "extras": [],
                            "multi_pm": []})
            continue
        role_results = []
        matched_titles = set()
        for std in STANDARD_ROLES:
            status, title, entity, score = match_role(std["role"], proj["roles"])
            # Carry through the name field from the matching obs_role
            name = next((o["name"] for o in proj["roles"]
                         if o["title"] == title and o["entity"] == entity), "")
            role_results.append({"std": std, "status": status,
                                  "title": title, "entity": entity,
                                  "score": score, "name": name})
            if title: matched_titles.add(title.lower())
        m  = sum(1 for r in role_results if r["status"] == S_MATCH)
        p  = sum(1 for r in role_results if r["status"] == S_PARTIAL)
        ms = sum(1 for r in role_results if r["status"] == S_MISSING)
        mand_hit = sum(1 for r in role_results
                       if r["std"]["mandatory"] and r["status"] in (S_MATCH, S_PARTIAL))
        pct_mand  = round(mand_hit / MANDATORY_N * 100)
        pct_total = round((m + p) / TOTAL_N * 100)
        risk = "LOW" if pct_mand >= 85 else "MEDIUM" if pct_mand >= 60 else "HIGH"
        mat  = proj["maturity"]
        mat_avg = round(sum(mat.values()) / len(mat), 1)
        extras = [r for r in proj["roles"]
                  if r["title"].lower() not in matched_titles]
        results.append({**proj,
                        "role_results": role_results,
                        "matched": m, "partial": p, "missing": ms,
                        "pct_mand": pct_mand, "pct_total": pct_total,
                        "risk": risk, "mat_avg": mat_avg, "extras": extras,
                        "multi_pm": find_all_pm_roles(proj["roles"])})
    return results

# ═══════════════════════════════════════════════════════════════════════════
# 4. HTML HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def donut_svg(m, p, ms, size=82):
    total = m + p + ms or 1
    cx = cy = size / 2
    r  = size / 2 - 7
    c  = 2 * 3.14159 * r
    def seg(val, off, col):
        d = c * val / total
        return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" '
                f'stroke-width="9" stroke-dasharray="{d:.1f} {c-d:.1f}" '
                f'stroke-dashoffset="{-off:.1f}" />')
    o0 = c * 0.25
    s1 = seg(m,  o0,             "#22c55e")
    s2 = seg(p,  o0 + c*m/total, "#f59e0b")
    s3 = seg(ms, o0 + c*(m+p)/total, "#ef4444")
    pct = round((m + p) / total * 100)
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#e5e7eb" stroke-width="9"/>'
            f'{s1}{s2}{s3}'
            f'<text x="{cx}" y="{cy+5}" text-anchor="middle" '
            f'font-size="15" font-weight="700" fill="#0f2d5a">{pct}%</text></svg>')

def bar_h(pct, color="#22c55e", height=14):
    c2 = "#ef4444" if pct < 60 else "#f59e0b" if pct < 85 else color
    return (f'<div style="background:#f1f5f9;border-radius:4px;height:{height}px;overflow:hidden;margin:2px 0">'
            f'<div style="width:{pct}%;background:{c2};height:100%;border-radius:4px;'
            f'display:flex;align-items:center;padding:0 5px">'
            f'<span style="font-size:10px;font-weight:700;color:#fff">{pct}%</span></div></div>')

def maturity_bar(val, max_val=5):
    pct = round(val / max_val * 100)
    colors = {1:"#ef4444",2:"#f97316",3:"#f59e0b",4:"#84cc16",5:"#22c55e"}
    c = colors.get(int(val), "#94a3b8")
    return (f'<div style="display:flex;align-items:center;gap:6px;font-size:.72rem">'
            + "".join(f'<div style="width:14px;height:14px;border-radius:3px;background:{"' + c + '" if i<=val else "#e5e7eb"}"></div>' for i in range(1,6))
            + f'<span style="color:#475569">{val}/5</span></div>')

def risk_badge(risk):
    cls = {"LOW":"#15803d;#dcfce7","MEDIUM":"#92400e;#fef9c3","HIGH":"#b91c1c;#fee2e2","PENDING":"#1d4ed8;#dbeafe"}[risk]
    fg, bg = cls.split(";")
    label = "⏳ DATA PENDING" if risk == "PENDING" else risk
    return f'<span style="background:{bg};color:{fg};border-radius:10px;padding:.2rem .7rem;font-size:.75rem;font-weight:700">{label}</span>'

PRIORITY_STAR = '<span style="color:#f59e0b;font-size:1rem;margin-right:3px" title="PMO Priority Project">★</span>'

def wf_badge(cat):
    m = {"aligned":"#15803d;#dcfce7;✔ Aligned",
         "partial":"#854d0e;#fef9c3;~ Partial Transition",
         "action":"#b91c1c;#fee2e2;⚠ Action Required",
         "exception":"#1d4ed8;#dbeafe;📋 Exception"}[cat]
    fg, bg, label = m.split(";")
    return f'<span style="background:{bg};color:{fg};border-radius:10px;padding:.2rem .7rem;font-size:.75rem;font-weight:700">{label}</span>'

def status_cell(status, title, entity, name=""):
    cfg = {
        S_MATCH:   ("✔","Matched","#22c55e","#f0fdf4"),
        S_PARTIAL: ("~","Partial","#f59e0b","#fffbeb"),
        S_MISSING: ("✘","MISSING","#ef4444","#fff1f2"),
    }
    icon, label, color, bg = cfg.get(status, ("?","?","#94a3b8","#f1f5f9"))
    tip = f"{title} ({entity})"
    if name: tip += f" — {name}"
    content = f'<div style="font-size:.72rem;color:#374151;margin-top:2px;line-height:1.3">{title}</div>' if title else ""
    name_tag = f'<div style="font-size:.67rem;color:#0f2d5a;font-style:italic">{name}</div>' if name else ""
    entity_tag = f'<span style="font-size:.68rem;color:#6b7280">{entity}</span>' if entity else ""
    return (f'<td style="padding:5px 7px;vertical-align:top" title="{tip}">'
            f'<div style="background:{bg};border-radius:6px;padding:4px 7px">'
            f'<span style="font-size:.72rem;font-weight:700;color:{color}">'
            f'{icon} {label}</span>{content}{name_tag}{entity_tag}</div></td>')

def multi_pm_cell(pm_list):
    """Special matrix cell for projects with multiple PM/Director roles."""
    tip = "⚠ Multi-PM: " + " / ".join(f'{o["title"]} ({o["entity"]})' for o in pm_list)
    rows = "".join(
        f'<div style="font-size:.68rem;color:#92400e;line-height:1.4">'
        f'{o["title"]} <span style="color:#b45309;font-size:.65rem">({o["entity"]})</span></div>'
        for o in pm_list
    )
    return (f'<td style="padding:5px 7px;vertical-align:top" title="{tip}">'
            f'<div style="background:#fff3cd;border:1px solid #fde68a;border-radius:6px;padding:4px 7px">'
            f'<span style="font-size:.72rem;font-weight:700;color:#92400e">⚠ Multi-PM</span>'
            f'{rows}</div></td>')

# ═══════════════════════════════════════════════════════════════════════════
# 5. HTML SECTIONS
# ═══════════════════════════════════════════════════════════════════════════
CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Segoe UI",system-ui,sans-serif;background:#f1f5f9;color:#1e293b;font-size:14px;line-height:1.55}
a{color:#2563eb;text-decoration:none}
/* header */
.hero{background:linear-gradient(135deg,#0a1f3c 0%,#0f2d5a 55%,#1a4a8a 100%);
  color:#fff;padding:2.8rem 3rem 2rem;box-shadow:0 4px 24px rgba(0,0,0,.4)}
.hero h1{font-size:1.9rem;font-weight:800;letter-spacing:-.02em}
.hero p{opacity:.8;margin-top:.4rem;font-size:.95rem}
.hero-meta{display:flex;flex-wrap:wrap;gap:.75rem;margin-top:1.2rem}
.pill{background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.22);
  border-radius:20px;padding:.25rem .95rem;font-size:.78rem;font-weight:600}
/* nav */
.nav{background:#fff;border-bottom:2px solid #e2e8f0;display:flex;gap:0;
  padding:0 2.5rem;position:sticky;top:0;z-index:200;
  box-shadow:0 2px 8px rgba(0,0,0,.06);overflow-x:auto;white-space:nowrap}
.nav a{padding:.7rem 1.1rem;font-size:.82rem;font-weight:600;color:#475569;
  border-bottom:3px solid transparent;transition:all .18s;display:inline-block}
.nav a:hover,.nav a.active{color:#0f2d5a;border-bottom-color:#0f2d5a}
/* main */
.main{max-width:1540px;margin:0 auto;padding:2rem 2rem 5rem}
section{margin-bottom:3.5rem}
.sec-title{font-size:1.15rem;font-weight:800;color:#0a1f3c;
  margin-bottom:1.4rem;padding-bottom:.5rem;
  border-bottom:2px solid #e2e8f0;display:flex;align-items:center;gap:.6rem}
.sec-title::before{content:"";display:block;width:4px;height:1.2em;
  background:linear-gradient(180deg,#0f2d5a,#2563eb);border-radius:2px}
/* cards */
.card{background:#fff;border-radius:14px;padding:1.5rem;
  box-shadow:0 2px 14px rgba(0,0,0,.07);border:1px solid #e2e8f0}
.grid-4{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.25rem}
.grid-5{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1rem}
/* scorecard */
.sc-head{margin-bottom:.9rem}
.sc-name{font-size:1rem;font-weight:700;color:#0a1f3c}
.sc-city{font-size:.76rem;color:#64748b;margin:.15rem 0 .5rem}
.sc-tags{display:flex;flex-wrap:wrap;gap:.3rem;margin-bottom:.7rem}
.tag{border-radius:8px;padding:.1rem .55rem;font-size:.7rem;font-weight:600}
.tag-region{background:#eff6ff;color:#1d4ed8}
.tag-lob{background:#f0fdf4;color:#15803d}
.tag-leg{background:#fef3c7;color:#92400e}
.sc-body{display:flex;align-items:center;gap:1rem;margin-bottom:.9rem}
.sc-stats{display:flex;flex-direction:column;gap:.35rem;font-size:.82rem}
.stat{display:flex;align-items:center;gap:.5rem}
.dot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
.sc-bars{margin-bottom:.9rem}
.bar-lbl{font-size:.72rem;color:#64748b;margin-bottom:.25rem}
.sc-foot{border-top:1px solid #f1f5f9;padding-top:.7rem;
  display:flex;justify-content:space-between;align-items:center;font-size:.78rem;color:#64748b}
/* matrix table */
.tbl-wrap{overflow-x:auto;border-radius:12px;box-shadow:0 2px 18px rgba(0,0,0,.09);
  border:1px solid #e2e8f0;max-height:80vh;overflow-y:auto}
table.matrix{width:100%;border-collapse:collapse;background:#fff;font-size:.78rem}
.matrix thead th{background:#0a1f3c;color:#fff;font-weight:600;padding:.7rem .6rem;
  text-align:center;white-space:nowrap;position:sticky;top:0;z-index:10}
.matrix thead th.th-role{text-align:left;min-width:190px;padding-left:.9rem}
.matrix thead th.th-proj{min-width:95px;font-size:.71rem;background:#0f2d5a}
.matrix .sec-row td{background:#1a4a8a;color:#fff;font-weight:700;
  padding:.45rem .9rem;font-size:.75rem;letter-spacing:.04em}
.matrix tr.role-row{border-bottom:1px solid #f1f5f9}
.matrix tr.role-row:hover{background:#f8faff!important}
.matrix tr.mand{background:#fffdf0}
.matrix tr.hidden{display:none}
.matrix td{padding:.5rem .5rem;vertical-align:middle}
.matrix td.td-abbr{color:#64748b;font-weight:600;font-size:.72rem;padding:.5rem .4rem .5rem .7rem}
.matrix td.td-role{font-weight:500;padding:.5rem .6rem}
.matrix td.td-lob{text-align:center}
.matrix td.td-mand{text-align:center;font-size:.75rem}
.lob-tag{display:inline-block;border-radius:5px;padding:.1rem .45rem;font-size:.68rem;font-weight:700}
.lob-core{background:#dbeafe;color:#1e40af}
.lob-srs{background:#dcfce7;color:#15803d}
.mand-dot{color:#f59e0b;font-size:.9rem;cursor:help;margin-right:.25rem}
/* filter */
.fbar{display:flex;flex-wrap:wrap;gap:.65rem;margin-bottom:1.1rem;align-items:center}
.fbar input{flex:1;min-width:160px;padding:.5rem .85rem;border:1px solid #cbd5e1;
  border-radius:8px;font-size:.82rem;outline:none}
.fbar input:focus{border-color:#0f2d5a;box-shadow:0 0 0 3px rgba(15,45,90,.1)}
.fbtn{padding:.45rem .9rem;border-radius:7px;font-size:.78rem;font-weight:600;
  cursor:pointer;border:1px solid #cbd5e1;background:#fff;color:#475569;transition:all .18s}
.fbtn:hover,.fbtn.active{border-color:#0f2d5a;background:#eff6ff;color:#0f2d5a}
.fbtn.fmiss.active{background:#fee2e2;border-color:#ef4444;color:#b91c1c}
.fcnt{font-size:.78rem;color:#94a3b8}
/* accordion */
.acc-item{border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;margin-bottom:.75rem;background:#fff}
.acc-head{display:flex;align-items:center;gap:.9rem;padding:1rem 1.25rem;
  cursor:pointer;user-select:none;transition:background .15s}
.acc-head:hover{background:#f8faff}
.acc-arrow{font-size:.9rem;transition:transform .25s;color:#64748b;flex-shrink:0}
.acc-item.open .acc-arrow{transform:rotate(90deg)}
.acc-body{display:none;padding:0 1.25rem 1.25rem;border-top:1px solid #f1f5f9}
.acc-item.open .acc-body{display:block}
.acc-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin-top:1rem}
@media(max-width:900px){.acc-grid{grid-template-columns:1fr}}
.info-box{background:#f8faff;border-radius:8px;padding:.9rem 1rem;font-size:.82rem;line-height:1.6}
.info-box h4{font-size:.8rem;font-weight:700;color:#0a1f3c;margin-bottom:.4rem;
  text-transform:uppercase;letter-spacing:.04em}
.gap-list li{margin:.25rem 0;padding-left:.5rem}
.gap-list li::marker{color:#ef4444}
.wf-list li{margin:.25rem 0;padding-left:.5rem}
.wf-list li::marker{color:#22c55e}
/* findings */
.find-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1rem}
.find-card{display:flex;gap:.85rem;align-items:flex-start;background:#fff;
  border-radius:12px;padding:1.1rem 1.2rem;
  box-shadow:0 1px 6px rgba(0,0,0,.06);font-size:.83rem;line-height:1.6}
.find-icon{font-size:1.5rem;flex-shrink:0;margin-top:.05rem}
.find-warn{border-left:4px solid #f59e0b}
.find-info{border-left:4px solid #3b82f6}
.find-ok{border-left:4px solid #22c55e}
.find-red{border-left:4px solid #ef4444}
/* roadmap */
.roadmap{position:relative;padding-left:2.5rem;margin-top:1.5rem}
.roadmap::before{content:"";position:absolute;left:.85rem;top:0;bottom:0;
  width:3px;background:linear-gradient(180deg,#0f2d5a,#2563eb,#22c55e)}
.rm-item{position:relative;margin-bottom:1.75rem}
.rm-dot{position:absolute;left:-2.5rem;top:.15rem;width:18px;height:18px;
  border-radius:50%;border:3px solid #fff;box-shadow:0 0 0 2px #0f2d5a;
  display:flex;align-items:center;justify-content:center;font-size:.6rem;font-weight:700;color:#0f2d5a;background:#fff}
.rm-phase{font-size:.7rem;font-weight:700;color:#2563eb;text-transform:uppercase;letter-spacing:.05em}
.rm-title{font-size:.95rem;font-weight:700;color:#0a1f3c;margin:.2rem 0 .3rem}
.rm-items{font-size:.82rem;color:#475569;line-height:1.7}
/* pptx outline */
.slide-list{counter-reset:slides}
.slide-item{display:flex;align-items:flex-start;gap:.75rem;padding:.65rem .9rem;
  border-radius:8px;background:#fff;border:1px solid #e2e8f0;margin-bottom:.45rem}
.slide-num{background:#0f2d5a;color:#fff;border-radius:5px;padding:.1rem .5rem;
  font-size:.75rem;font-weight:700;flex-shrink:0;min-width:32px;text-align:center}
.slide-title{font-weight:600;font-size:.85rem;color:#0a1f3c}
.slide-note{font-size:.78rem;color:#64748b;margin-top:.15rem}
/* summary stats */
.stats-row{display:flex;flex-wrap:wrap;gap:1rem;margin-bottom:2rem}
.stat-box{background:#fff;border-radius:12px;padding:1.1rem 1.5rem;flex:1;
  min-width:150px;box-shadow:0 2px 8px rgba(0,0,0,.06);text-align:center}
.stat-num{font-size:2rem;font-weight:800;color:#0f2d5a}
.stat-lbl{font-size:.78rem;color:#64748b;margin-top:.2rem}
/* vision box */
.vision-box{background:linear-gradient(135deg,#0f2d5a,#1a4a8a);color:#fff;
  border-radius:16px;padding:2rem 2.5rem;margin-bottom:2rem}
.vision-box h3{font-size:1rem;font-weight:700;opacity:.75;text-transform:uppercase;
  letter-spacing:.06em;margin-bottom:.75rem}
.vision-box p{font-size:1.05rem;line-height:1.7;font-style:italic}
/* methodology */
.meth-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem}
.meth-card{background:#fff;border-radius:12px;padding:1.25rem;
  box-shadow:0 1px 8px rgba(0,0,0,.06);border-top:4px solid #0f2d5a}
.meth-num{font-size:1.5rem;font-weight:800;color:#0f2d5a;margin-bottom:.3rem}
.meth-title{font-size:.92rem;font-weight:700;margin-bottom:.5rem}
.meth-body{font-size:.82rem;color:#475569;line-height:1.6}
/* scope box */
.scope-box{background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
  padding:1rem 1.25rem;font-size:.84rem;line-height:1.6;margin-top:1rem}
.scope-box strong{color:#92400e}
/* priority project highlight */
.priority-banner{background:linear-gradient(90deg,#78350f,#b45309);color:#fff;
  font-size:.7rem;font-weight:700;padding:.15rem .7rem;border-radius:0 0 6px 6px;
  letter-spacing:.05em;text-align:center;margin:-1.5rem -1.5rem .9rem}
.card.is-priority{border:2px solid #f59e0b;box-shadow:0 0 0 3px rgba(245,158,11,.15),0 2px 14px rgba(0,0,0,.1)}
.priority-col-head{background:#78350f!important}
/* pending */
.card.is-pending{border:2px dashed #94a3b8;opacity:.85}
.pending-overlay{background:#f1f5f9;border-radius:8px;padding:.9rem;text-align:center;
  color:#64748b;font-size:.82rem;margin:.5rem 0}
/* region summary */
.region-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1rem}
.reg-card{background:#fff;border-radius:12px;padding:1.2rem;
  box-shadow:0 1px 8px rgba(0,0,0,.06);border-left:5px solid #0f2d5a}
.reg-name{font-size:.85rem;font-weight:700;color:#0a1f3c}
.reg-count{font-size:2rem;font-weight:800;color:#0f2d5a}
.reg-projects{font-size:.75rem;color:#64748b;line-height:1.6;margin-top:.3rem}
/* footer */
.footer{text-align:center;color:#94a3b8;font-size:.76rem;padding:2rem;border-top:1px solid #e2e8f0}
@media print{.nav,.fbar{position:static}.tbl-wrap{max-height:none;overflow:visible}body{background:#fff}}
"""

JS = """
const secs = document.querySelectorAll('section[id]');
const navs = document.querySelectorAll('.nav a');
window.addEventListener('scroll',()=>{
  let cur='';
  secs.forEach(s=>{if(window.scrollY>=s.offsetTop-130)cur=s.id});
  navs.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+cur));
},{passive:true});
navs.forEach(a=>a.addEventListener('click',e=>{
  e.preventDefault();
  document.querySelector(a.getAttribute('href')).scrollIntoView({behavior:'smooth',block:'start'});
}));
// accordion
document.querySelectorAll('.acc-head').forEach(h=>{
  h.addEventListener('click',()=>{
    const item=h.closest('.acc-item');
    item.classList.toggle('open');
  });
});
// matrix filter
let aStat='all', aLob='all';
function filterMatrix(){
  const q=document.getElementById('roleSearch').value.toLowerCase();
  let vis=0;
  document.querySelectorAll('#matBody tr.role-row').forEach(row=>{
    const rn=row.querySelector('td.td-role').textContent.toLowerCase();
    const lob=row.dataset.lob;
    const cells=[...row.querySelectorAll('td[data-status]')];
    const hasS=aStat==='all'||cells.some(c=>c.dataset.status===aStat);
    const lobOk=aLob==='all'||lob===aLob;
    const txtOk=q===''||rn.includes(q);
    const show=lobOk&&txtOk&&hasS;
    row.classList.toggle('hidden',!show);
    if(show)vis++;
  });
  document.getElementById('rCnt').textContent=vis+' role'+(vis!==1?'s':'')+' shown';
}
function fLob(lob,btn){
  aLob=lob;
  document.querySelectorAll('.fbtn[data-lob]').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');filterMatrix();
}
function fStat(s,btn){
  aStat=s;
  document.querySelectorAll('.fbtn[data-stat]').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');filterMatrix();
}
filterMatrix();
"""

def render_methodology():
    pillars = [
        ("1","Pull Current OBS (As-Is)",
         "Extract the existing project OBS (Current OBS) from each Hitachi Rail (HR) project — capturing both the On-shore and Off-shore organizational structure, entity breakdown, role titles, and personnel assignments."),
        ("2","Compare Current OBS → PTO (To-Be)",
         "Compare the extracted 'As-Is' Current OBS against the PTO standard (G-TRN A08001 To-Be). Map equivalent roles, identify gaps (missing roles), partial matches (naming misalignment), and extra roles (legacy GTS)."),
        ("3","Provide Rationale",
         "Explain the root cause of the current organizational structure: Legacy project context (GTS vs RSBU), multi-entity CBTC delivery model, regional maturity, customer requirements, and contractual constraints."),
        ("4","Determine Way Forward",
         "Based on the maturity assessment, recommend the transition path: Align Now, Partial Transition, Action Required, or Exception Documented — with specific named actions per Current OBS."),
    ]
    factors = [
        ("🔧","Technology","IS / MS / CS Solution maturity in the region. Reflects whether the local team has sufficient CBTC product knowledge."),
        ("🛠","Tools Readiness","Availability and adoption of standard project management tools, ERP, planning and reporting platforms."),
        ("👥","Resource Knowledge Base","Depth and breadth of qualified project team members with CBTC execution experience in the country/region."),
        ("📋","Customer Requirements","Complexity, rigour, and specificity of the customer's contractual and governance requirements."),
        ("🏗","Structure / Strategy Fit","How closely the current OBS aligns with the G-TRN A08001 PTO standard and the CBTC operating model."),
    ]
    p_html = "".join(f'''<div class="meth-card">
      <div class="meth-num">{n}</div>
      <div class="meth-title">{t}</div>
      <div class="meth-body">{b}</div>
    </div>''' for n, t, b in pillars)
    f_html = "".join(f'''<div style="display:flex;gap:.65rem;align-items:flex-start;padding:.7rem;
      background:#fff;border-radius:8px;border:1px solid #e2e8f0;font-size:.82rem">
      <span style="font-size:1.2rem">{ic}</span>
      <div><b>{t}</b><br><span style="color:#475569">{b}</span></div>
    </div>''' for ic, t, b in factors)
    return f'''<section id="methodology">
  <h2 class="sec-title">Assessment Methodology</h2>
  <div class="meth-grid">{p_html}</div>
  <div style="margin-top:1.5rem">
    <div style="font-size:.9rem;font-weight:700;color:#0a1f3c;margin-bottom:.75rem">
      Maturity Assessment Factors — CBTC Business Segment × Region
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:.75rem">
      {f_html}
    </div>
  </div>
  <div class="scope-box">
    <strong>⚑ Scope of this Initial Assessment:</strong>
    This assessment focuses primarily on the <strong>Project Manager (PM)</strong> role within the PTO — accountability, single-PM principle, and reporting structure. Initial findings are also provided for
    <strong>Project Engineer (PE / SEM)</strong> and <strong>Project RAMS Manager</strong>.
    Subsequent dedicated assessments are recommended for: <em>Project Engineer, Commissioning Manager, Project RAMS Manager</em>.
    <br><br>
    <strong>Key Structural Finding:</strong>
    CBTC Solution Development is primarily executed in <strong>Canada (Toronto competence centre)</strong>.
    This creates an inherent offshore-onshore split in all CBTC projects and is the biggest single influence on project OBS structure across the portfolio.
  </div>
</section>'''

def render_portfolio_overview(results):
    region_data = {}
    for r in results:
        reg = r["region"]
        if reg not in region_data:
            region_data[reg] = []
        region_data[reg].append(r)
    total = len(results)
    total_m  = sum(r["matched"]  for r in results)
    total_p  = sum(r["partial"]  for r in results)
    total_ms = sum(r["missing"]  for r in results)
    pct_cov  = round((total_m + total_p) / (total * TOTAL_N) * 100)
    high_risk = sum(1 for r in results if r["risk"] == "HIGH")
    action_req = sum(1 for r in results if r["wf_category"] == "action")
    stats = f'''<div class="stats-row">
      <div class="stat-box"><div class="stat-num">{total}</div><div class="stat-lbl">Projects Assessed</div></div>
      <div class="stat-box"><div class="stat-num">{len(STANDARD_ROLES)}</div><div class="stat-lbl">Standard Roles (G-TRN)</div></div>
      <div class="stat-box"><div class="stat-num">{MANDATORY_N}</div><div class="stat-lbl">Mandatory Core Roles</div></div>
      <div class="stat-box"><div class="stat-num" style="color:#22c55e">{total_m}</div><div class="stat-lbl">Total Matched Roles</div></div>
      <div class="stat-box"><div class="stat-num" style="color:#f59e0b">{total_p}</div><div class="stat-lbl">Partial Matches</div></div>
      <div class="stat-box"><div class="stat-num" style="color:#ef4444">{total_ms}</div><div class="stat-lbl">Missing Roles (Gaps)</div></div>
      <div class="stat-box"><div class="stat-num" style="color:#ef4444">{high_risk}</div><div class="stat-lbl">High-Risk Projects</div></div>
      <div class="stat-box"><div class="stat-num" style="color:#f59e0b">{action_req}</div><div class="stat-lbl">Action Required</div></div>
    </div>'''
    reg_cards = ""
    region_colors = {
        "Americas – NA":"#2563eb","APAC – SE Asia":"#16a34a",
        "APAC – Other":"#15803d","MEA":"#d97706","SE & LATAM":"#db2777","Europe – UK":"#7c3aed"
    }
    for reg, projs in region_data.items():
        col = region_colors.get(reg, "#0f2d5a")
        names = ", ".join(p["short"] for p in projs)
        reg_cards += f'''<div class="reg-card" style="border-left-color:{col}">
          <div class="reg-name">{REGION_ICONS.get(reg,"")} {reg}</div>
          <div class="reg-count" style="color:{col}">{len(projs)}</div>
          <div style="font-size:.7rem;color:{col};font-weight:600">PROJECTS</div>
          <div class="reg-projects">{names}</div>
        </div>'''
    return f'''<section id="overview">
  <h2 class="sec-title">Portfolio Overview</h2>
  {stats}
  <div class="region-grid">{reg_cards}</div>
</section>'''

def render_scorecards(results):
    cards = ""
    for r in results:
        mat      = r["maturity"]
        is_pri   = r.get("priority", False)
        is_pend  = r.get("pending",  False)
        pri_cls  = "is-priority" if is_pri  else ""
        pend_cls = "is-pending"  if is_pend else ""
        pri_banner = '<div class="priority-banner">★ PMO PRIORITY PROJECT</div>' if is_pri else ""
        mat_rows = ""  # maturity removed from scorecard (see deep dive for details)
        multi_pm = r.get("multi_pm", [])
        multi_pm_html = ""
        if len(multi_pm) > 1:
            names_str = " / ".join(
                f"{o['title']}{(' — ' + o['name']) if o.get('name') else ''} ({o['entity']})"
                for o in multi_pm
            )
            multi_pm_html = (f'<div style="background:#fff8e1;border:1px solid #fde68a;border-radius:6px;'
                             f'padding:.35rem .6rem;font-size:.7rem;margin:.4rem 0;color:#78350f">'
                             f'⚠ Multi-PM: {names_str}</div>')
        pend_body = '<div class="pending-overlay">⏳ OBS data not yet available.<br>Submit OBS file to trigger full gap analysis.</div>' if is_pend else ""
        cards += f'''<div class="card {pri_cls} {pend_cls}">
          {pri_banner}
          <div class="sc-head">
            <div class="sc-name">{PRIORITY_STAR if is_pri else ""}{r["name"]}</div>
            <div class="sc-city">📍 {r["city"]}</div>
            <div class="sc-tags">
              <span class="tag tag-region">{r["region"]}</span>
              <span class="tag tag-lob">{r["lob"]}</span>
              <span class="tag tag-leg">{r["legacy"]}</span>
            </div>
            <div style="font-size:.73rem;color:#64748b">
              <b>Offshore:</b> {r["entity_offshore"]}<br>
              <b>Onshore:</b> {r["entity_onshore"]}
            </div>
          </div>
          {pend_body if is_pend else f'''
          <div class="sc-body">
            {donut_svg(r["matched"], r["partial"], r["missing"])}
            <div class="sc-stats">
              <div class="stat"><span class="dot" style="background:#22c55e"></span><b>{r["matched"]}</b>&nbsp;Matched</div>
              <div class="stat"><span class="dot" style="background:#f59e0b"></span><b>{r["partial"]}</b>&nbsp;Partial</div>
              <div class="stat"><span class="dot" style="background:#ef4444"></span><b>{r["missing"]}</b>&nbsp;Missing</div>
            </div>
          </div>
          <div class="sc-bars">
            <div class="bar-lbl">Mandatory roles covered</div>
            {bar_h(r["pct_mand"])}
            <div class="bar-lbl" style="margin-top:5px">All standard roles covered</div>
            {bar_h(r["pct_total"])}
          </div>
          {multi_pm_html}
          '''}
          <div class="sc-foot" style="margin-top:.7rem">
            <span>Risk {risk_badge(r["risk"])}</span>
            {wf_badge(r["wf_category"])}
          </div>
        </div>'''
    pri_n = sum(1 for r in results if r.get("priority"))
    pend_n = sum(1 for r in results if r.get("pending"))
    note = f'<div style="font-size:.82rem;color:#64748b;margin-bottom:1rem">'\
           f'<span style="color:#f59e0b;font-weight:700">★ {pri_n} PMO Priority Projects</span> highlighted with gold border  · '\
           f'<span style="color:#64748b">⏳ {pend_n} projects pending OBS submission</span></div>'
    return f'<section id="scorecard"><h2 class="sec-title">Compliance Scorecard — All {len(results)} Projects</h2>{note}<div class="grid-5">{cards}</div></section>'

def render_matrix(results):
    # Only include projects that have an actual OBS (not pending)
    active = [r for r in results if not r.get("pending")]
    # compact matrix – project columns show just icon
    proj_th = "".join(
        f'<th class="th-proj{" priority-col-head" if r.get("priority") else ""}" title="{("★ PRIORITY — " if r.get("priority") else "") + r["name"]}">'  
        f'<div style="writing-mode:vertical-lr;transform:rotate(180deg);max-height:100px;font-size:.68rem">'
        f'{("★ " if r.get("priority") else "") + r["short"]}</div></th>'
        for r in active)
    lob_order = ["SRS+VHC","SRS"]
    lob_labels = {"SRS+VHC":"Core Roles — All Projects (Mandatory)","SRS":"SRS-Specific Roles"}
    body = ""
    prev_lob = None
    for std in STANDARD_ROLES:
        if std["lob"] != prev_lob:
            if std["lob"] in lob_labels:
                nc = 4 + len(active)
                body += f'<tr class="sec-row"><td colspan="{nc}">{lob_labels[std["lob"]]}</td></tr>'
                prev_lob = std["lob"]
        mand_cls = "mand" if std["mandatory"] else ""
        lob_css  = "lob-core" if std["lob"]=="SRS+VHC" else "lob-srs"
        mand_icon = '<span class="mand-dot" title="Mandatory">●</span>' if std["mandatory"] else ""
        cells = ""
        for r in active:
            si = next(i for i, sr in enumerate(STANDARD_ROLES) if sr["role"] == std["role"])
            if std["role"] == "Project Manager" and len(r.get("multi_pm", [])) > 1:
                cells += multi_pm_cell(r["multi_pm"])
            else:
                cells += status_cell(r["role_results"][si]["status"],
                                     r["role_results"][si]["title"],
                                     r["role_results"][si]["entity"],
                                     r["role_results"][si].get("name", ""))
        body += (f'<tr class="role-row {mand_cls}" data-lob="{std["lob"]}">'
                 f'<td class="td-abbr">{std["abbr"]}</td>'
                 f'<td class="td-role">{mand_icon}{std["role"]}</td>'
                 f'<td class="td-lob"><span class="lob-tag {lob_css}">{std["lob"]}</span></td>'
                 f'<td class="td-mand">{"Yes" if std["mandatory"] else "—"}</td>'
                 f'{cells}</tr>\n')
    pend_n = len(results) - len(active)
    pend_note = (f'<div style="font-size:.78rem;color:#94a3b8;margin-bottom:.6rem">'
                 f'ℹ {pend_n} pending project{"s" if pend_n!=1 else ""} (no OBS submitted) excluded from matrix.</div>') if pend_n else ""
    return f'''<section id="matrix">
  <h2 class="sec-title">OBS Gap Analysis Matrix — {len(active)} Projects × {len(STANDARD_ROLES)} PTO Standard Roles</h2>
  {pend_note}
  <div class="fbar">
    <input type="text" id="roleSearch" placeholder="🔍 Search role…" oninput="filterMatrix()"/>
    <button class="fbtn active" data-lob="all" onclick="fLob('all',this)">All LoB</button>
    <button class="fbtn" data-lob="SRS+VHC" onclick="fLob('SRS+VHC',this)">Mandatory Core</button>
    <button class="fbtn" data-lob="SRS" onclick="fLob('SRS',this)">SRS-Specific</button>
    <button class="fbtn fmiss" data-stat="missing" onclick="fStat('missing',this)">⚠ Gaps Only</button>
    <button class="fbtn" data-stat="all" onclick="fStat('all',this)">Show All</button>
    <span class="fcnt" id="rCnt"></span>
  </div>
  <div class="tbl-wrap">
    <table class="matrix">
      <thead><tr>
        <th style="width:48px">Abbr</th>
        <th class="th-role">PTO Standard Role (G-TRN A08001)</th>
        <th style="width:75px">LoB</th>
        <th style="width:70px">Mandatory</th>
        {proj_th}
      </tr></thead>
      <tbody id="matBody">{body}</tbody>
    </table>
  </div>
</section>'''

def render_deep_dives(results):
    def offshore_entity_key(proj):
        """Extract primary entity name from entity_offshore field."""
        s = proj.get("entity_offshore", "")
        return s.split("(")[0].strip().lower()

    def split_roles_by_entity(proj):
        """Split roles into offshore and onshore based on entity_offshore field."""
        key = offshore_entity_key(proj)
        offshore, onshore = [], []
        for obs in proj.get("roles", []):
            ent = obs["entity"].lower()
            if key and key != "n/a" and any(w in ent for w in key.split() if len(w) > 2):
                offshore.append(obs)
            else:
                onshore.append(obs)
        return offshore, onshore

    def roles_table(role_list, color):
        if not role_list:
            return '<div style="font-size:.78rem;color:#94a3b8;font-style:italic">None / same entity</div>'
        rows = ""
        for o in role_list:
            name_part = f' <span style="color:#0f2d5a;font-style:italic">({o["name"]})</span>' if o.get("name") else ""
            rows += (f'<div style="padding:.2rem 0;border-bottom:1px solid #f1f5f9;font-size:.78rem">'
                     f'<span style="color:{color}">●</span> {o["title"]}{name_part} '
                     f'<span style="color:#94a3b8;font-size:.7rem">{o["entity"]}</span></div>')
        return rows

    items = ""
    for r in results:
        is_pri  = r.get("priority", False)
        is_pend = r.get("pending",  False)
        pri_strip = f'<div style="background:linear-gradient(90deg,#78350f,#b45309);color:#fff;font-size:.72rem;font-weight:700;padding:.3rem .9rem;border-radius:8px 8px 0 0;margin-bottom:.75rem;letter-spacing:.04em">★ PMO PRIORITY PROJECT</div>' if is_pri else ""
        matched_roles = [(rr["std"]["role"], rr["title"], rr["entity"])
                         for rr in r["role_results"] if rr["status"] == S_MATCH]
        partial_roles = [(rr["std"]["role"], rr["title"], rr["entity"])
                         for rr in r["role_results"] if rr["status"] == S_PARTIAL]
        missing_roles = [rr["std"]["role"]
                         for rr in r["role_results"] if rr["status"] == S_MISSING and rr["std"]["mandatory"]]
        missing_srs   = [rr["std"]["role"]
                         for rr in r["role_results"] if rr["status"] == S_MISSING and not rr["std"]["mandatory"]]
        gap_html = ""
        if missing_roles:
            gap_html += "<div style='font-size:.8rem;font-weight:700;color:#b91c1c;margin:.5rem 0 .25rem'>⚑ Missing Mandatory Roles:</div>"
            gap_html += "<ul class='gap-list'>" + "".join(f"<li>{g}</li>" for g in missing_roles) + "</ul>"
        if partial_roles:
            gap_html += "<div style='font-size:.8rem;font-weight:700;color:#92400e;margin:.5rem 0 .25rem'>~ Naming Misalignment (Partial Match):</div>"
            gap_html += "<ul style='list-style:disc;padding-left:1.2rem;font-size:.8rem'>" \
                + "".join(f"<li><b>{s}</b> → found as <em>{t}</em> ({e})</li>" for s,t,e in partial_roles) \
                + "</ul>"
        if missing_srs:
            gap_html += "<div style='font-size:.8rem;font-weight:700;color:#64748b;margin:.5rem 0 .25rem'>ℹ SRS Roles Not Visible in OBS:</div>"
            gap_html += "<ul style='list-style:circle;padding-left:1.2rem;font-size:.8rem;color:#64748b'>" \
                + "".join(f"<li>{g}</li>" for g in missing_srs) + "</ul>"
        if not gap_html:
            gap_html = '<div style="color:#15803d;font-size:.82rem">✔ No critical gaps identified. Good alignment to G-TRN standard.</div>'
        extra_html = ""
        if r["extras"]:
            extra_html = "<div style='font-size:.8rem;font-weight:700;color:#1d4ed8;margin:.5rem 0 .25rem'>+ Extra / Legacy GTS Roles (not in G-TRN standard):</div>"
            extra_html += "<ul style='list-style:disc;padding-left:1.2rem;font-size:.8rem;color:#475569'>" \
                + "".join(f"<li>{e['title']} <span style='color:#94a3b8'>({e['entity']})</span></li>"
                          for e in r["extras"][:12]) + "</ul>"
        mat = r["maturity"]
        # maturity removed from display
        mat_html = ""
        # Pre-compute offshore/onshore split and multi-PM warning outside the f-string
        multi_pm_list = r.get("multi_pm", [])
        if len(multi_pm_list) > 1:
            pm_names = " / ".join(
                f'{o["title"]}{(" \u2014 " + o["name"]) if o.get("name") else ""} ({o["entity"]})'
                for o in multi_pm_list
            )
            multi_pm_dd = (f'<div style="background:#fff3cd;border:1px solid #ffc107;border-radius:6px;'
                           f'padding:.4rem .75rem;font-size:.78rem;color:#78350f;margin-bottom:.6rem">'
                           f'<b>\u26a0 Multiple PM/Director roles found:</b> {pm_names}. '
                           f'G-TRN A08001 requires a single accountable Project Manager.</div>')
        else:
            multi_pm_dd = ""
        if not is_pend:
            off, on = split_roles_by_entity(r)
            offshore_onshore_html = (
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:.8rem;margin-bottom:.9rem">'
                f'<div class="info-box" style="background:#eff6ff;border:1px solid #bfdbfe">'
                f'<h4 style="color:#1d4ed8">Offshore Roles \u2014 {r["entity_offshore"]}</h4>'
                f'{roles_table(off, "#1d4ed8")}</div>'
                f'<div class="info-box" style="background:#f0fdf4;border:1px solid #bbf7d0">'
                f'<h4 style="color:#15803d">Onshore Roles \u2014 {r["entity_onshore"]}</h4>'
                f'{roles_table(on, "#15803d")}</div></div>'
            )
        else:
            offshore_onshore_html = ""
        items += f'''<div class="acc-item{'  is-priority-acc' if is_pri else ''}" id="acc-{r['id']}" style="{'border:2px solid #f59e0b;' if is_pri else ''}">
          {pri_strip}
          <div class="acc-head" style="{'background:#fffbeb;' if is_pri else ''}">
            <span class="acc-arrow">▶</span>
            <div style="flex:1">
              <div style="display:flex;align-items:center;gap:.75rem;flex-wrap:wrap">
                <b style="font-size:.95rem;color:#0a1f3c">{r["name"]}</b>
                <span style="font-size:.75rem;color:#64748b">{r["city"]} · {r["date"]}</span>
                <span class="tag tag-region" style="margin:0">{r["region"]}</span>
                {risk_badge(r["risk"])}
                {wf_badge(r["wf_category"])}
              </div>
            </div>
            <div style="display:flex;gap:1rem;align-items:center;font-size:.82rem">
              <span style="color:#22c55e;font-weight:700">{r["matched"]}✔</span>
              <span style="color:#f59e0b;font-weight:700">{r["partial"]}~</span>
              <span style="color:#ef4444;font-weight:700">{r["missing"]}✘</span>
            </div>
          </div>
          <div class="acc-body">
            {'<div style="background:#fff8e1;border:1px solid #fde68a;border-radius:8px;padding:.75rem 1rem;font-size:.82rem;margin-bottom:.9rem"><b>⏳ OBS Data Pending</b> — No OBS file available. Submit the project OBS to enable full gap analysis.</div>' if is_pend else ''}
            {multi_pm_dd}
            {offshore_onshore_html}
            <div class="acc-grid">
              <div>
                <div class="info-box">
                  <h4>As-Is — Current OBS Structure</h4>
                  <div><b>Entity Structure:</b><br>
                    Offshore: {r["entity_offshore"]}<br>
                    Onshore: {r["entity_onshore"]}
                  </div>
                  <div style="margin-top:.5rem"><b>Rationale:</b><br>{r["rationale"]}</div>
                </div>
              </div>
              <div>
                <div class="info-box" style="background:#fff8f8;border:1px solid #fecaca">
                  <h4 style="color:#b91c1c">Gap Analysis — As-Is vs To-Be</h4>
                  {gap_html}
                  {extra_html}
                </div>
                <div class="info-box" style="margin-top:.8rem;background:#f0fdf4;border:1px solid #bbf7d0">
                  <h4 style="color:#15803d">Way Forward — Transition Recommendation</h4>
                  <div style="margin-bottom:.5rem">{wf_badge(r["wf_category"])}</div>
                  <p style="font-size:.82rem;color:#166534">{r["wf_action"]}</p>
                </div>
              </div>
            </div>
          </div>
        </div>'''
    return f'<section id="deepdives"><h2 class="sec-title">Project Deep Dives — As-Is / Gaps / Way Forward</h2>{items}</section>'

def render_key_findings():
    findings = [
        ("find-red",   "🔴", "Multiple PM Structure — Systemic Gap",
         "The most prevalent structural gap across the CBTC portfolio is the presence of <b>multiple Project Managers</b> (per entity: Canada PM, France PM, Singapore PM) or a <b>Project Director layer above PM</b>. G-TRN A08001 mandates a <b>single accountable PM</b>. This affects 14 of 18 projects assessed."),
        ("find-warn",  "⚠",  "Role Naming Misalignment — Legacy GTS Titles",
         "<b>Financial Controller → Project Controller</b>, <b>SEM → Project Engineer</b>, <b>PDA → Project Engineer</b>, <b>TIC/T&C Manager → Commissioning Manager</b>. These are same-function roles with different names. Renaming and formalizing per G-TRN A08001 is the quickest and lowest-risk transition action."),
        ("find-warn",  "⚠",  "RAMS Coverage — Inconsistent Visibility",
         "Project RAMS Manager is a mandatory SRS role per G-TRN A08001. It is only explicitly visible in <b>6 of 18 projects</b>. In several projects safety functions are present (Safety Engineering, Safety Authority, Safety Assurance) but these are <em>independent roles</em>, not the PM's RAMS Manager."),
        ("find-info",  "ℹ",  "Canada Technology Lead Model — Structural Influence",
         "CBTC Solution Development is led by <b>HR Canada (Toronto)</b>. This creates a baseline offshore-onshore split in all projects. The G-TRN model accommodates this through the WPM/WPL hierarchy — Canada roles should be formalised as MWPMs or WPMs reporting to a single PM, not as parallel PMs."),
        ("find-info",  "ℹ",  "Project Director Role — Not in G-TRN Standard",
         "The 'Project Director' role appears in Abou Qir, CML1, Hyderabad, Crosstown, and others. G-TRN does not include a Project Director in the PTO. This role should be mapped to <b>Functional Management</b> (e.g., Portfolio Director, Programme Director) outside the project team structure."),
        ("find-ok",    "✔",  "Strong Quality & Safety Coverage",
         "Quality Assurance and Safety roles are well-covered across the portfolio. 16 of 18 projects have a visible QA role and 14 have a safety-related role. These map well to G-TRN Project Quality Manager and Project RAMS/Safety Manager."),
        ("find-ok",    "✔",  "APAC Singapore — Pilot Ready",
         "R152B SA1 URS Singapore has the highest role coverage in the portfolio (16/12 standard roles matched or partially matched). APAC Singapore is confirmed as the <b>Pilot for PM maturity assessment</b> per the CBTC operating model plan."),
        ("find-info",  "ℹ",  "UK Programme (DLR/4GSCS) — Programme Model Consideration",
         "DLR and 4GSCS share the same Senior PM and team. The G-TRN model allows a programme-level PM with project WPMs. Recommend formalising this as a single PM with WPL/WPM structure beneath, aligned to the UK programme governance model."),
        ("find-warn",  "⚠",  "Commissioning Manager Coverage — SRS Critical Role",
         "Commissioning/T&C Manager is present in only <b>8 of 18 projects</b> at the top-level OBS. This is an SRS-specific role and is critical for project delivery. It should be explicitly added to OBS where missing (DUAT, Blue Line, NYCT, MMMP, Hyderabad, Blue Line, Singapore Hub)."),
        ("find-info",  "ℹ",  "Draft OBS Projects — Formalisation Needed",
         "MMMP Ph2 Saudi Arabia has a <b>Draft OBS</b>. Formalising the OBS per G-TRN A08001 structure before execution progresses is strongly recommended. This is an opportunity to implement G-TRN from the start."),
    ]
    cards = "".join(f'''<div class="find-card {cls}">
      <div class="find-icon">{icon}</div>
      <div><b>{title}</b><br><span style="color:#475569">{body}</span></div>
    </div>''' for cls, icon, title, body in findings)
    return f'<section id="findings"><h2 class="sec-title">Key Findings &amp; Recommendations</h2><div class="find-grid">{cards}</div></section>'

def render_transition_roadmap(results):
    phase_projects = {
        "immediate": [r for r in results if r["wf_category"] == "aligned"],
        "phase1":    [r for r in results if r["wf_category"] == "partial"],
        "phase2":    [r for r in results if r["wf_category"] == "action"],
    }
    def proj_pills(lst):
        return " ".join(f'<span style="background:#dbeafe;color:#1d4ed8;border-radius:6px;'
                        f'padding:.1rem .55rem;font-size:.72rem;font-weight:600">{r["short"]}</span>'
                        for r in lst)
    return f'''<section id="roadmap">
  <h2 class="sec-title">Transition Roadmap — Way Forward</h2>
  <div class="roadmap">
    <div class="rm-item">
      <div class="rm-dot">✔</div>
      <div class="rm-phase">Now — Immediate (0–3 months)</div>
      <div class="rm-title">Publish G-TRN A08001 Awareness & Role Naming Alignment</div>
      <div class="rm-items">
        • All projects: rename legacy GTS titles to G-TRN equivalents (Financial Controller → Project Controller, SEM → Project Engineer, T&C Manager → Commissioning Manager)<br>
        • APAC Singapore (R152B): Pilot PM maturity assessment. Designate single PM. Canada / France leads move to WPM roles.<br>
        • UK (DLR/4GSCS): Formalise programme PM model with WPL/WPM hierarchy.<br>
        • All PMs acknowledge G-TRN A08001 and confirm OBS compliance status.
      </div>
      {proj_pills(phase_projects["phase1"][:5])}
    </div>
    <div class="rm-item">
      <div class="rm-dot">1</div>
      <div class="rm-phase">Phase 1 — Short-Term (3–6 months)</div>
      <div class="rm-title">Structural Alignment for Partial-Match Projects</div>
      <div class="rm-items">
        • Projects with partial compliance: close specific gaps (add missing roles to OBS, remove Project Director from PM PTO, add RAMS coverage)<br>
        • OEWL, Taiwan Xidong, Istanbul, KL Midlife, HK TME: targeted OBS updates<br>
        • Crosstown: Confirm single PM; restructure Project Director to Portfolio Director (functional)<br>
        • Agree on formal exceptions with LoB/Region management where justified<br>
        • Launch PM competency assessment pilot (APAC-Singapore)
      </div>
      {proj_pills(phase_projects["phase1"])}
    </div>
    <div class="rm-item">
      <div class="rm-dot">2</div>
      <div class="rm-phase">Phase 2 — Medium-Term (6–12 months)</div>
      <div class="rm-title">Full G-TRN Transition for Action-Required Projects</div>
      <div class="rm-items">
        • Projects with multiple structural gaps: full OBS restructure per G-TRN A08001<br>
        • Abou Qir + CML1 Cairo: Single PM per project; Project Director → functional management<br>
        • DUAT Dubai: Add QA, HSE, RAMS, Contract Manager roles to OBS<br>
        • MMMP Saudi: Finalise Draft OBS with full G-TRN structure<br>
        • NYCT R211, SFMTA: Formalise PM accountability, add Planner and RAMS roles<br>
        • SG Engineering Hub: Integrate into parent project PTO as WPM/WPL structure
      </div>
      {proj_pills(phase_projects["phase2"])}
    </div>
    <div class="rm-item">
      <div class="rm-dot">3</div>
      <div class="rm-phase">Phase 3 — Ongoing (12+ months)</div>
      <div class="rm-title">Full Portfolio Compliance & Subsequent Role Assessments</div>
      <div class="rm-items">
        • All 18 projects: full G-TRN A08001 OBS in place and formally documented<br>
        • Launch subsequent assessments: <b>Project Engineer (PE/SEM)</b>, <b>Commissioning Manager</b>, <b>Project RAMS Manager</b><br>
        • CBTC PM competency and maturity assessment rolled out to all regions<br>
        • Integrate G-TRN PTO requirements into new bid OBS templates<br>
        • Annual OBS compliance review process established
      </div>
    </div>
  </div>
</section>'''

def render_pptx_outline(results):
    high_risk = [r for r in results if r["risk"] == "HIGH"]
    action = [r for r in results if r["wf_category"] == "action"]
    region_groups = {}
    for r in results:
        region_groups.setdefault(r["region"], []).append(r["short"])
    slides = [
        ("Cover",
         "CBTC PTO Transition Plan — OBS Gap Analysis",
         "Title: 'Project Team Organisation — Gap Analysis & Transition Plan'. Subtitle: G-TRN A08001 vs 18 Active Execution Projects. Date, Author, Confidentiality."),
        ("Executive Summary",
         "Key Findings at a Glance",
         "3 key numbers (18 projects, X gaps, X action required). Vision statement. 3 headline findings. Risk heat-map by region."),
        ("Vision & Objective",
         "Purpose of this Assessment",
         "Vision: Unified scalable project organization. Objectives. Scope statement (PM focus, PE/Commissioning/RAMS next steps)."),
        ("Methodology",
         "How We Assessed — 4 Pillars",
         "Pillar 1: Pull Current OBS (As-Is). Pillar 2: Compare Current OBS vs PTO (G-TRN A08001). Pillar 3: Rationale. Pillar 4: Way Forward. Hitachi Rail (HR) Canada influence note."),
        ("Maturity Framework",
         "Maturity Assessment Factors",
         "5 factors: Technology, Tools, Resources, Customer, Structure. Rating scale 1-5. Pilot: APAC Singapore."),
        ("Portfolio Overview",
         "18 Projects — Regional Breakdown",
         "Region map/summary. Project count per region. Legacy type breakdown (Legacy GTS vs Legacy RSBU)."),
        ("Key Structural Findings",
         "Top 5 Portfolio-Wide Issues",
         "1. Multiple PM structure (14/18 projects). 2. Role naming misalignment. 3. RAMS coverage gaps. 4. Canada technology lead model. 5. Project Director layer."),
        ("Gap Analysis Matrix",
         f"OBS Compliance Matrix — All {len(results)} Current OBS × 12 PTO Roles",
         "Colour-coded heatmap comparing each project Current OBS to the PTO standard. ✔ Green = Matched, ~ Amber = Partial, ✘ Red = Missing."),
        ("Scorecard Summary",
         "Compliance % per Project",
         "Bar chart or table: each project's mandatory %, total %, risk level. Sorted by compliance score."),
        *[(f"Project Deep Dive — {r['short']}",
           f"As-Is OBS | Gaps | Way Forward",
           f"Entity structure (offshore/onshore). Gap summary. Rationale. Transition recommendation. Maturity score.")
          for r in results],
        ("Transition Roadmap",
         "4-Phase Transition Plan",
         "Phase 0 (Now): Naming alignment. Phase 1 (0-3m): Partial transitions. Phase 2 (3-6m): Action required projects. Phase 3 (ongoing): Full compliance + PE/RAMS assessments."),
        ("Next Steps",
         "Actions & Owners",
         "Priority actions table: Action | Owner | Timeline | Status. APAC Singapore PM pilot. Role deep-dives for PE, Commissioning, RAMS."),
        ("Appendix A",
         "PTO Standard Role Definitions (G-TRN A08001)",
         "Table of all 12 PTO standard roles with abbreviation, LoB, mandatory status, and key responsibilities."),
        ("Appendix B",
         "URS (Urban Railway Signalling) Generic OBS Reference",
         "Reference copy of the Hitachi Rail URS Generic OBS from 83410775-PRJ-CAN-EN Rev 012. Shows the legacy project structure that Current OBS are compared against."),
        ("Appendix C",
         "Full Role Inventory per Current OBS",
         "Detailed role listing for each project: Current OBS role → PTO mapped role → gap/action."),
    ]
    slide_html = "".join(f'''<div class="slide-item">
      <span class="slide-num">S{i+1}</span>
      <div>
        <div class="slide-title">{t}</div>
        <div class="slide-note">{note}</div>
      </div>
    </div>''' for i, (t, _, note) in enumerate(slides))
    return f'''<section id="pptx">
  <h2 class="sec-title">Recommended PowerPoint Slide Outline ({len(slides)} slides)</h2>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:.5rem 1.5rem">
    {slide_html}
  </div>
</section>'''

def render_generic_obs():
    """Render the Hitachi Rail URS Generic OBS as an interactive org chart.
    Source: 83410775-PRJ-CAN-EN Rev 012 — Generic OBS for URS (Urban Railway Signalling) Projects."""

    def node(title, color="#0f2d5a", sub=None, width="auto"):
        sub_html = f'<div style="font-size:.67rem;color:rgba(255,255,255,.75);margin-top:2px">{sub}</div>' if sub else ""
        return (f'<div style="background:{color};color:#fff;border-radius:7px;padding:.4rem .8rem;'
                f'font-size:.75rem;font-weight:700;text-align:center;min-width:130px;width:{width};'
                f'box-shadow:0 2px 6px rgba(0,0,0,.18);white-space:nowrap">'
                f'{title}{sub_html}</div>')

    def group(title, children_html, color="#1a4a8a", bg="#f0f7ff"):
        return (f'<div style="border:2px solid {color};border-radius:10px;background:{bg};padding:.75rem 1rem">'
                f'<div style="font-size:.7rem;font-weight:700;color:{color};text-transform:uppercase;'
                f'letter-spacing:.05em;margin-bottom:.6rem">{title}</div>'
                f'<div style="display:flex;flex-wrap:wrap;gap:.4rem;align-items:flex-start">{children_html}</div>'
                f'</div>')

    pm_box    = node("Project Manager (PM)", "#0a1f3c", sub="Single Accountable Leader", width="200px")
    pom_group = group("Program Office",
        node("Project Office Manager", "#1e40af") +
        node("Data Manager", "#1e40af") +
        node("Administrative Assistant", "#3b82f6", sub="via Data Mgr") +
        node("Publications WPM", "#3b82f6", sub="via Data Mgr") +
        node("Project Planner", "#1e40af") +
        node("Risk &amp; Opportunity Manager", "#1e40af"),
        "#1e40af", "#eff6ff")
    ctrl_group = group("Project Controls",
        node("Project Financial Controller", "#15803d") +
        node("Contract Manager", "#15803d") +
        node("Acquisition / Procurement PM", "#15803d") +
        node("Quality Assurance Manager", "#15803d") +
        node("Project Configuration Manager", "#15803d"),
        "#15803d", "#f0fdf4")
    safety_group = group("Technical Safety (Independent / Dotted Line)",
        node("Safety Authority", "#7c3aed", sub="Independent") +
        node("Project Safety Manager", "#7c3aed") +
        node("Safety Assurance Manager", "#7c3aed") +
        node("RAM Lead", "#7c3aed") +
        node("Independent Validator", "#7c3aed") +
        node("Indep. SW Assessor", "#6d28d9") +
        node("Indep. Safety Assessor", "#6d28d9") +
        node("Cyber Security Authority", "#6d28d9") +
        node("Project Cybersecurity Manager (PCM)", "#6d28d9") +
        node("Localised Safety Manager", "#6d28d9"),
        "#7c3aed", "#faf5ff")
    sem_group = group("Solution Engineering (SEM Lead)",
        node("Solution Eng. Manager (SEM)", "#b45309", sub="Engineering Lead") +
        node("Chief Engineering Architect", "#b45309") +
        node("Project Design Authority (PDA)", "#b45309") +
        node("PDA Product/Platform", "#92400e") +
        node("System WPM", "#92400e") +
        node("System Engineers", "#92400e") +
        node("Architect", "#92400e") +
        node("Data Comms Systems Manager", "#92400e") +
        node("SW Engineering Manager", "#92400e") +
        node("SW Architect", "#78350f") +
        node("SW Engineers", "#78350f") +
        node("SW CM Controller", "#78350f") +
        node("HW Engineering Manager", "#92400e") +
        node("HW Architect", "#78350f") +
        node("HW Engineers", "#78350f") +
        node("HW CM Controller", "#78350f") +
        node("IVVQ Manager", "#92400e") +
        node("HW IVQ Manager", "#78350f") +
        node("SW IV Manager", "#78350f"),
        "#b45309", "#fffbeb")
    deploy_group = group("Solution Deployment",
        node("Deployment Project Manager", "#0e7490") +
        node("SID WPM", "#0e7490") +
        node("Site Deployment Lead", "#0e7490") +
        node("Site Configuration Manager", "#0891b2") +
        node("Subcontractor Manager", "#0891b2") +
        node("HSE Manager", "#0891b2") +
        node("Training", "#0891b2") +
        node("Service Delivery Manager (SDM)", "#0891b2") +
        node("Lifecycle Support", "#0e7490") +
        node("Integrated Logistics Support", "#0e7490"),
        "#0e7490", "#ecfeff")

    return f'''<section id="generic_obs">
  <h2 class="sec-title">Hitachi Rail — URS Generic OBS (As-Is Reference Baseline)</h2>
  <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:.9rem 1.25rem;font-size:.82rem;margin-bottom:1.25rem;line-height:1.6">
    <b>Source:</b> 83410775-PRJ-CAN-EN Rev 012 (May 2025) — <i>URS Generic WBS, OBS and RACI Matrix</i>
    &nbsp;·&nbsp; <b>URS</b> = Urban Railway Signalling (legacy Hitachi Rail CBTC delivery methodology)
    &nbsp;·&nbsp; <b>HR</b> = Hitachi Rail (formerly GTS — Global Traction Systems)
    <br>This is the <b>standard "As-Is" OBS</b> that most existing CBTC projects are based on.
    The gap analysis in this report compares each project's Current OBS against the <b>PTO standard (G-TRN A08001)</b>.
  </div>
  <div style="display:flex;flex-direction:column;align-items:center;gap:.75rem">
    <div style="display:flex;justify-content:center">{pm_box}</div>
    <div style="width:3px;height:20px;background:#0a1f3c"></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:.75rem;width:100%;max-width:1200px">
      {pom_group}
      {ctrl_group}
    </div>
    <div style="width:3px;height:20px;background:#7c3aed"></div>
    <div style="width:100%;max-width:1200px">{safety_group}</div>
    <div style="width:3px;height:20px;background:#b45309"></div>
    <div style="width:100%;max-width:1200px">{sem_group}</div>
    <div style="width:3px;height:20px;background:#0e7490"></div>
    <div style="width:100%;max-width:1200px">{deploy_group}</div>
  </div>
  <div style="margin-top:1.25rem;background:#f8faff;border-radius:8px;padding:.9rem 1.1rem;font-size:.8rem;color:#475569">
    <b style="color:#0a1f3c">Key Structural Differences vs G-TRN A08001 PTO:</b>
    <ul style="margin-top:.5rem;padding-left:1.25rem;line-height:1.9">
      <li>URS OBS has <b>larger engineering hierarchy</b> (SEM, Chief Engineering Architect, multiple SW/HW WPMs) not present as individual PTO roles</li>
      <li>URS uses <b>"Project Financial Controller"</b> (PCC) — PTO calls this <b>"Project Controller"</b></li>
      <li>URS has <b>"Acquisition Project Manager"</b> (Procurement) — PTO calls this <b>"Supply Chain &amp; Procurement Manager"</b></li>
      <li>URS separates <b>Safety Engineering / Safety Assurance / Safety Authority</b> — PTO consolidates under <b>"Project RAMS Manager"</b></li>
      <li>URS has <b>"Deployment Project Manager"</b> — PTO calls this <b>"Commissioning Manager"</b></li>
      <li>Many current project OBS add a <b>Project Director or Portfolio Director</b> above the PM — this is <b>not aligned</b> with the G-TRN A08001 single-PM principle</li>
    </ul>
  </div>
</section>'''


def render_legend():
    items = [
        ("#dcfce7","#bbf7d0","✔ Matched","Role name/keyword found in project OBS (match score ≥ 88%)"),
        ("#fef9c3","#fde68a","~ Partial","Similar role with different name — needs renaming/alignment"),
        ("#fee2e2","#fecaca","✘ Missing","Standard role has no equivalent in OBS — this is a GAP"),
        ("#dbeafe","#bfdbfe","+ Extra/Legacy","Role in OBS not in G-TRN standard (legacy GTS / project-specific)"),
        ("#fffdf0","#fde68a","● Mandatory Row","Mandatory core role required for ALL projects"),
    ]
    html = "".join(f'<div class="find-card" style="border-left:4px solid {bc}">'
                   f'<div style="width:32px;height:22px;background:{bg};border-radius:4px;flex-shrink:0"></div>'
                   f'<div><b>{label}</b><br><span style="color:#475569;font-size:.8rem">{desc}</span></div></div>'
                   for bg, bc, label, desc in items)
    abbrevs = [
        ("PTO", "Project Team Organisation — the standard structure defined in G-TRN A08001"),
        ("G-TRN", "Group Transport standard number (A08001) — defines the PTO for CBTC SRS projects"),
        ("OBS", "Organisational Breakdown Structure — the actual project team org chart"),
        ("HR", "Hitachi Rail — the delivering entity (previously known as GTS: Global Traction Systems)"),
        ("URS", "Urban Railway Signalling — the legacy brand/methodology for CBTC project delivery"),
        ("SRS", "Signalling, Rolling Stock and Services — the Hitachi Rail business segment"),
        ("SEM", "Solution Engineering Manager — leads the engineering workpackage (maps to Project Engineer in PTO)"),
        ("PDA", "Project Design Authority — technical authority for solution design"),
        ("RAMS", "Reliability, Availability, Maintainability and Safety"),
        ("PPTM", "Project Portfolio / Programme Manager — legacy GTS title above the PM level"),
        ("WPM", "Work Package Manager — responsible for a specific WBS work package"),
        ("IVVQ", "Integration, Verification, Validation and Qualification"),
    ]
    abbrev_html = "".join(f'<div style="display:flex;gap:.75rem;font-size:.81rem;padding:.45rem .7rem;background:#f8faff;border-radius:6px;border:1px solid #e2e8f0">'
                          f'<b style="color:#0a1f3c;min-width:60px">{a}</b><span style="color:#475569">{d}</span></div>'
                          for a, d in abbrevs)
    return f'''<section id="legend">
  <h2 class="sec-title">Legend &amp; Acronyms</h2>
  <div class="find-grid">{html}</div>
  <div style="margin-top:1.5rem">
    <div style="font-size:.9rem;font-weight:700;color:#0a1f3c;margin-bottom:.75rem">Key Acronyms Used in This Report</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:.5rem">{abbrev_html}</div>
  </div>
</section>'''

# ═══════════════════════════════════════════════════════════════════════════
# 6. FULL HTML ASSEMBLY
# ═══════════════════════════════════════════════════════════════════════════
def build_html(results):
    pri_projects  = [r for r in results if r.get("priority")]
    pend_projects = [r for r in results if r.get("pending")]
    n = len(results)
    nav = """<nav class="nav">
      <a href="#summary">Summary</a>
      <a href="#methodology">Methodology</a>
      <a href="#overview">Portfolio</a>
      <a href="#generic_obs">Generic OBS</a>
      <a href="#scorecard">Scorecard</a>
      <a href="#matrix">Gap Matrix</a>
      <a href="#deepdives">Deep Dives</a>
      <a href="#findings">Findings</a>
      <a href="#roadmap">Roadmap</a>
      <a href="#pptx">PPTX Outline</a>
      <a href="#legend">Legend</a>
    </nav>"""
    vision = '''<div class="vision-box">
      <h3>Vision — To-Be State</h3>
      <p>"To create a unified and scalable project organization that combines global expertise with regional strength —
      driven by clear accountability, consistent ways of working, and empowered teams — to deliver safe, high-quality,
      and successful CBTC projects."</p>
    </div>'''
    pri_pills = " ".join(f'<span style="background:linear-gradient(90deg,#78350f,#b45309);color:#fff;border-radius:8px;padding:.2rem .65rem;font-size:.72rem;font-weight:700">★ {r["short"]}</span>' for r in pri_projects)
    summary_sec = f'''<section id="summary">
      <h2 class="sec-title">Executive Summary</h2>
      {vision}
      <div style="background:#fffbeb;border:2px solid #f59e0b;border-radius:12px;padding:1rem 1.5rem;margin-bottom:1.5rem">
        <div style="font-size:.85rem;font-weight:700;color:#78350f;margin-bottom:.6rem">★ {len(pri_projects)} PMO Priority Projects — highlighted throughout this report</div>
        <div style="display:flex;flex-wrap:wrap;gap:.35rem">{pri_pills}</div>
      </div>
      <div class="find-grid">
        <div class="find-card find-red">
          <div class="find-icon">⚑</div>
          <div><b>Primary Gap — Single PM Principle</b><br>
          14 of {n} projects have multiple PMs or a Project Director layer above the PM.
          G-TRN A08001 mandates <b>one single accountable PM</b>.</div>
        </div>
        <div class="find-card find-warn">
          <div class="find-icon">~</div>
          <div><b>Naming Misalignment — Legacy GTS Titles</b><br>
          Most roles exist under different names (SEM, PDA, Financial Controller, TIC Manager).
          Quick wins available through <b>title alignment</b> without structural change.</div>
        </div>
        <div class="find-card find-ok">
          <div class="find-icon">✔</div>
          <div><b>Strong Quality & Safety Foundation</b><br>
          88% of projects have visible QA roles and 78% have safety coverage.
          Core delivery capability exists — structure formalization is the priority.</div>
        </div>
      </div>
    </section>'''
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>CBTC PTO Gap Analysis — G-TRN A08001 vs {n} Projects</title>
<style>{CSS}</style>
</head>
<body>
<div class="hero">
  <h1>CBTC PTO Transition Plan — OBS Gap Analysis</h1>
  <p>G-TRN A08001 Standard Project Team Organisation vs {n} Projects  ·  <span style="color:#fbbf24">★ {len(pri_projects)} PMO Priority Projects</span></p>
  <div class="hero-meta">
    <span class="pill">G-TRN A08001 Rev.00 · April 2026</span>
    <span class="pill">{n} Projects Assessed</span>
    <span class="pill" style="background:rgba(245,158,11,.25);border-color:rgba(245,158,11,.5)">★ {len(pri_projects)} Priority Projects</span>
    <span class="pill">{len(STANDARD_ROLES)} Standard Roles</span>
    <span class="pill">SRS · CBTC Business Segment</span>
    <span class="pill">Report Date: 2026-06-17</span>
    <span class="pill">CONFIDENTIAL — Hitachi Rail Internal</span>
  </div>
</div>
{nav}
<div class="main">
  {summary_sec}
  {render_methodology()}
  {render_portfolio_overview(results)}
  {render_generic_obs()}
  {render_scorecards(results)}
  {render_matrix(results)}
  {render_deep_dives(results)}
  {render_key_findings()}
  {render_transition_roadmap(results)}
  {render_pptx_outline(results)}
  {render_legend()}
</div>
<div class="footer">
  Generated by obs_full_report.py · Hitachi Rail PMO · CBTC Business Segment · Report Date: 2026-06-17
</div>
<script>{JS}</script>
</body>
</html>"""

# ═══════════════════════════════════════════════════════════════════════════
# 7. MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    out_dir = r"\\spiderman\DEPARTMENTS\Project_Management_Office\Artificial_Intelligence\26_OBS Compare\2_Output"
    os.makedirs(out_dir, exist_ok=True)
    print("Building CBTC PTO Gap Analysis report …")
    results = build_project_results()
    html    = build_html(results)
    out     = os.path.join(out_dir, "CBTC_PTO_Gap_Analysis.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✔  Saved: {out}")
    print(f"\n{'Project':<42} {'P':>2} {'Match':>6} {'Partial':>8} {'Missing':>8} {'Mand%':>7} {'Risk':>9} {'Way Forward'}")
    print("-"*103)
    for r in results:
        star = '★' if r.get('priority') else ' '
        pend = '⏳' if r.get('pending') else ' '
        print(f"{star}{pend} {r['name'][:38]:<38} {r['matched']:>6} {r['partial']:>8} {r['missing']:>8} "
              f"{r['pct_mand']:>6}%  {r['risk']:>9}  {r['wf_category']}")

if __name__ == "__main__":
    main()
