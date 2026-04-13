# graph_query.py
from neo4j import GraphDatabase

# ==== CONFIG ====
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"

# ==== CONNECT ====
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))


def run_cypher_query(cypher: str):
    """
    Execute a Cypher query and return JSON-friendly results.
    Handles both count queries and property-based queries.
    """
    with driver.session() as session:
        result = session.run(cypher)
        records = list(result)

        if not records:
            return []

        # Handle count queries
        keys = records[0].keys()
        if any("count" in k.lower() for k in keys):
            return [{"count": records[0][0]}]

        # Otherwise return list of dicts with clean keys
        output = []
        for record in records:
            row = {}
            for key, val in record.items():
                if val is None:
                    continue
                # Clean up keys like "s.name" → "name"
                clean_key = key.split(".")[-1]
                row[clean_key] = val
            if row:
                output.append(row)

        return output


def close():
    driver.close()
