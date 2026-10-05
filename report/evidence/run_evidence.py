"""Run error-hunting Cypher (LAB_GUIDE 8.4) against the current graph and dump query + rows."""
import os, sys
from dotenv import load_dotenv
sys.path.insert(0, os.getcwd())
load_dotenv(os.path.join(os.getcwd(), ".env"))
from src.graph import Neo4jGraph

QUERIES = {
    "count_nodes": "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY n DESC",
    "count_rels": "MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS n ORDER BY n DESC",
    "E1_case_without_crime": "MATCH (k:Case) WHERE NOT (k)-[:CHARGED_WITH]->() RETURN k.name AS case, k.doc_id AS doc_id ORDER BY doc_id",
    "E1_cases_per_doc": "MATCH (k:Case) RETURN k.doc_id AS doc_id, collect(k.name) AS cases ORDER BY doc_id",
    "E2_hoang_nato": "MATCH (p:Person)-[r:INVOLVED_IN]->(k:Case) WHERE p.name CONTAINS 'Tuấn' OR any(a IN p.aliases WHERE a CONTAINS 'Nato') OPTIONAL MATCH (k)-[:INVOLVES]->(s:Substance) OPTIONAL MATCH (k)-[:CHARGED_WITH]->(c:Crime) RETURN p.name AS person, p.aliases AS aliases, r.charge AS charge, k.name AS case, collect(DISTINCT s.name) AS substances, collect(DISTINCT c.name) AS crimes",
    "E2_article255_clause_substances": "MATCH (:Article {id:'Điều 255 BLHS'})-[:HAS_CLAUSE]->(cl:Clause) OPTIONAL MATCH (cl)-[:MENTIONS]->(s:Substance) RETURN cl.number AS clause, cl.penalty AS penalty, collect(s.name) AS substances ORDER BY clause",
    "E2_clauses_per_case_mdma_5_vien": "MATCH (k:Case)-[i:INVOLVES]->(s:Substance)<-[:MENTIONS]-(cl:Clause)<-[:HAS_CLAUSE]-(a:Article)-[:DEFINES]->(:Crime)<-[:CHARGED_WITH]-(k) RETURN k.name AS case, s.name AS substance, i.amount AS amount, a.id AS article, collect(cl.number) AS clauses_selected ORDER BY case",
    "E3_substances": "MATCH (s:Substance) OPTIONAL MATCH (k:Case)-[:INVOLVES]->(s) RETURN s.name AS substance, count(k) AS cases ORDER BY toLower(s.name)",
    "E3_cases": "MATCH (k:Case) RETURN k.name AS case, k.doc_id AS doc_id ORDER BY toLower(k.name)",
    "E3_persons": "MATCH (p:Person)-[r:INVOLVED_IN]->(k:Case) RETURN p.name AS person, p.aliases AS aliases, collect(k.name) AS cases ORDER BY toLower(p.name)",
    "E3_location": "MATCH (l:Location) OPTIONAL MATCH (k)-[:LOCATED_IN]->(l) RETURN l.name AS location, count(k) AS cases ORDER BY toLower(l.name)",
    "E5_mdma_cases": "MATCH (k:Case)-[r:INVOLVES]->(s:Substance {name:'MDMA'}) RETURN k.name AS case, r.amount AS amount, k.doc_id AS doc_id ORDER BY doc_id",
    "E6_empty_charge": "MATCH (p:Person)-[r:INVOLVED_IN]->(k) WHERE r.charge = '' RETURN p.name AS person, r.role AS role, r.sentence AS sentence, k.name AS case ORDER BY case",
}

g = Neo4jGraph(os.environ["NEO4J_URI"], os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
s = g.stats()
print(f"# Graph: {s['nodes']} nodes / {s['relationships']} rels\n")
for name, q in QUERIES.items():
    print(f"## {name}\n```cypher\n{q};\n```\n```")
    for row in g.run(q):
        print(" | ".join(f"{k}={v}" for k, v in row.items()))
    print("```\n")
g.close()
