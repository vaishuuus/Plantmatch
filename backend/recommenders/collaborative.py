"""
Stage 2b of the hybrid: COLLABORATIVE filtering (neighborhood-based).
Neighbors are found by ROOM-PROFILE similarity (a new user has no ratings yet: cold start).
Real feedback from the database is merged in as extra users on every reload().
"""
import threading
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from recommenders.content import thermometer

DATA = Path(__file__).parent.parent / "data"
PROFILE_COLS = ["light", "water", "humidity", "size", "effort"]


def profile_vector(u):
    """Room profile -> vector (light-bulb ruler). Pets count extra: they change which plants are OK."""
    vec = []
    for k in PROFILE_COLS:
        vec.extend(thermometer(int(u[k])))
    vec.extend([1 if u["pets"] else 0] * 3)
    return vec


class CollaborativeRecommender:
    def __init__(self, k=30):
        self.k = k                          # how many neighbors to ask
        self.lock = threading.Lock()        # reload() and predict() can run at the same moment
        self.reload()

    def reload(self, feedback=None):
        """(Re)build everything from the CSVs + real feedback (a pandas table from db.load_feedback())."""
        users = pd.read_csv(DATA / "users.csv")
        ratings = pd.read_csv(DATA / "ratings.csv")
        n_sim_users, n_sim_ratings, n_feedback = len(users), len(ratings), 0

        if feedback is not None and len(feedback) > 0:
            fb = feedback.copy()
            fb["user_id"] = 100000 + pd.factorize(fb["room_id"])[0]   # each search = one new user
            fb["pets"] = fb["pets"].astype(bool)
            fb_users = fb.drop_duplicates("user_id")[["user_id"] + PROFILE_COLS + ["pets"]]
            users = pd.concat([users, fb_users], ignore_index=True)
            ratings = pd.concat([ratings, fb[["user_id", "plant_id", "rating"]]], ignore_index=True)
            n_feedback = len(fb)

        profiles = np.array([profile_vector(r) for r in users.to_dict("records")])

        matrix = ratings.pivot(index="user_id", columns="plant_id", values="rating")
        matrix = matrix.reindex(users["user_id"])          # same row order as the profiles
        R = matrix.to_numpy(dtype=float)                   # NaN = never rated

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            global_mean = float(np.nanmean(R))
            counts = (~np.isnan(R)).sum(axis=1)
            # users with 2+ ratings: their own average; users with 1 rating: the global average
            user_mean = np.where(counts >= 2, np.nanmean(R, axis=1), global_mean)
            item_mean = np.nanmean(R, axis=0)

        with self.lock:                                    # swap everything in at once
            self.profiles = profiles
            self.col = {pid: i for i, pid in enumerate(matrix.columns)}
            self.R = R
            self.C = R - user_mean[:, None]                # rating minus the user's own average
            self.global_mean = global_mean
            self.item_mean = item_mean
            self.n_sim_users, self.n_sim_ratings, self.n_feedback = n_sim_users, n_sim_ratings, n_feedback

    def predict(self, plants, u):
        """For each plant: community score (0-1), how many neighbors rated it, their average stars."""
        with self.lock:
            profiles, R, C, col = self.profiles, self.R, self.C, self.col
            global_mean, item_mean = self.global_mean, self.item_mean

        sims = cosine_similarity([profile_vector(u)], profiles)[0]   # who has a room like mine?
        top = np.argsort(sims)[::-1][: self.k]
        w = sims[top] ** 2                                           # closer rooms count more

        out = []
        for p in plants:
            j = col.get(p["id"])
            if j is None:                                            # nobody ever rated it
                out.append({"score": (global_mean - 1) / 4, "raters": 0, "avg": None})
                continue

            dev = C[top, j]                                          # neighbors' "above/below own average"
            rated = ~np.isnan(dev)

            if rated.any():
                pred = global_mean + (w[rated] * dev[rated]).sum() / w[rated].sum()
                avg = round(float(np.mean(R[top, j][rated])), 2)
            else:
                pred, avg = item_mean[j], None

            out.append({
                "score": float(np.clip((pred - 1) / 4, 0, 1)),      # stars 1-5 -> 0-1
                "raters": int(rated.sum()),
                "avg": avg,
            })
        return out
    