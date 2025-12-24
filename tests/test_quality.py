import pytest
from fastapi.testclient import TestClient
from app.main import app  # Ensure this points to your actual FastAPI app instance

# Initialize the test client
client = TestClient(app)

# =========================================================================
# THE TEST DATASET
# =========================================================================
TEST_CASES = [
    # TEST GROUP 1: THE "CHEAPEST/TOP" DISTINCTION
    {
        "query": "Find the cheapest employee", 
        "expected_id": 112, 
        "expected_op": "SELECT_TOP_N",
        "rationale": "Needs ORDER BY ASC + LIMIT 1"
    },
    {
        "query": "Who is the highest paid engineer?", 
        "expected_id": 113, 
        "expected_op": "SELECT_FILTER_SORT_LIMIT", 
        "rationale": "Filter (Engineer) + Sort (Highest) + Limit"
    },
    {
        "query": "Show me the top 5 most recent orders", 
        "expected_id": 112, 
        "expected_op": "SELECT_TOP_N",
        "rationale": "Sort by Date DESC + LIMIT 5"
    },

    # TEST GROUP 2: GROUPING vs. FILTERING GROUPS
    {
        "query": "Show total sales per country", 
        "expected_id": 210, 
        "expected_op": "GROUP_BY_BASIC",
        "rationale": "Simple Group By"
    },
    {
        "query": "Which countries have total sales over 1 million?", 
        "expected_id": 220, 
        "expected_op": "GROUP_BY_HAVING",
        "rationale": "Group By + Having Condition (> 1M)"
    },
    {
        "query": "Count the number of active users per platform", 
        "expected_id": 211, 
        "expected_op": "GROUP_BY_FILTERED",
        "rationale": "Filter (Active) first, then Group By (Platform)"
    },

    # TEST GROUP 3: COMPLEX LOGIC & SUBQUERIES
    {
        "query": "Users with salary greater than the average", 
        "expected_id": 402, 
        "expected_op": "SUBQUERY_COMPARISON",
        "rationale": "Requires calculating average first, then comparing"
    },
    {
        "query": "Show employees who have never placed an order", 
        "expected_id": 401, 
        "expected_op": "SUBQUERY_FILTER",
        "rationale": "Requires 'NOT IN' subquery logic"
    },

    # TEST GROUP 4: JOINS (RELATIONAL)
    {
        "query": "List all employees and their department names", 
        "expected_id": 301, 
        "expected_op": "JOIN_BASIC",
        "rationale": "Explicitly asks for data from two related entities"
    },
    {
        "query": "How many orders did each customer place?", 
        "expected_id": 302, 
        "expected_op": "JOIN_AGGREGATE",
        "rationale": "Join Customers+Orders, then Count Grouped by Customer"
    },

    # TEST GROUP 5: EDGE CASES
    {
        "query": "Dump the whole user table", 
        "expected_id": 101, 
        "expected_op": "SELECT_BASIC",
        "rationale": "Slang for SELECT *"
    },
    {
        "query": "Remove John Doe from the database", 
        "expected_id": 503, 
        "expected_op": "DELETE_RECORD",
        "rationale": "Destructive action"
    },
    {
        "query": "What are the different types of product categories?", 
        "expected_id": 102, 
        "expected_op": "SELECT_DISTINCT",
        "rationale": "Implies DISTINCT values"
    }
]

# =========================================================================
# PYTEST EXECUTION
# =========================================================================

@pytest.mark.parametrize("case", TEST_CASES)
def test_semantic_intent_classification(case):
    """
    Runs each test case against the API and validates the Top 1 result.
    This is an INTEGRATION test (requires live Qdrant DB).
    """
    query = case["query"]
    expected_id = case["expected_id"]
    rationale = case["rationale"]

    print(f"\n🧪 Testing Query: '{query}'")

    # 1. Call the API
    response = client.post("/api/classify-intent", json={"query": query})
    
    # Check if API is alive
    assert response.status_code == 200, f"API crashed or returned error: {response.text}"
    
    data = response.json()
    
    # 2. Extract Top Match
    matches = data.get("matches", [])
    assert len(matches) > 0, "No matches returned from Vector DB"
    
    top_match = matches[0]
    
    # Helper for debugging if test fails
    actual_id = int(top_match["intent_id"])
    actual_op = top_match["allowed_operations"][0]
    confidence = top_match["confidence"]

    error_msg = (
        f"\n❌ FAIL: '{query}'"
        f"\n   Expected ID: {expected_id} ({case['expected_op']})"
        f"\n   Got ID:      {actual_id} ({actual_op})"
        f"\n   Confidence:  {confidence:.4f}"
        f"\n   Rationale:   {rationale}"
    )

    # 3. Validation Assertions
    # We verify the ID matches. Using string vs int conversion to be safe.
    assert actual_id == expected_id, error_msg

    # Optional: Warn if confidence is low, even if it passed
    if confidence < 0.75:
        print(f"   ⚠ WARNING: Match correct but low confidence ({confidence:.2f})")