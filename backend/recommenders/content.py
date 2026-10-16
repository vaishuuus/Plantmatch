"""
Stage 2a of the hybrid: CONTENT-BASED filtering.
Plants and the user are turned into vectors; cosine similarity ranks the plants.
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# which plant columns we compare, and which user answer each one is compared with
FEATURES = ["light_ideal", "water", "humidity", "effort"]
USER_KEY = {"light_ideal": "light", "water": "water", "humidity": "humidity", "effort": "effort"}

# "volume knobs": how much each feature matters, per priority choice
WEIGHTS = {
    "balanced": {"light_ideal": 0.35, "water": 0.25, "humidity": 0.20, "effort": 0.20},
    "easy":     {"light_ideal": 0.20, "water": 0.25, "humidity": 0.15, "effort": 0.40},
    "light":    {"light_ideal": 0.55, "water": 0.20, "humidity": 0.15, "effort": 0.10},
}

LIGHT_WORD = ["", "low light", "medium light", "bright light"]


def thermometer(value, levels=3):
    """The light-bulb ruler: 1 -> [1,0,0], 2 -> [1,1,0], 3 -> [1,1,1]"""
    return [1 if i < value else 0 for i in range(levels)]


def encode(values, w):
    """
    Turn one plant (or the user) into a vector.
    values: dict with the 4 feature values, w: the volume knobs.
    We multiply by sqrt(weight) so each weight acts like a plain
    'importance share' once cosine similarity does its math.
    """
    vec = []
    for f in FEATURES:
        vec.extend([np.sqrt(w[f]) * bit for bit in thermometer(values[f])])
    return np.array(vec)


def content_scores(plants, u):
    """Cosine similarity between the user's vector and EVERY plant's vector (0 to 1)."""
    w = WEIGHTS[u["priority"]]

    user_values = {f: u[USER_KEY[f]] for f in FEATURES}
    user_vec = encode(user_values, w).reshape(1, -1)           # one row

    plant_matrix = np.array([encode(p, w) for p in plants])    # one row per plant

    return cosine_similarity(user_vec, plant_matrix)[0]        # one score per plant


def explain(p, u):
    """Up to 3 'why this plant' lines, based on exact feature matches."""
    lines = []
    if p["light_ideal"] == u["light"]:
        lines.append(f"Happy in {LIGHT_WORD[u['light']]}")
    else:
        lines.append("Tolerates your light")
    if p["water"] == u["water"]:
        lines.append("Forgives missed waterings" if u["water"] == 1 else "Fits your watering rhythm")
    if u["pets"] and p["pet"]:
        lines.append("Pet-safe")
    if p["humidity"] == u["humidity"]:
        lines.append("Comfortable at your humidity")
    if p["effort"] == 1:
        lines.append("Very low maintenance")
    return lines[:3]