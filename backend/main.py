from pathlib import Path
from typing import Literal

import pandas as pd
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from recommenders.knowledge import filter_plants, best_relaxation
from recommenders.content import content_scores, explain
from recommenders.collaborative import CollaborativeRecommender

BASE = Path(__file__).parent

# load the plants ONCE when the server starts
df = pd.read_csv(BASE / "data" / "plants.csv")
df["pet"] = df["pet"].astype(bool)
PLANTS = df.to_dict("records")          # list of dicts, one per plant
COLLAB = CollaborativeRecommender()     # loads users + ratings once at startup

app = FastAPI(title="PlantMatch API")


class Answers(BaseModel):
    """What the frontend sends. FastAPI rejects bad values automatically."""
    light: int = Field(ge=1, le=3)
    water: int = Field(ge=1, le=3)
    humidity: int = Field(ge=1, le=3)
    size: int = Field(ge=1, le=3)
    effort: int = Field(ge=1, le=3)
    priority: Literal["balanced", "easy", "light"] = "balanced"
    pets: bool = False


@app.get("/api/health")
def health():
    return {"status": "ok", "plants_loaded": len(PLANTS)}


@app.post("/api/recommend")
def recommend(answers: Answers):
    u = answers.model_dump()
    passed, rejected = filter_plants(PLANTS, u)        # Stage 1: knowledge filter

    ranked = []
    if passed:
        sims = content_scores(passed, u)               # Stage 2a: content-based
        community = COLLAB.predict(passed, u)          # Stage 2b: collaborative
        for p, s, c in zip(passed, sims, community):
            ranked.append({
                "plant": p,
                "score": float(s),                     # still content only, Day 4 blends the two
                "content": float(s),
                "collab": c["score"],
                "raters": c["raters"],
                "avg_rating": c["avg"],
                "why": explain(p, u),
            })
        ranked.sort(key=lambda r: r["score"], reverse=True)

    result = {"ranked": ranked, "rejected": rejected}
    if not ranked:
        result["relax"] = best_relaxation(PLANTS, u)
    return result


# MUST be last: serves your frontend folder at http://127.0.0.1:8000/
app.mount("/", StaticFiles(directory=BASE.parent / "frontend", html=True), name="frontend")