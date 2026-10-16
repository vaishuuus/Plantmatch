"""
Stage 1 of the hybrid: KNOWLEDGE-BASED (constraint) filtering.
Hard rules remove plants that cannot survive the user's conditions.
p = a plant (dict), u = the user's answers (dict)
"""

# each rule returns True if the plant SURVIVES that rule
CHECKS = {
    "light":    lambda p, u: p["light_min"] <= u["light"] <= p["light_max"],
    "water":    lambda p, u: p["water"] <= u["water"],            # can the user give enough water?
    "humidity": lambda p, u: p["humidity"] <= u["humidity"] + 1,  # not a humid-lover in a dry room
    "size":     lambda p, u: p["size"] <= u["size"],              # does it fit?
    "effort":   lambda p, u: p["effort"] <= u["effort"],          # will the user give enough care?
    "pets":     lambda p, u: (not u["pets"]) or p["pet"],         # pet-safe if user has pets
}

# sentence explaining WHY a plant was rejected
FAIL_TEXT = {
    "light":    lambda p, u: "Needs more light than your spot gets" if u["light"] < p["light_min"]
                             else "Scorches in that much sun",
    "water":    lambda p, u: "Needs more water than you plan to give",
    "humidity": lambda p, u: "Needs a more humid spot",
    "size":     lambda p, u: "Grows too big for your space",
    "effort":   lambda p, u: "Needs more care than you want to give",
    "pets":     lambda p, u: "Not pet-safe",
}

# used when NOTHING survives
RELAX_TEXT = {
    "light": "your light level", "water": "how often you can water",
    "humidity": "the humidity", "size": "the space",
    "effort": "the care level", "pets": "the pet-safe filter",
}


def filter_plants(plants, u, ignore=()):
    """Return (passed, rejected). `ignore` = rules to skip (for the 'what if I relax X' trick)."""
    passed, rejected = [], []
    for p in plants:
        # find the FIRST rule this plant breaks (None if it breaks nothing)
        failed = next(
            (rule for rule, check in CHECKS.items()
             if rule not in ignore and not check(p, u)),
            None,
        )
        if failed:
            rejected.append({"plant": p, "failed": failed, "reason": FAIL_TEXT[failed](p, u)})
        else:
            passed.append(p)
    return passed, rejected


def best_relaxation(plants, u):
    """If no plant survives: which ONE rule, if relaxed, lets in the most plants?"""
    best = None
    for rule in CHECKS:
        if rule == "pets" and not u["pets"]:
            continue
        count = len(filter_plants(plants, u, ignore=(rule,))[0])
        if best is None or count > best["count"]:
            best = {"rule": rule, "label": RELAX_TEXT[rule], "count": count}
    return best