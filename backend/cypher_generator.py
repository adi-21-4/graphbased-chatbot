# cypher_generator.py
import re
import subprocess
import json
from pathlib import Path

# -----------------
# Load few-shot examples from JSON
# -----------------
EXAMPLES_FILE = Path(__file__).parent / "examples.json"
with open(EXAMPLES_FILE, "r", encoding="utf-8") as f:
    EXAMPLES = json.load(f)

# -----------------
# Schema grounding
# -----------------
SCHEMA_HINT = """
Use only these labels:
- Scheme, SchemeBy, Department, Location, Beneficiary, Founder, Objective, Description, Tag

Use only these relationships:
- (s:Scheme)-[:IS_UNDER]->(sb:SchemeBy)
- (s:Scheme)-[:LIES_UNDER]->(d:Department)
- (s:Scheme)-[:HAS_LOCATION]->(sl:Location)
- (s:Scheme)-[:BENEFITS]->(b:Beneficiary)
- (s:Scheme)-[:FOUNDED_BY]->(f:Founder)
- (s:Scheme)-[:HAS_OBJECTIVE]->(o:Objective)
- (s:Scheme)-[:DETAILS]->(desc:Description)
- (s:Scheme)-[:HAS_TAG]->(t:Tag)

Use only these properties:
- s.name
- sb.name, d.name, sl.name, b.name, f.name, o.name, desc.text, t.name

Rules:
- Always normalize text matches with: toLower(field) CONTAINS toLower("keyword")
- Never use '=' or '=~' for text matches.
- Do not invent labels, relationships, or properties.
- Do not place relationship patterns inside WHERE clauses.
- Always include LIMIT (<=200).
- Output only a Cypher query, nothing else.
"""

# -----------------
# Prompt Builder
# -----------------
def build_ollama_prompt(question: str) -> str:
    examples_text = "\n".join(
        [f"Q: {ex['question']}\nA:\n{ex['cypher']}" for ex in EXAMPLES]
    )
    return f"""
You are a Cypher query generator for Neo4j.

Schema:
{SCHEMA_HINT}

Here are some examples:

{examples_text}

Now generate a Cypher query for:

Q: {question}
A:
"""

# -----------------
# Query Cleaning
# -----------------
def clean_cypher(raw: str) -> str:
    """Extract the Cypher query from Ollama output."""
    cypher = re.sub(r"^```[\w]*|```$", "", raw.strip(), flags=re.MULTILINE).strip()

    # Keep only first MATCH... onwards
    match = re.search(r"(MATCH|MERGE|WITH|UNWIND|RETURN|CALL).*", cypher, flags=re.I | re.S)
    if match:
        cypher = match.group(0).strip()

    return cypher

# -----------------
# Safety Validator
# -----------------
ILLEGAL_PATTERNS = [
    r":NAMED",
    r":RUNS",
    r":String",
    r"=~",      # disallow regex
    r"\s=\s",   # disallow equality for text
    r"WHERE.*-\[.*\]->",  # disallow relationship patterns inside WHERE
    r"WITH\s+'",  # disallow WITH just for string aliases
]

def looks_illegal(cypher: str) -> bool:
    for pat in ILLEGAL_PATTERNS:
        if re.search(pat, cypher, flags=re.IGNORECASE):
            return True
    return False

# -----------------
# Ensure Safe RETURN (OPTIONAL MATCH)
# -----------------
def ensure_safe_return(cypher: str) -> str:
    needed = []
    if "sb.name" in cypher and ":SchemeBy" not in cypher:
        needed.append("OPTIONAL MATCH (s)-[:IS_UNDER]->(sb:SchemeBy)")
    if "d.name" in cypher and ":Department" not in cypher:
        needed.append("OPTIONAL MATCH (s)-[:LIES_UNDER]->(d:Department)")
    if "sl.name" in cypher and ":Location" not in cypher:
        needed.append("OPTIONAL MATCH (s)-[:HAS_LOCATION]->(sl:Location)")
    if "b.name" in cypher and ":Beneficiary" not in cypher:
        needed.append("OPTIONAL MATCH (s)-[:BENEFITS]->(b:Beneficiary)")
    if "f.name" in cypher and ":Founder" not in cypher:
        needed.append("OPTIONAL MATCH (s)-[:FOUNDED_BY]->(f:Founder)")
    if "o.name" in cypher and ":Objective" not in cypher:
        needed.append("OPTIONAL MATCH (s)-[:HAS_OBJECTIVE]->(o:Objective)")
    if "desc.text" in cypher and ":Description" not in cypher:
        needed.append("OPTIONAL MATCH (s)-[:DETAILS]->(desc:Description)")
    if "t.name" in cypher and ":Tag" not in cypher:
        needed.append("OPTIONAL MATCH (s)-[:HAS_TAG]->(t:Tag)")

    if needed:
        parts = cypher.split("RETURN")
        cypher = parts[0].strip() + "\n" + "\n".join(needed) + "\nRETURN " + parts[1].strip()

    return cypher

