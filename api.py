"""
api.py — FastAPI bridge for HiringTeam-Scorecard-demo
Drop this into: github.com/Talent-Drift/HiringTeam-Scorecard-demo

Imports your existing scoring_engine.py and exposes endpoints
the React dashboard calls. Zero changes to your existing files.

Endpoints:
  GET /api/health               — confirm API is running
  GET /api/scores               — all recruiter + HM scores (latest)
  GET /api/scores/{name}        — single person's scores + breakdown
  GET /api/historical           — all 6 snapshots from historical_performance_data.json
  GET /api/roles                — all open roles from sample_ats_export.csv
  GET /api/violations/{name}    — violations for a specific person
  GET /api/org                  — org summary (averages, totals)
  GET /api/departments          — scores broken down by department
"""

import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

# Import YOUR existing scoring engine — no changes to that file
from scoring_engine import ScorecardEngine

app = FastAPI(title="HireIQ API", version="1.0.0")

# ── CORS — allows the React frontend (on Vercel) to call this API ──────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tighten this to your Vercel URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load data once on startup ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_ats_data():
    """Load sample_ats_export.csv and run your scoring engine"""
    csv_path = os.path.join(BASE_DIR, "sample_ats_export.csv")
    df = pd.read_csv(csv_path)
    engine = ScorecardEngine(df)
    violations = engine.calculate_scores()
    recruiter_scores = engine.score_by_recruiter(violations)
    hm_scores = engine.score_by_hiring_manager(violations)
    org_summary = engine.get_org_summary(recruiter_scores, hm_scores)
    return {
        "raw": df,
        "violations": violations,
        "recruiter_scores": recruiter_scores,
        "hm_scores": hm_scores,
        "org_summary": org_summary,
    }

def load_historical():
    """Load historical_performance_data.json"""
    json_path = os.path.join(BASE_DIR, "historical_performance_data.json")
    with open(json_path, "r") as f:
        return json.load(f)

# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "message": "HireIQ API is running"}

# ── All scores (latest snapshot) ──────────────────────────────────────────────
@app.get("/api/scores")
def get_all_scores():
    """
    Returns recruiter and HM scores calculated live from your scoring engine.
    React dashboard calls this on load and when time filter changes.
    """
    data = load_ats_data()

    recruiters = data["recruiter_scores"].to_dict(orient="records")
    hms = data["hm_scores"].to_dict(orient="records")

    # Add rank
    recruiters_sorted = sorted(recruiters, key=lambda x: -x["final_score"])
    for i, r in enumerate(recruiters_sorted):
        r["rank"] = i + 1

    hms_sorted = sorted(hms, key=lambda x: -x["final_score"])
    for i, h in enumerate(hms_sorted):
        h["rank"] = i + 1

    return {
        "recruiters": recruiters_sorted,
        "hiring_managers": hms_sorted,
        "org_summary": data["org_summary"],
    }

# ── Single person's scores ─────────────────────────────────────────────────────
@app.get("/api/scores/{name}")
def get_person_score(name: str, role_type: str = "recruiter"):
    """
    Returns score breakdown for a specific person.
    role_type: 'recruiter' or 'hm'
    """
    data = load_ats_data()

    if role_type == "recruiter":
        scores_df = data["recruiter_scores"]
    else:
        scores_df = data["hm_scores"]

    person = scores_df[scores_df["name"] == name]
    if person.empty:
        raise HTTPException(status_code=404, detail=f"{name} not found")

    score_data = person.iloc[0].to_dict()

    # Add their violations
    violations = data["violations"]
    person_violations = violations[
        (violations["recruiter_name"] == name) |
        (violations["hiring_manager_name"] == name)
    ]

    score_data["violations"] = person_violations.to_dict(orient="records")

    # Add their roles
    raw = data["raw"]
    if role_type == "recruiter":
        roles = raw[raw["recruiter_name"] == name][
            ["requisition_id", "job_title", "team", "hiring_manager_name", "current_status"]
        ].drop_duplicates("requisition_id").to_dict(orient="records")
    else:
        roles = raw[raw["hiring_manager_name"] == name][
            ["requisition_id", "job_title", "team", "recruiter_name", "current_status"]
        ].drop_duplicates("requisition_id").to_dict(orient="records")

    score_data["roles"] = roles

    return score_data

# ── Historical snapshots ───────────────────────────────────────────────────────
@app.get("/api/historical")
def get_historical():
    """
    Returns all 6 biweekly snapshots from historical_performance_data.json.
    Used by the trend charts and time filter.
    """
    return load_historical()

