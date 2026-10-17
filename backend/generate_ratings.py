"""
Generates SIMULATED users and ratings.
(State clearly in the report that this data is simulated.)
Each user has a room profile + a hidden taste that nudges their ratings.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from recommenders.knowledge import filter_plants

rng = np.random.default_rng(42)          # fixed seed = same data every run
DATA = Path(__file__).parent / "data"
N_USERS = 150

plants_df = pd.read_csv(DATA / "plants.csv")
plants_df["pet"] = plants_df["pet"].astype(bool)
PLANTS = plants_df.to_dict("records")

# hidden taste groups (plant ids from plants.csv)
TASTES = {
    "succulent": {7, 8, 17, 18, 19, 25, 27},
    "leafy":     {3, 5, 9, 10, 11, 12, 13, 14, 15, 16, 20, 21, 28},
    "classic":   {1, 2, 4, 6, 22, 23, 24, 26},
}


def closeness(a, b):
    return 1 - abs(a - b) / 2            # 1 = perfect, 0 = two steps off


users, ratings = [], []

for uid in range(1, N_USERS + 1):
    # 1) a random room
    u = {
        "light": int(rng.integers(1, 4)),
        "water": int(rng.integers(1, 4)),
        "humidity": int(rng.integers(1, 4)),
        "size": int(rng.integers(1, 4)),
        "effort": int(rng.integers(1, 4)),
        "pets": bool(rng.random() < 0.3),
    }
    taste = str(rng.choice(list(TASTES)))
    users.append({"user_id": uid, **u})        # taste is NOT saved: it stays hidden

    # 2) which plants would survive in this room?
    survives = {p["id"]: bool(filter_plants([p], u)[0]) for p in PLANTS}

    # 3) this user rates 8-13 plants, mostly ones that fit their room
    weights = np.array([3.0 if survives[p["id"]] else 1.0 for p in PLANTS])
    chosen = rng.choice(len(PLANTS), size=int(rng.integers(8, 14)),
                        replace=False, p=weights / weights.sum())

    for idx in chosen:
        p = PLANTS[idx]
        fit = np.mean([
            closeness(p["light_ideal"], u["light"]),
            closeness(p["water"], u["water"]),
            closeness(p["humidity"], u["humidity"]),
            closeness(p["effort"], u["effort"]),
        ])
        raw = 1 + 3.2 * fit                                   # good fit -> higher stars
        raw += 0.9 if p["id"] in TASTES[taste] else 0         # hidden taste bonus
        raw += rng.normal(0, 0.5)                             # human randomness
        if not survives[p["id"]]:
            raw = min(raw, 2.0)                               # the plant died :(
        ratings.append({"user_id": uid, "plant_id": p["id"],
                        "rating": int(np.clip(round(raw), 1, 5))})

pd.DataFrame(users).to_csv(DATA / "users.csv", index=False)
pd.DataFrame(ratings).to_csv(DATA / "ratings.csv", index=False)

r = pd.DataFrame(ratings)
density = len(r) / (N_USERS * len(PLANTS))
print(f"users: {N_USERS}  ratings: {len(r)}  density: {density:.0%}  mean rating: {r.rating.mean():.2f}")