# -----------------
# Post-processing: Count, Names, Objectives, Text
# -----------------
def adjust_return(question: str, cypher: str) -> str:
    q = question.lower()

    # Count queries
    if re.search(r"\b(number of|how many|count)\b", q):
        return re.sub(r"RETURN .*", "RETURN count(s) AS count\nLIMIT 50", cypher, flags=re.I|re.S)

    # Names only
    if "list" in q or "names" in q:
        return re.sub(r"RETURN .*", "RETURN s.name AS scheme\nLIMIT 200", cypher, flags=re.I|re.S)

    # Objective
    if "objective" in q:
        return re.sub(
            r"RETURN .*",
            "RETURN s.name AS scheme, o.name AS objective\nLIMIT 200",
            cypher,
            flags=re.I | re.S
        )

    # Text/description
    if "text" in q or "description" in q:
        return re.sub(
            r"RETURN .*",
            "RETURN s.name AS scheme, desc.text AS description\nLIMIT 200",
            cypher,
            flags=re.I|re.S
        )

    return cypher

# -----------------
# Clause Reordering
# -----------------
def reorder_where_clauses(cypher: str) -> str:
    """
    Ensure WHERE clauses always come after all MATCH/OPTIONAL MATCH statements.
    """
    lines = [line.strip() for line in cypher.splitlines() if line.strip()]

    match_lines = []
    where_lines = []
    return_lines = []
    other_lines = []

    for line in lines:
        if line.upper().startswith("MATCH") or line.upper().startswith("OPTIONAL MATCH"):
            match_lines.append(line)
        elif line.upper().startswith("WHERE"):
            where_lines.append(line)
        elif line.upper().startswith("RETURN") or line.upper().startswith("LIMIT"):
            return_lines.append(line)
        else:
            other_lines.append(line)

    # Reassemble in correct order
    new_query = "\n".join(match_lines + where_lines + other_lines + return_lines)
    return new_query

# -----------------
# Keyword Expansion for Tags + Name + Description
# -----------------
def expand_keyword_filters(cypher: str, question: str) -> str:
    """
    Ensure filters check tags, scheme name, and description together.
    """
    keywords = []
    for word in re.findall(r"\b\w+\b", question.lower()):
        if word in ["farmer", "student", "women", "girl", "tribal", "pension", "housing", "research", "fellowship"]:
            keywords.append(word)

    if not keywords:
        return cypher

    conditions = []
    for kw in keywords:
        conditions.append(f"toLower(t.name) CONTAINS toLower('{kw}')")
        conditions.append(f"toLower(s.name) CONTAINS toLower('{kw}')")
        conditions.append(f"toLower(desc.text) CONTAINS toLower('{kw}')")

    condition_block = " OR ".join(conditions)

    if "WHERE" in cypher:
        # already has a WHERE → append with AND
        cypher = re.sub(r"WHERE (.+)", f"WHERE (\\1) AND ({condition_block})", cypher, flags=re.I|re.S)
    else:
        # insert WHERE before RETURN
        cypher = re.sub(r"(RETURN)", f"WHERE {condition_block}\n\\1", cypher, flags=re.I|re.S)

    return cypher


# -----------------
# LLM Call
# -----------------
def generate_cypher_query(question: str, model: str = "mistral") -> str:
    prompt = build_ollama_prompt(question)

    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt.encode("utf-8"),
        capture_output=True,
    )
    raw_output = result.stdout.decode("utf-8").strip()

    cypher = clean_cypher(raw_output)
    cypher = ensure_safe_return(cypher)
    cypher = adjust_return(question, cypher)
    cypher = reorder_where_clauses(cypher)
    cypher = expand_keyword_filters(cypher, question)

    if looks_illegal(cypher):
        raise ValueError(f"Generated Cypher contains illegal patterns:\n{cypher}")

    return cypher
