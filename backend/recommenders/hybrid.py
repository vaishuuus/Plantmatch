"""
The HYBRID recommender (cascade + weighted):
  Stage 1  knowledge filter (knowledge.py)       -> removes plants that can't survive
  Stage 2  weighted blend of content + community -> ranks the survivors
The crowd's weight is reduced when few neighbors have rated a plant.
"""

CROWD_WEIGHT = 0.4     # max share of the crowd in the final score (content gets the rest)
MIN_RATERS = 5         # neighbors needed to fully trust the crowd


def blend(content, community, raters):
    """final = (1 - b) * content + b * community, where b shrinks if few raters."""
    trust = min(1.0, raters / MIN_RATERS)
    b = CROWD_WEIGHT * trust
    return (1 - b) * content + b * community


def community_line(raters, avg):
    """A 'why this plant' line from the crowd (or None if too few neighbors)."""
    if raters >= MIN_RATERS and avg is not None:
        return f"Rated {avg}★ by {raters} similar rooms"
    return None