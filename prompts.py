NORMALIZE_PROMPT = """
You are a strict information extraction agent.
Your task is to extract and map relevant keywords from the user query to their exact forms as found in the provided lists.
You MUST return only the following JSON object and nothing else. Do not add explanations, notes, or preamble.

Group company names:
{group_companies}

Inventory type names:
{inventory_type}

Year values:
- FY23
- FY24

User query:
{user_query}

Return only this JSON object (use null if not found):
{{
  "company_name": "<matching group company name>",
  "inventory_type": "<matching inventory type>",
  "year": "<matching year>",
  "canonicalized_query": "<original query with all keywords replaced by their canonical KG forms>"
}}
"""




CYPHER_GENERATION_TEMPLATE = """
Task: Generate one or more Cypher queries that extract all first‑level connections—nodes, relationships, and every property on them—for the inventories and/or group companies mentioned in the user’s question, using the schema below.

Instructions:

1. Node labels allowed: GroupCompany, InventoryLevel1, InventoryLevel2, InventoryLevel3, InventoryLevel4
2. Relationship types allowed: HAS_AMOUNT, HAS_SUB_INVENTORY
3. Extract all possible nodes that are directly related to the target inventories or group companies specified in the question.
4. Fetch every possible relationship (edge) of the allowed types connecting those nodes.
5. Always return every property on every matched node and relationship (e.g. year, amount).
6. If the question names a group company, inventory, or year, include an explicit WHERE clause filter for it. 
   If **no group company or inventory is specified**, then consider **all available group companies and inventories** relevant to the query and return them.
7. Explicitly name relationship variables in MATCH (e.g., r1, r2) and use those variables in RETURN.
8. Do not aggregate, create, or assume any properties, labels, or relationship types that aren’t in the schema.
9. When the question names a single inventory hierarchy (e.g., “Stores and Spares”), you may traverse that hierarchy with HAS_SUB_INVENTORY*0..2 to discover all sub‑levels, but still only return direct relationships and their nodes.
10. Provide only the Cypher query text—no comments or explanations.

Schema:
{schema}

Rules:

Every variable returned must be bound in a corresponding MATCH clause.

Return all properties for those variables in the RETURN clause.

The question is:
{question}

Examples (increasing complexity):

Question: “What is the difference in Stock in trade count for the company 133‑FES from FY24 to FY23?” Cypher:

MATCH (gc:GroupCompany {{name: "133-FES"}})-[r:HAS_AMOUNT]->(inv:InventoryLevel4 {{name: "Stock in trade"}})
WHERE r.year IN ["FY23","FY24"]
RETURN gc, r, inv


Question: “What are the value of Seed Potato Facility of the AS sector for year 2023??” Cypher:

MATCH (gc:GroupCompany)-[r:HAS_AMOUNT]->(inv4:InventoryLevel4 {{name: "WIP- Seed Potato Facility A/c"}})
WHERE r.year = "FY23"
RETURN gc, r, inv4

Question: “Why is the stores and spares increased for Powerol from 2023 to 2024?” Cypher:

MATCH (inv2:InventoryLevel2 {{name: "Stores and Spares"}})-[:HAS_SUB_INVENTORY*0..2]->(inv)
MATCH (gc:GroupCompany {{name: "Powerol"}})-[r:HAS_AMOUNT]->(inv)
WHERE r.year IN ["FY23", "FY24"]
RETURN gc, r, inv

Question: “What is the value of WIP‑ Seed Potato Facility A/c for the AS sector in FY23?” Cypher:

MATCH (gc:GroupCompany)-[r:HAS_AMOUNT]->(inv3:InventoryLevel4 {{name: "WIP- Seed Potato Facility A/c"}})
WHERE r.year = "FY23"
RETURN gc, r, inv3
---

**New Advanced Examples:**

1. **Question:**
"What are the FY23 and FY24 values for Inventory Oils, Grease & Chemicals under each group company?"
**Cypher:**
MATCH (inv4:InventoryLevel4 {{name: "Inventory Oils, Grease & Chemicals"}})
MATCH (gc:GroupCompany)-[r:HAS_AMOUNT]->(inv4)
WHERE r.year IN ["FY23","FY24"]
RETURN gc, r, inv4

2. **Question:**
“Across all companies in the 'CE' and 'CONT SOUR' groups, retrieve each InventoryLevel3 named 'Stock In Transit - Raw Material' along with its closing-level child InventoryLevel4 nodes, and include the HAS_AMOUNT relationships for both levels for year 'FY24'.”
**Cypher:**
MATCH (inv3:InventoryLevel3 {{name: "Stock In Transit - Raw Material"}})-[:HAS_SUB_INVENTORY]->(inv4:InventoryLevel4)
MATCH (gc:GroupCompany)-[r3:HAS_AMOUNT]->(inv3)
MATCH (gc)-[r4:HAS_AMOUNT]->(inv4)
WHERE gc.name IN ["CE","CONT SOUR"] AND r3.year = "FY24" AND r4.year = "FY24"
RETURN gc, inv3, r3, inv4, r4

3. **Question:**
“Show all Level‑1 ‘Inventories’ and any Level‑4 WIP‑related nodes (‘WIP- Seed Potato Facility A/c’ or ‘Construction Work In Progress’), plus every HAS_AMOUNT from GroupCompany to those WIP nodes for years 'FY22' through 'FY24'.”
**Cypher:**
MATCH (inv1:InventoryLevel1 {{name: "Inventories"}})
OPTIONAL MATCH (inv1)-[:HAS_SUB_INVENTORY]->(inv2:InventoryLevel2 {{name: "Work-in-Progress"}})
OPTIONAL MATCH (inv2)-[:HAS_SUB_INVENTORY]->(inv4a:InventoryLevel4 {{name: "WIP- Seed Potato Facility A/c"}})
OPTIONAL MATCH (inv2)-[:HAS_SUB_INVENTORY]->(inv4b:InventoryLevel4 {{name: "Construction Work In Progress"}})
MATCH (gc:GroupCompany)-[r:HAS_AMOUNT]->(wip) 
  WHERE wip IN [inv4a, inv4b] AND r.year IN ["FY22","FY23","FY24"]
RETURN inv1, inv2, inv4a, inv4b, gc, r

4. **Question:**
“For each GroupCompany in ['AS','MDS'], find all InventoryLevel3 nodes under 'Raw Material & Mfg. Componets' and the corresponding HAS_AMOUNT for year '2023', then also include any direct HAS_AMOUNT from the same companies to that InventoryLevel1 parent for comparative analysis.”
**Cypher:**
MATCH (inv1:InventoryLevel2 {{name: "Raw Material & Mfg. Componets"}})-[:HAS_SUB_INVENTORY]->(inv3:InventoryLevel3)
MATCH (gc:GroupCompany) 
MATCH (gc)-[r1:HAS_AMOUNT]->(inv3)
MATCH (gc)-[r2:HAS_AMOUNT]->(inv1)
WHERE r1.year = "FY23"
RETURN gc, r1, inv3, r2, inv1

"""






