"""TEMPORARY scorer (same weighted idea as the JS prototype). Replaced by content-based cosine on Day 2."""

LIGHT_WORD = ["", "low light", "medium light", "bright light"]

WEIGHTS = {
    "balanced": {"light": 0.35, "water": 0.25, "humidity": 0.20, "effort": 0.20},
    "easy":     {"light": 0.20, "water": 0.25, "humidity": 0.15, "effort": 0.40},
    "light":    {"light": 0.55, "water": 0.20, "humidity": 0.15, "effort": 0.10},
}


def closeness(a, b):
    """1 = perfect match, 0.5 = one step off, 0 = two steps off."""
    return 1 - abs(a - b) / 2


def score_plant(p, u):
    parts = {
        "light":    closeness(p["light_ideal"], u["light"]),
        "water":    closeness(p["water"], u["water"]),
        "humidity": closeness(p["humidity"], u["humidity"]),
        "effort":   closeness(p["effort"], u["effort"]),
    }
    w = WEIGHTS[u["priority"]]
    total = sum(w[k] * parts[k] for k in w)
    return {"total": total, "parts": parts}


def explain(p, u, parts):
    """Up to 3 'why this plant' lines."""
    lines = []
    lines.append(f"Happy in {LIGHT_WORD[u['light']]}" if parts["light"] == 1 else "Tolerates your light")
    if parts["water"] == 1:
        lines.append("Forgives missed waterings" if u["water"] == 1 else "Fits your watering rhythm")
    if u["pets"] and p["pet"]:
        lines.append("Pet-safe")
    if parts["humidity"] == 1:
        lines.append("Comfortable at your humidity")
    if p["effort"] == 1:
        lines.append("Very low maintenance")
    return lines[:3]
