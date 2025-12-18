def rule_gate_node(state):
    query = state["query"].lower()
    ops = set()

    if any(w in query for w in ["insert", "add", "create"]):
        ops.add("INSERT")

    if any(w in query for w in ["update", "modify", "change"]):
        ops.add("UPDATE")

    if any(w in query for w in ["delete", "remove"]):
        ops.add("DELETE")

    if any(w in query for w in ["where", "filter"]):
        ops.add("SELECT_WHERE")

    if any(w in query for w in ["count", "sum", "avg", "average"]):
        ops.add("SELECT_AGGREGATE")

    if not ops:
        ops.add("SELECT_BASIC")

    state["allowed_operations"] = list(ops)
    return state
