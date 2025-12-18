def confidence_check_node(state):
    if state["confidence"] < 0.4:
        state["final_intent_id"] = None
    return state
