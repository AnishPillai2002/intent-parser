from collections import defaultdict

def voting_node(state):
    scores = defaultdict(float)

    for hit in state["vector_hits"]:
        weight = {
            "example": 1.0,
            "description": 0.8,
            "keyword": 0.4
        }.get(hit.payload["source"], 0.5)

        scores[hit.payload["intent_id"]] += hit.score * weight

    if not scores:
        state["final_intent_id"] = None
        state["confidence"] = 0.0
        return state

    best_intent, best_score = max(scores.items(), key=lambda x: x[1])
    total = sum(scores.values())

    state["intent_scores"] = dict(scores)
    state["final_intent_id"] = best_intent
    state["confidence"] = best_score / total

    return state