# ── Historical for a specific person ──────────────────────────────────────────
@app.get("/api/historical/{name}")
def get_person_historical(name: str):
    """
    Returns score trend for a single person across all snapshots.
    Powers the individual trend sparklines.
    """
    historical = load_historical()
    snapshots = historical["snapshots"]

    trend = []
    for snap in snapshots:
        # Check recruiters
        for r in snap.get("recruiters", []):
            if r["name"] == name:
                trend.append({
                    "date": snap["snapshot_date"],
                    "final_score": r["final_score"],
                    "feedback_score": r["feedback_score"],
                    "velocity_score": r["velocity_score"],
                    "engagement_score": r["engagement_score"],
                    "role_type": "recruiter",
                })
        # Check HMs
        for h in snap.get("hiring_managers", []):
            if h["name"] == name:
                trend.append({
                    "date": snap["snapshot_date"],
                    "final_score": h["final_score"],
                    "feedback_score": h["feedback_score"],
                    "velocity_score": h["velocity_score"],
                    "engagement_score": h["engagement_score"],
                    "role_type": "hm",
                })

    if not trend:
        raise HTTPException(status_code=404, detail=f"No historical data for {name}")

    return {"name": name, "snapshots": trend}

# ── All open roles ─────────────────────────────────────────────────────────────
@app.get("/api/roles")
def get_roles(team: str = None):
    """
    Returns all open roles from sample_ats_export.csv.
    Optionally filter by team/department.
    """
    data = load_ats_data()
    raw = data["raw"]

    # Get one row per requisition (latest stage)
    roles = raw.sort_values("stage_entered_date", ascending=False)
    roles = roles.drop_duplicates("requisition_id")

    if team:
        roles = roles[roles["team"] == team]

    result = roles[[
        "requisition_id", "job_title", "team",
        "recruiter_name", "hiring_manager_name",
        "role_opened_date", "current_status", "stage"
    ]].to_dict(orient="records")

    return {"roles": result, "total": len(result)}

# ── Violations for a person ────────────────────────────────────────────────────
@app.get("/api/violations/{name}")
def get_violations(name: str):
    """
    Returns all SLA violations associated with a person.
    Used for the alerts panel in each dashboard.
    """
    data = load_ats_data()
    violations = data["violations"]

    person_v = violations[
        (violations.get("recruiter_name", pd.Series()) == name) |
        (violations.get("hiring_manager_name", pd.Series()) == name)
    ] if not violations.empty else pd.DataFrame()

    if violations.empty or person_v.empty:
        return {"name": name, "violations": [], "total": 0}

    v_list = person_v.fillna("").to_dict(orient="records")

    summary = {
        "high": int((person_v["severity"] == "high").sum()),
        "medium": int((person_v["severity"] == "medium").sum()),
        "low": int((person_v["severity"] == "low").sum()),
    }

    return {
        "name": name,
        "violations": v_list,
        "total": len(v_list),
        "summary": summary,
    }

# ── Org summary ────────────────────────────────────────────────────────────────
@app.get("/api/org")
def get_org_summary():
    """
    Returns org-level aggregates.
    Used by the Talent Intelligence dashboard KPI strip.
    """
    data = load_ats_data()
    return data["org_summary"]

# ── Department breakdown ───────────────────────────────────────────────────────
@app.get("/api/departments")
def get_departments():
    """
    Returns scores broken down by department/team.
    Used by the dept filter in Talent Intelligence.
    """
    data = load_ats_data()
    raw = data["raw"]
    recruiter_scores = data["recruiter_scores"]
    hm_scores = data["hm_scores"]

    teams = raw["team"].unique()
    result = []

    for team in teams:
        team_data = raw[raw["team"] == team]

        team_recruiters = team_data["recruiter_name"].unique()
        team_hms = team_data["hiring_manager_name"].unique()

        rec_scores = recruiter_scores[recruiter_scores["name"].isin(team_recruiters)]
        hm_scores_team = hm_scores[hm_scores["name"].isin(team_hms)]

        rec_avg = round(rec_scores["final_score"].mean(), 1) if len(rec_scores) > 0 else None
        hm_avg  = round(hm_scores_team["final_score"].mean(), 1) if len(hm_scores_team) > 0 else None

        dept_avg = None
        if rec_avg is not None and hm_avg is not None:
            dept_avg = round((rec_avg + hm_avg) / 2, 1)
        elif rec_avg is not None:
            dept_avg = rec_avg
        elif hm_avg is not None:
            dept_avg = hm_avg

        open_roles = len(team_data["requisition_id"].unique())

        result.append({
            "team": team,
            "avg_score": dept_avg,
            "recruiter_avg": rec_avg,
            "hm_avg": hm_avg,
            "open_roles": open_roles,
            "recruiters": list(team_recruiters),
            "hiring_managers": list(team_hms),
        })

    result.sort(key=lambda x: -(x["avg_score"] or 0))
    return {"departments": result}


# ── Run locally ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
