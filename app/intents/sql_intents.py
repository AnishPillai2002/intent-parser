SQL_INTENTS = [
    # =========================================================================
    # 100 SERIES: BASIC READS & FORMATTING
    # =========================================================================
    {
        "id": 101,
        "operation": "SELECT_BASIC",
        "category": "READ",
        "complexity": 1,
        "sql_pattern": "SELECT * FROM table",
        "text": "Retrieve all rows or specific columns from a table without any conditions.",
        "keywords": ["show", "list", "get", "display", "retrieve", "fetch"],
        "examples": [
            "show all employees",
            "list every product in the inventory",
            "get all customer records",
            "display the transaction logs",
            "fetch all rows from the data"
        ],
        "paraphrases": [
            "dump the table",
            "return the full dataset",
            "show me everything in the table"
        ]
    },
    {
        "id": 102,
        "operation": "SELECT_DISTINCT",
        "category": "READ",
        "complexity": 2,
        "sql_pattern": "SELECT DISTINCT column FROM table",
        "text": "Retrieve unique values from a column, removing duplicates.",
        "keywords": ["distinct", "unique", "different", "types of"],
        "examples": [
            "show unique countries in the user list",
            "list the different product categories available",
            "what are the unique job titles?",
            "get distinct status codes from logs"
        ],
        "paraphrases": [
            "remove duplicates and show list",
            "find all unique entries",
            "deduplicate the results"
        ]
    },

    # =========================================================================
    # 110 SERIES: FILTERING & SORTING (ROW LEVEL)
    # =========================================================================
    {
        "id": 110,
        "operation": "SELECT_WHERE",
        "category": "READ",
        "complexity": 2,
        "sql_pattern": "SELECT * FROM table WHERE condition",
        "text": "Filter rows based on specific criteria or conditions.",
        "keywords": ["where", "filtered by", "condition", "only", "specific"],
        "examples": [
            "show employees who live in New York",
            "list orders with status 'shipped'",
            "find products that cost less than 50 dollars",
            "get tickets created after 2023-01-01"
        ],
        "paraphrases": [
            "search for records matching X",
            "restrict results to specific condition",
            "get only the rows where X is true"
        ]
    },
    {
        "id": 111,
        "operation": "SELECT_ORDER_BY",
        "category": "READ",
        "complexity": 2,
        "sql_pattern": "SELECT * FROM table ORDER BY column [ASC/DESC]",
        "text": "Retrieve rows sorted by one or more columns.",
        "keywords": ["sort", "order by", "arrange", "ascending", "descending", "alphabetical"],
        "examples": [
            "list customers sorted by name",
            "show transactions ordered by date descending",
            "arrange products by price",
            "sort the employee list by join date"
        ],
        "paraphrases": [
            "organize the data by column",
            "put the results in order",
            "rank the rows simply"
        ]
    },
    {
        "id": 112,
        "operation": "SELECT_TOP_N",
        "category": "READ",
        "complexity": 3,
        "sql_pattern": "SELECT * FROM table ORDER BY col [ASC/DESC] LIMIT N",
        "text": "Find the extreme values (highest/lowest/newest/oldest) by sorting and limiting.",
        "keywords": ["top", "bottom", "first", "latest", "cheapest", "most expensive", "highest", "lowest", "limit"],
        "examples": [
            "find the cheapest employee", 
            "show the top 5 highest paying jobs",
            "who are the 3 most recent signups?",
            "get the most expensive product",
            "list the bottom 10 performing students"
        ],
        "paraphrases": [
            "get the extreme values",
            "find the min or max records",
            "show the head or tail of the sorted list"
        ]
    },
     {
        "id": 113,
        "operation": "SELECT_FILTER_SORT_LIMIT",
        "category": "READ",
        "complexity": 3,
        "sql_pattern": "SELECT * FROM table WHERE condition ORDER BY col LIMIT N",
        "text": "Filter data, sort the remaining results, and take the top N rows.",
        "keywords": ["top", "most", "latest", "where", "filtered", "sorted"],
        "examples": [
            "show the 5 most recent active orders",
            "find the cheapest product in the 'Electronics' category",
            "who is the highest paid engineer?",
            "list the top 3 customers from Canada"
        ],
        "paraphrases": [
            "search, sort, and limit",
            "find best/worst within a specific category"
        ]
    },

    # =========================================================================
    # 200 SERIES: AGGREGATION & ANALYTICS
    # =========================================================================
    {
        "id": 201,
        "operation": "AGGREGATE_GLOBAL",
        "category": "ANALYTICS",
        "complexity": 2,
        "sql_pattern": "SELECT COUNT(*) / SUM(col) / AVG(col) FROM table",
        "text": "Calculate a single statistic (Count, Sum, Avg, Min, Max) for the entire dataset.",
        "keywords": ["total", "count", "average", "sum", "how many", "overall"],
        "examples": [
            "how many users are there?",
            "what is the total revenue?",
            "calculate the average salary of all staff",
            "count the total number of orders"
        ],
        "paraphrases": [
            "calculate a global metric",
            "compute statistics for the whole table"
        ]
    },
    {
        "id": 202,
        "operation": "AGGREGATE_FILTERED",
        "category": "ANALYTICS",
        "complexity": 3,
        "sql_pattern": "SELECT AGG(col) FROM table WHERE condition",
        "text": "Calculate a statistic for a specific filtered subset of data.",
        "keywords": ["total", "count", "average", "where", "only"],
        "examples": [
            "how many active users are there?",
            "sum of sales for last month",
            "what is the average age of managers?",
            "count orders from the USA"
        ],
        "paraphrases": [
            "metric calculation with a filter",
            "conditional aggregation"
        ]
    },
    {
        "id": 210,
        "operation": "GROUP_BY_BASIC",
        "category": "ANALYTICS",
        "complexity": 3,
        "sql_pattern": "SELECT category, AGG(col) FROM table GROUP BY category",
        "text": "Group rows by a specific column and calculate aggregates for each group.",
        "keywords": ["per", "by", "each", "group by", "breakdown"],
        "examples": [
            "show total sales per country",
            "count the number of employees by department",
            "average grade for each class",
            "breakdown of expenses by category"
        ],
        "paraphrases": [
            "segment the data",
            "aggregate data per group"
        ]
    },
    {
        "id": 211,
        "operation": "GROUP_BY_FILTERED",
        "category": "ANALYTICS",
        "complexity": 4,
        "sql_pattern": "SELECT cat, AGG(col) FROM table WHERE cond GROUP BY cat",
        "text": "Filter the raw data first, then group the remaining rows.",
        "keywords": ["where", "per", "by", "each", "filtered"],
        "examples": [
            "show total sales per region for the year 2023",
            "count active users per platform",
            "average ticket resolution time per agent for high priority tickets"
        ],
        "paraphrases": [
            "conditional grouping",
            "filter then segment"
        ]
    },
    {
        "id": 220,
        "operation": "GROUP_BY_HAVING",
        "category": "ANALYTICS",
        "complexity": 4,
        "sql_pattern": "SELECT cat, AGG(col) FROM table GROUP BY cat HAVING AGG(col) condition",
        "text": "Group data and then filter the groups based on the result of the aggregation.",
        "keywords": ["having", "more than", "greater than", "at least", "groups with"],
        "examples": [
            "show departments with more than 10 employees",
            "which countries have total sales over 1 million?",
            "list categories that have an average price less than 50",
            "find classes with at least 20 students"
        ],
        "paraphrases": [
            "filter the results of a grouping",
            "restrict groups by their aggregate value"
        ]
    },
    {
        "id": 230,
        "operation": "GROUP_BY_ORDERED",
        "category": "ANALYTICS",
        "complexity": 4,
        "sql_pattern": "SELECT cat, AGG(col) FROM table GROUP BY cat ORDER BY AGG(col) DESC",
        "text": "Group data, aggregate it, and then sort the results to find the top/bottom groups.",
        "keywords": ["rank", "highest", "lowest", "most", "per", "by"],
        "examples": [
            "which country has the highest total sales?",
            "rank departments by number of employees",
            "show the top 5 product categories by revenue",
            "list sales reps ordered by their total deal value"
        ],
        "paraphrases": [
            "sort the grouped results",
            "find the top performing segments"
        ]
    },

    # =========================================================================
    # 300 SERIES: JOINS & RELATIONAL
    # =========================================================================
    {
        "id": 301,
        "operation": "JOIN_BASIC",
        "category": "READ",
        "complexity": 3,
        "sql_pattern": "SELECT * FROM t1 JOIN t2 ON t1.id = t2.id",
        "text": "Retrieve data combined from two or more related tables.",
        "keywords": ["join", "combined with", "along with", "their", "related"],
        "examples": [
            "list employees and their department names",
            "show orders along with customer details",
            "get student names and the courses they are taking",
            "find products and their supplier information"
        ],
        "paraphrases": [
            "merge data from two tables",
            "connect related entities"
        ]
    },
    {
        "id": 302,
        "operation": "JOIN_AGGREGATE",
        "category": "ANALYTICS",
        "complexity": 4,
        "sql_pattern": "SELECT t1.name, COUNT(t2.id) FROM t1 JOIN t2 GROUP BY t1.name",
        "text": "Join two tables and perform aggregation across the relationship.",
        "keywords": ["per", "each", "count", "sum", "join", "related"],
        "examples": [
            "how many orders did each customer place?",
            "calculate total revenue per supplier",
            "count the number of students in each course",
            "average salary per department name"
        ],
        "paraphrases": [
            "cross-table aggregation",
            "summarize related data"
        ]
    },

    # =========================================================================
    # 400 SERIES: COMPLEX LOGIC
    # =========================================================================
    {
        "id": 401,
        "operation": "SUBQUERY_FILTER",
        "category": "READ",
        "complexity": 5,
        "sql_pattern": "SELECT * FROM table WHERE col IN (SELECT ...)",
        "text": "Filter data using a list of values derived from another query.",
        "keywords": ["who have", "that are in", "based on", "subquery"],
        "examples": [
            "show users who have placed an order in the last month",
            "find products that have never been sold",
            "list employees who belong to departments in New York"
        ],
        "paraphrases": [
            "nested filtering",
            "filter based on another table's result"
        ]
    },
    {
        "id": 402,
        "operation": "SUBQUERY_COMPARISON",
        "category": "ANALYTICS",
        "complexity": 5,
        "sql_pattern": "SELECT * FROM table WHERE col > (SELECT AVG(col) FROM table)",
        "text": "Compare individual rows against a global statistic (above average, below max, etc).",
        "keywords": ["above average", "below average", "higher than the mean", "outliers"],
        "examples": [
            "users with salary greater than the average",
            "products priced higher than the average category price",
            "orders that are larger than the maximum order from yesterday"
        ],
        "paraphrases": [
            "compare against the mean",
            "relative value search"
        ]
    },

    # =========================================================================
    # 500 SERIES: MUTATIONS
    # =========================================================================
    {
        "id": 501,
        "operation": "INSERT_RECORD",
        "category": "WRITE",
        "complexity": 2,
        "sql_pattern": "INSERT INTO table VALUES (...)",
        "text": "Add new records or rows to a database table.",
        "keywords": ["add", "insert", "create", "new", "register"],
        "examples": [
            "add a new user named John",
            "create a new order for client X",
            "insert a record into the logs",
            "register a new employee"
        ],
        "paraphrases": [
            "store a new entry",
            "append data to table"
        ]
    },
    {
        "id": 502,
        "operation": "UPDATE_RECORD",
        "category": "WRITE",
        "complexity": 3,
        "sql_pattern": "UPDATE table SET col=val WHERE condition",
        "text": "Modify existing data based on specific conditions.",
        "keywords": ["update", "change", "modify", "set", "correct"],
        "examples": [
            "update the status of order 123 to 'delivered'",
            "change Alice's email address",
            "modify the price of product X",
            "set all inactive users to archived"
        ],
        "paraphrases": [
            "edit existing records",
            "alter data values"
        ]
    },
    {
        "id": 503,
        "operation": "DELETE_RECORD",
        "category": "WRITE",
        "complexity": 3,
        "sql_pattern": "DELETE FROM table WHERE condition",
        "text": "Remove records from a table permanently.",
        "keywords": ["delete", "remove", "drop", "erase", "clear"],
        "examples": [
            "delete user 501",
            "remove all canceled orders",
            "erase logs older than 2020",
            "drop the record for product Y"
        ],
        "paraphrases": [
            "remove rows from database",
            "clean up specific data"
        ]
    }
]