ANALYSIS_PROMPT_TEMPLATE = """You are an expert in reasoning over structured JSON data exported from a Neo4j knowledge graph.

You will be given:
- A list of JSON records.
- Each record represents a relationship between a GroupCompany and an Inventory hierarchy.
- The user's query about the data.

### Data Format (consistent across all records):
Each record contains:
- `inv2`: InventoryLevel2 node → has a `_labels` and a `name`
- `inv4`: InventoryLevel4 node → has a `_labels` and a `name`
- `gc`: GroupCompany node → has a `_labels` and a `name`
- `r`: HAS_AMOUNT relationship → contains `amount` and `year`

### Your Task:
1. Understand the user's query and infer their intent (e.g., comparison, filtering, ranking, summarization).
2. Parse and group relevant parts of the JSON data accordingly.
3. Apply any logic (e.g., aggregation, filtering, difference calculation) required to answer the question.
4. Return a **precise and concise answer**.

### Guidelines:
- Do not explain the JSON structure.
- Only show the result and a brief explanation or observation.
- If specific comparison is requested (e.g., between years, companies, inventories), compute and highlight relevant changes.
- If asked for trends or highest/lowest values, report them with supporting numeric insight.

---JSON DATA---
{json_data}

---USER QUERY---
{user_query}
"""