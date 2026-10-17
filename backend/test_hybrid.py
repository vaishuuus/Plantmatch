from pathlib import Path

import pandas as pd

from recommenders.knowledge import filter_plants
from recommenders.content import content_scores
from recommenders.collaborative import CollaborativeRecommender
from recommenders.hybrid import blend

df = pd.read_csv(Path(__file__).parent / "data" / "plants.csv")
df["pet"] = df["pet"].astype(bool)
PLANTS = df.to_dict("records")
collab = CollaborativeRecommender()

u = {"light": 1, "water": 1, "humidity": 1, "size": 2, "effort": 1,
     "priority": "balanced", "pets": False}

passed, _ = filter_plants(PLANTS, u)
content = content_scores(passed, u)
crowd = collab.predict(passed, u)

rows = []
for p, s, c in zip(passed, content, crowd):
    rows.append((p["name"], s, c["score"], c["raters"], blend(s, c["score"], c["raters"])))

print(f"{'Plant':<18}{'content':>9}{'crowd':>8}{'raters':>8}{'FINAL':>8}")
for name, s, c, r, f in sorted(rows, key=lambda x: -x[4]):
    print(f"{name:<18}{s:>9.3f}{c:>8.3f}{r:>8}{f:>8.3f}")