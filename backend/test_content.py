from pathlib import Path
import pandas as pd
from recommenders.knowledge import filter_plants
from recommenders.content import content_scores

df = pd.read_csv(Path(__file__).parent / "data" / "plants.csv")
df["pet"] = df["pet"].astype(bool)
PLANTS = df.to_dict("records")

u = {"light": 1, "water": 1, "humidity": 1, "size": 2, "effort": 1,
     "priority": "balanced", "pets": False}

passed, rejected = filter_plants(PLANTS, u)
sims = content_scores(passed, u)

for p, s in sorted(zip(passed, sims), key=lambda x: -x[1]):
    print(f"{p['name']:<18} {s:.3f}")
print("Kicked out:", len(rejected))