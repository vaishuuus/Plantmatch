from pathlib import Path

import pandas as pd

from recommenders.knowledge import filter_plants
from recommenders.collaborative import CollaborativeRecommender

df = pd.read_csv(Path(__file__).parent / "data" / "plants.csv")
df["pet"] = df["pet"].astype(bool)
PLANTS = df.to_dict("records")

collab = CollaborativeRecommender()

personas = {
    "Dark dorm, forgetful": {"light": 1, "water": 1, "humidity": 1, "size": 2, "effort": 1, "pets": False},
    "Sunny balcony":        {"light": 3, "water": 1, "humidity": 1, "size": 1, "effort": 1, "pets": False},
}

for name, u in personas.items():
    passed, _ = filter_plants(PLANTS, u)
    preds = collab.predict(passed, u)
    print(f"\n=== {name} ===")
    for p, c in sorted(zip(passed, preds), key=lambda x: -x[1]["score"]):
        print(f"{p['name']:<18} community={c['score']:.3f}  raters={c['raters']:>2}  avg stars={c['avg']}")