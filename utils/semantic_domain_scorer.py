from config.domain_semantics import DOMAIN_SEMANTICS
from utils.embedding_utils import embed_text, cosine_similarity


# -------------------------------------------------
# Precompute Domain Embeddings Once
# -------------------------------------------------

DOMAIN_VECTORS = {
    domain: embed_text(data["description"])
    for domain, data in DOMAIN_SEMANTICS.items()
}


# Strategic intersection pairs
INTERSECTIONS = [
    ("DOMAIN_A", "DOMAIN_B"),
    ("DOMAIN_A", "DOMAIN_D"),
    ("DOMAIN_B", "DOMAIN_C"),
    ("DOMAIN_D", "DOMAIN_C"),
]


# -------------------------------------------------
# Compute Raw Similarity Scores
# -------------------------------------------------

def compute_semantic_domain_scores(text: str):
    """
    Returns:
        raw_similarities: cosine similarity per domain (0–1 scale)
        weighted_scores: similarity * strategic weight
    """

    article_vector = embed_text(text)

    raw_similarities = {}
    weighted_scores = {}

    for domain, domain_vector in DOMAIN_VECTORS.items():
        similarity = cosine_similarity(article_vector, domain_vector)
        weight = DOMAIN_SEMANTICS[domain]["weight"]

        raw_similarities[domain] = similarity
        weighted_scores[domain] = similarity * weight

    return raw_similarities, weighted_scores


# -------------------------------------------------
# Intersection Multiplier (Relative, Not Absolute)
# -------------------------------------------------

def apply_intersection_multiplier(raw_similarities: dict):
    """
    Apply multiplier when two domains are BOTH strongly activated
    relative to the strongest domain in the article.

    This avoids fragile absolute thresholds.
    """

    if not raw_similarities:
        return 1.0

    # Sort domains by similarity
    sorted_domains = sorted(
        raw_similarities.items(),
        key=lambda x: x[1],
        reverse=True
    )

    top_domain, top_score = sorted_domains[0]

    multiplier = 1.0

    for d1, d2 in INTERSECTIONS:
        if (
            raw_similarities.get(d1, 0) > 0.75 * top_score and
            raw_similarities.get(d2, 0) > 0.75 * top_score
        ):
            multiplier *= 1.5

    return multiplier


# -------------------------------------------------
# Total Strategic Signal
# -------------------------------------------------

def compute_total_signal(text: str):
    """
    Returns:
        total_score: weighted strategic score
        raw_similarities: per-domain similarity (for clustering)
    """

    raw_similarities, weighted_scores = compute_semantic_domain_scores(text)

    multiplier = apply_intersection_multiplier(raw_similarities)

    total_score = sum(weighted_scores.values()) * multiplier

    return total_score, raw_similarities
