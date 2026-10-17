"""
Stage 2b of the hybrid: COLLABORATIVE filtering (neighborhood-based).
A new user has no ratings (cold start), so neighbors are found by ROOM-PROFILE
similarity. Then: predicted rating = what those neighbors thought of each plant.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from recommenders.content import thermometer

DATA = Path(__file__).parent.parent / "data"
PROFILE_COLS = ["light", "water", "humidity", "size", "effort"]


def profile_vector(u):
    """Room profile -> vector (light-bulb ruler again). Pets count extra, since they change which plants are OK."""
    vec = []
    for k in PROFILE_COLS:
        vec.extend(thermometer(int(u[k])))
    vec.extend([1 if u["pets"] else 0] * 3)
    return vec


class CollaborativeRecommender:
    def __init__(self, k=30):
        self.k = k                                     # how many neighbors to ask

        users = pd.read_csv(DATA / "users.csv")
        ratings = pd.read_csv(DATA / "ratings.csv")

        # profile matrix: one row per past user
        self.profiles = np.array([profile_vector(r) for r in users.to_dict("records")])

        # rating matrix R: rows = users, columns = plants, NaN = "never rated"
        matrix = ratings.pivot(index="user_id", columns="plant_id", values="rating")
        matrix = matrix.reindex(users["user_id"])      # same row order as the profiles
        self.col = {pid: i for i, pid in enumerate(matrix.columns)}
        self.R = matrix.to_numpy(dtype=float)

        self.user_mean = np.nanmean(self.R, axis=1)    # each user's own average (some are generous, some harsh)
        self.C = self.R - self.user_mean[:, None]      # "centered": rating minus that user's average
        self.global_mean = float(np.nanmean(self.R))
        self.item_mean = np.nanmean(self.R, axis=0)

    def predict(self, plants, u):
        """For each plant: community score (0-1), how many neighbors rated it, their average stars."""
        # 1) who are my neighbors? (most similar rooms)
        sims = cosine_similarity([profile_vector(u)], self.profiles)[0]
        top = np.argsort(sims)[::-1][: self.k]
        w = sims[top] ** 2                              # closer rooms count more

        out = []
        for p in plants:
            j = self.col.get(p["id"])
            if j is None:                               # nobody ever rated this plant
                out.append({"score": (self.global_mean - 1) / 4, "raters": 0, "avg": None})
                continue

            neighbor_dev = self.C[top, j]               # their "above/below own average" for this plant
            rated = ~np.isnan(neighbor_dev)

            if rated.any():
                dev = (w[rated] * neighbor_dev[rated]).sum() / w[rated].sum()
                pred = self.global_mean + dev           # weighted-average opinion
                avg = round(float(np.mean(self.R[top, j][rated])), 2)
            else:                                       # no neighbor tried it -> fall back to everyone's average
                pred, avg = self.item_mean[j], None

            out.append({
                "score": float(np.clip((pred - 1) / 4, 0, 1)),   # stars 1-5 -> 0-1
                "raters": int(rated.sum()),
                "avg": avg,
            })
        return out