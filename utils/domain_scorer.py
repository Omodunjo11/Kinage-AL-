from config.signal_taxonomy import TAXONOMY

INTERSECTIONS = [
    ("DOMAIN_A", "DOMAIN_B"),
    ("DOMAIN_A", "DOMAIN_D"),
    ("DOMAIN_B", "DOMAIN_C"),
    ("DOMAIN_D", "DOMAIN_C"),
]

def compute_domain_scores(text: str):
    text = text.lower()
    domain_scores = {}

    for domain_key, domain_data in TAXONOMY.items():
        weight = domain_data["weight"]
        score = 0

        for cluster_phrases in domain_data["clusters"].values():
            for phrase in cluster_phrases:
                if phrase in text:
                    score += 1

        domain_scores[domain_key] = score * weight

    return domain_scores


def apply_intersection_multiplier(domain_scores):
    multiplier = 1.0

    for d1, d2 in INTERSECTIONS:
        if domain_scores.get(d1, 0) > 0 and domain_scores.get(d2, 0) > 0:
            multiplier *= 1.5

    return multiplier


def compute_total_signal(text: str):
    domain_scores = compute_domain_scores(text)
    multiplier = apply_intersection_multiplier(domain_scores)
    total_score = sum(domain_scores.values()) * multiplier

    return total_score, domain_scores
