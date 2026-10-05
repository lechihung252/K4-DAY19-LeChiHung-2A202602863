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
    "E3_substances": "MATCH (s:Substance) OPTIONAL MATCH (k:Case)-[:INVOLVES]->(s) RETURN s.name AS substance, count(k) AS cases ORDER BY toLower(substance)",
    "E3_cases": "MATCH (k:Case) RETURN k.name AS case, k.doc_id AS doc_id ORDER BY toLower(k.name)",
    "E3_persons": "MATCH (p:Person)-[r:INVOLVED_IN]->(k:Case) RETURN p.name AS person, p.aliases AS aliases, collect(k.name) AS cases ORDER BY toLower(p.name)",
    "E3_location": "MATCH (l:Location) OPTIONAL MATCH (k)-[:LOCATED_IN]->(l) RETURN l.name AS location, count(k) AS cases ORDER BY toLower(l.name)",
    "E5_mdma_cases": "MATCH (k:Case)-[r:INVOLVES]->(s:Substance {name:'MDMA'}) RETURN k.name AS case, r.amount AS amount, k.doc_id AS doc_id ORDER BY doc_id",
    "OWN_thresholds_250_mdma": "MATCH (a:Article {id:'Điều 250 BLHS'})-[:HAS_CLAUSE]->(cl:Clause)-[t:THRESHOLD]->(s:Substance {name:'MDMA'}) RETURN cl.number AS clause, t.point AS point, t.min_g AS min_g, t.max_g AS max_g, cl.penalty AS penalty ORDER BY clause",
    "OWN_clause_by_amount": "MATCH (k:Case)-[i:INVOLVES]->(s:Substance) WHERE i.grams IS NOT NULL MATCH (k)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(a:Article)-[:HAS_CLAUSE]->(cl:Clause)-[t:THRESHOLD]->(g:Substance) WHERE g.name = CASE WHEN EXISTS { (a)-[:HAS_CLAUSE]->()-[:THRESHOLD]->(s) } THEN s.name ELSE 'chất ma túy khác (thể rắn)' END AND t.min_g <= i.grams AND (t.max_g IS NULL OR i.grams < t.max_g) RETURN k.name AS case, s.name AS substance, i.amount AS amount, i.grams AS grams, a.id AS article, cl.number AS clause, t.point AS point ORDER BY case, article",
    "OWN_max_penalty_255": "MATCH (:Article {id:'Điều 255 BLHS'})-[:HAS_CLAUSE]->(cl:Clause) RETURN cl.number AS clause, cl.max_years AS max_years, cl.life AS life, cl.death AS death, cl.severity AS severity ORDER BY severity DESC",
    "OWN_substance_aliases": "MATCH (s:Substance) WHERE size(coalesce(s.aliases, [])) > 0 RETURN s.name AS substance, s.aliases AS aliases ORDER BY substance",
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
