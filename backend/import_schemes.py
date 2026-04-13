from neo4j import GraphDatabase
import pandas as pd

# ==== CONFIG ====
CSV_FILE = "dataset.csv"   # your CSV file path
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"

# ==== CONNECT ====
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

# ==== CYPHER QUERY ====
def insert_scheme(tx, row):
    query = """
    MERGE (s:Scheme {name: $schemeName})
    MERGE (sb:SchemeBy {name: $schemeBy})
    MERGE (sl:Location {name: $schemeLocation})
    MERGE (fb:Founder {name: $foundedBy})
    MERGE (d:Department {name: $departmentName})
    MERGE (b:Beneficiary {name: $beneficiary})
    MERGE (o:Objective {name: $schemeObjective})
    MERGE (desc:Description {text: $description})
    MERGE (t:Tag {name: $tags})

    MERGE (s)-[:IS_UNDER]->(sb)
    MERGE (s)-[:HAS_LOCATION]->(sl)
    MERGE (s)-[:FOUNDED_BY]->(fb)
    MERGE (s)-[:LIES_UNDER]->(d)
    MERGE (s)-[:BENEFITS]->(b)
    MERGE (s)-[:HAS_OBJECTIVE]->(o)
    MERGE (s)-[:DETAILS]->(desc)
    MERGE (s)-[:HAS_TAG]->(t)
    MERGE (sb)-[:OF_LOCATION]->(sl)
    """
    tx.run(query, 
           schemeName=row["schemeName"],
           schemeBy=row["schemeBy"],
           schemeLocation=row["schemeLocation"],
           foundedBy=row["foundedBy"],
           departmentName=row["departmentName"],
           beneficiary=row["Beneficiary"],
           schemeObjective=row["schemeObjective"],
           description=row["description"],
           tags=row["tags"])

# ==== LOAD CSV ====
df = pd.read_csv(CSV_FILE)

with driver.session() as session:
    for _, row in df.iterrows():
        session.write_transaction(insert_scheme, row.to_dict())

driver.close()
print("✅ Data imported into Neo4j successfully!")
