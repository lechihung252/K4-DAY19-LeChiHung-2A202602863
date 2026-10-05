"""Knowledge Graph (Neo4j) + GraphRAG over two drug-topic knowledge bases.

Contract (fixed — bench_kg.py and the tests rely on it):
    link_entity(name, known)                       -> one of `known` or None          (TODO KG-1)
    build_graph(graph, law_docs, news_docs, llm_fn)   load both KBs into Neo4j      (TODO KG-2)
        every node created from ONE document carries the property `doc_id`
    Neo4jGraph.context(question, doc_ids)         -> list[str] facts               (TODO KG-3)
    GraphRAGAgent.answer(question, top_k)         -> str                           (TODO KG-4)

Own ontology (used by default, see report/ONTOLOGY.md) — the suggested one below plus:
    (:Clause {..., min_years, max_years, life, death, severity})          structured penalty
    (:Clause)-[:THRESHOLD {point, min_g, max_g, text}]->(:Substance)      quantity range of a point
    (:Clause)-[:MENTIONS]->(:Substance)                                   only when the point has no range
    (:Substance {name, aliases})                                          canonical name + street names
    (:Case)-[:INVOLVES {amount, grams}]->(:Substance)                     amount normalized to grams
Set KG_ONTOLOGY=suggested to rebuild / query the suggested ontology instead (baseline benchmark).

Suggested ontology (HINT; Crime is the bridge between the law KB and the news KB):

    (:Article {id, title, law, doc_id})-[:DEFINES]->(:Crime {name})
    (:Article)-[:HAS_CLAUSE]->(:Clause {id, number, penalty, text})-[:MENTIONS]->(:Substance {name})
    (:Case {name, summary, date, doc_id})-[:CHARGED_WITH]->(:Crime)
    (:Case)-[:INVOLVES {amount}]->(:Substance)
    (:Case)-[:LOCATED_IN]->(:Location {name})
    (:Person {name, aliases})-[:INVOLVED_IN {role, sentence, charge}]->(:Case)
"""

from __future__ import annotations

import difflib
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from .models import Document
from .store import EmbeddingStore

# Canonical substance names: the ones BLHS Chương XX lists, plus common ones in Vietnamese news.
SUBSTANCES = ["Heroine", "Cocaine", "Methamphetamine", "Amphetamine", "MDMA", "XLR-11", "Ketamine",
              "cần sa", "thuốc phiện", "côca"]
CLAUSE_START = re.compile(r"^(\d+)\.\s", re.MULTILINE)
FOOTNOTE = re.compile(r"\[\d+\]")

def load_markdown_docs(folder: str | Path) -> list[Document]:
    """Read crawler output (.md with a flat `key: "value"` front matter) into Documents."""
    docs = []
    for path in sorted(Path(folder).glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        _, front, body = raw.split("---", 2)
        metadata = {k: json.loads(v) for k, v in re.findall(r'^(\w+): (".*")$', front, re.MULTILINE)}
        docs.append(Document(id=metadata.get("doc_id", path.stem), content=body.strip(), metadata=metadata))
    return docs

def normalize_crime(name: str) -> str:
    """'Tội Mua bán trái phép chất ma túy' -> 'mua bán trái phép chất ma túy'."""
    name = re.sub(r"\s+", " ", name.strip().strip("\"'“”").lower())
    return name.removeprefix("tội ").strip()

def link_entity(name: str, known: list[str], normalize: Callable[[str], str] = normalize_crime) -> str | None:
    """Map a free-text mention (e.g. a charge written by a journalist) onto one canonical name in `known`."""
    target = normalize(name or "")
    if not target:
        return None
    by_normalized = {normalize(k): k for k in known}
    if target in by_normalized:
        return by_normalized[target]
    close = difflib.get_close_matches(target, list(by_normalized), n=1, cutoff=0.8)
    return by_normalized[close[0]] if close else None

def find_substances(text: str) -> list[str]:
    lowered = text.lower()
    return [name for name in SUBSTANCES if name.lower() in lowered]

# ----------------------------------------------------------------------------------------------
# HINT — suggested ontology: extraction helpers
# ----------------------------------------------------------------------------------------------

def parse_law_article(doc: Document) -> dict[str, Any]:
    """Deterministic (regex) extraction for one 'Điều' — law text is regular enough to skip the LLM."""
    article_id = doc.metadata["article"]                       # "Điều 251 BLHS"
    title = doc.metadata["title"].split(". ", 1)[-1]           # "Tội mua bán trái phép chất ma túy"
    body = FOOTNOTE.sub("", doc.content)
    starts = list(CLAUSE_START.finditer(body))
    clauses = []
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(body)
        text = body[start.start():end].strip()
        first_line = text.splitlines()[0]
        penalty = re.search(r"\bbị ((?:phạt|tù|cảnh cáo).+?)(?::|$)", first_line)
        clauses.append({
            "id": f"{article_id} khoản {start.group(1)}",
            "number": int(start.group(1)),
            "penalty": penalty.group(1).rstrip(".") if penalty else "",
            "text": text,
            "substances": find_substances(text),
        })
    return {
        "id": article_id,
        "law": doc.metadata.get("law", ""),
        "title": title,
        "doc_id": doc.id,
        "crime": normalize_crime(title) if title.startswith("Tội ") else None,
        "clauses": clauses,
    }

NEWS_EXTRACTION_PROMPT = """Bạn trích xuất knowledge graph từ một bài báo tiếng Việt về ma túy.
Chỉ dùng thông tin có trong bài. Trả về JSON đúng dạng:
{{"cases": [{{
  "name": "tên ngắn của vụ việc, ví dụ: Vụ mua bán 36kg ma túy tại TP.HCM",
  "summary": "1-2 câu tóm tắt",
  "date": "ngày xảy ra/xét xử nếu có, dạng YYYY-MM-DD hoặc chuỗi rỗng",
  "location": "tỉnh/thành phố, chuỗi rỗng nếu không rõ",
  "charges": ["tội danh, BẮT BUỘC chọn đúng nguyên văn từ DANH SÁCH TỘI DANH"],
  "substances": [{{"name": "tên chất, dùng tên chuẩn trong DANH SÁCH CHẤT nếu khớp", "amount": "khối lượng nếu có"}}],
  "people": [{{"name": "họ tên", "aliases": ["biệt danh"], "role": "bị cáo|bị can|nghi phạm|người liên quan|cán bộ",
               "charge": "tội danh của người này (từ DANH SÁCH TỘI DANH) hoặc chuỗi rỗng",
               "sentence": "mức án nếu có, ví dụ: tử hình, 8 năm tù"}}]
}}]}}
Bài không nói về vụ việc cụ thể (tuyên truyền, hội nghị...) thì trả về {{"cases": []}}.

DANH SÁCH TỘI DANH: {crimes}
DANH SÁCH CHẤT: {substances}

Tiêu đề: {title}
Nội dung:
{content}"""

def extract_news_cases(doc: Document, llm_fn: Callable[[str], str], known_crimes: list[str]) -> list[dict]:
    """LLM extraction for one news article; charges are re-linked to law-KB crimes in code."""
    prompt = NEWS_EXTRACTION_PROMPT.format(
        crimes="; ".join(known_crimes), substances=", ".join(SUBSTANCES),
        title=doc.metadata.get("title", ""), content=doc.content[:12000],
    )
    try:
        cases = json.loads(llm_fn(prompt)).get("cases", [])
    except (json.JSONDecodeError, AttributeError):
        return []
    for case in cases:
        case["charges"] = sorted({c for c in (link_entity(x, known_crimes) for x in case.get("charges", [])) if c})
        for person in case.get("people", []):
            person["charge"] = link_entity(person.get("charge") or "", known_crimes) or ""
    return cases

# ----------------------------------------------------------------------------------------------
# Own ontology (report/ONTOLOGY.md): quantity thresholds, structured penalties, canonical substances
# ----------------------------------------------------------------------------------------------

# Street names / spellings used by the news KB -> the canonical name used by the law KB.
SUBSTANCE_ALIASES = {
    "MDMA": ["thuốc lắc", "ecstasy"],
    "Methamphetamine": ["ma túy đá", "ma tuý đá", "hồng phiến"],
    "Ketamine": ["ketamin", "ke"],
    "Heroine": ["heroin", "hêrôin"],
    "Cocaine": ["cocain"],
    "cần sa": ["marijuana", "bồ đà"],
}
# Too vague to be a substance: as a node they would tie unrelated cases together.
GENERIC_SUBSTANCES = {"ma túy", "ma tuý", "chất ma túy", "chất ma tuý", "ma túy tổng hợp", "ma tuý tổng hợp",
                      "không rõ", "chất cấm"}
OTHER_SOLID = "chất ma túy khác (thể rắn)"   # BLHS: "Các chất ma túy khác ở thể rắn" (e.g. Ketamine)

UNIT_GRAMS = {"kilôgam": 1000.0, "kilogram": 1000.0, "kg": 1000.0, "gam": 1.0, "gram": 1.0, "g": 1.0}
MASS = re.compile(r"(\d[\d.,]*)\s*(kilôgam|kilogram|kg|gam|gram|g)(?![a-zà-ỹ])", re.IGNORECASE)
POINT = re.compile(r"^([a-zđ])\) (.+)$", re.MULTILINE)
RANGE = re.compile(r"từ (\d[\d.,]*) (gam|kilôgam) đến dưới (\d[\d.,]*) (gam|kilôgam)")
AT_LEAST = re.compile(r"(\d[\d.,]*) (gam|kilôgam) trở lên")

def to_number(text: str) -> float:
    """'0,686' -> 0.686, '9.6' -> 9.6, '3.000' -> 3000 (dot as thousands separator)."""
    text = text.rstrip(".,")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", text):
        return float(text.replace(".", ""))
    return float(text.replace(",", "."))

def parse_grams(amount: Any) -> float | None:
    """'hơn 9,6kg' -> 9600.0; '5 viên', 'nửa chỉ', '' -> None (no mass, no threshold can be applied)."""
    match = MASS.search(str(amount or ""))
    return to_number(match.group(1)) * UNIT_GRAMS[match.group(2).lower()] if match else None

def parse_penalty(penalty: str) -> dict[str, Any]:
    """'phạt tù 20 năm, tù chung thân hoặc tử hình' -> min/max years, life, death, severity (for ranking)."""
    prison = penalty.split("tù", 1)[1] if re.search(r"\btù\b", penalty) else ""
    years = [int(n) / (12 if unit == "tháng" else 1) for n, unit in re.findall(r"(\d+) (năm|tháng)", prison)]
    life, death = "chung thân" in prison, "tử hình" in prison
    max_years = max(years) if years else None
    return {"min_years": min(years) if years else None, "max_years": max_years, "life": life, "death": death,
            "severity": 30 if death else 25 if life else (max_years or 0)}

def parse_thresholds(clause_text: str) -> list[dict[str, Any]]:
    """One row per (point, substance) whose quantity range the point defines, in grams (max_g None = no cap)."""
    rows = []
    for point, line in POINT.findall(clause_text):
        if match := RANGE.search(line):
            low = to_number(match[1]) * UNIT_GRAMS[match[2]]
            high = to_number(match[3]) * UNIT_GRAMS[match[4]]
        elif match := AT_LEAST.search(line):
            low, high = to_number(match[1]) * UNIT_GRAMS[match[2]], None
        else:
            continue
        substances = find_substances(line) or ([OTHER_SOLID] if "thể rắn" in line else [])
        rows += [{"point": point, "substance": s, "min_g": low, "max_g": high, "text": line.rstrip(";.")}
                 for s in substances]
    return rows

def parse_law_article_detailed(doc: Document) -> dict[str, Any]:
    """parse_law_article + per-clause structured penalty, THRESHOLD rows, and threshold-free MENTIONS."""
    article = parse_law_article(doc)
    for clause in article["clauses"]:
        clause.update(parse_penalty(clause["penalty"]))
        clause["thresholds"] = parse_thresholds(clause["text"])
        with_range = {t["substance"] for t in clause["thresholds"]}
        clause["mentions"] = [s for s in clause.pop("substances") if s not in with_range]
    return article

def canonical_substance(name: str) -> str | None:
    """'thuốc lắc' -> 'MDMA', 'ketamine' -> 'Ketamine', 'ma túy' -> None, 'Etomidate' -> 'etomidate'."""
    key = re.sub(r"\s+", " ", (name or "").strip().lower())
    if not key or key in GENERIC_SUBSTANCES:
        return None
    for canonical, aliases in SUBSTANCE_ALIASES.items():
        if key in aliases:
            return canonical
    return link_entity(key, SUBSTANCES, normalize=str.lower) or key

def canonicalize_substances(case: dict) -> dict:
    """Map every substance of an extracted case to its canonical name and add `grams`; merge duplicates."""
    merged: dict[str, dict] = {}
    for item in case.get("substances", []):
        name = canonical_substance(item.get("name", ""))
        if not name:
            continue
        amount, grams = str(item.get("amount") or ""), parse_grams(item.get("amount"))
        if name in merged:
            amount = "; ".join(a for a in (merged[name]["amount"], amount) if a)
            grams = max((g for g in (merged[name]["grams"], grams) if g is not None), default=None)
        merged[name] = {"name": name, "amount": amount, "grams": grams}
    case["substances"] = list(merged.values())
    return case

# ----------------------------------------------------------------------------------------------
# Neo4j
# ----------------------------------------------------------------------------------------------

class Neo4jGraph:
    """Thin wrapper over the official neo4j driver."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        from neo4j import GraphDatabase

        self.driver = GraphDatabase.driver(uri, auth=(user, password), notifications_min_severity="OFF")
        self.driver.verify_connectivity()

    def close(self) -> None:
        self.driver.close()

    def run(self, cypher: str, **params: Any) -> list[dict]:
        records, _, _ = self.driver.execute_query(cypher, params)
        return [record.data() for record in records]

    def reset(self) -> None:
        """Delete every node, relationship and constraint (bench_kg.py calls this before build_graph)."""
        self.run("MATCH (n) DETACH DELETE n")
        for row in self.run("SHOW CONSTRAINTS YIELD name RETURN name"):
            self.run(f"DROP CONSTRAINT `{row['name']}` IF EXISTS")

    def stats(self) -> dict[str, int]:
        nodes = self.run("MATCH (n) RETURN count(n) AS n")[0]["n"]
        rels = self.run("MATCH ()-[r]->() RETURN count(r) AS n")[0]["n"]
        return {"nodes": nodes, "relationships": rels}

    def seed_facts(self, question: str, doc_ids: list[str], skip_labels: tuple[str, ...] = (),
                   limit: int = 60) -> tuple[list[str], list[str]]:
        """Ontology-independent first step: seed nodes + their 1-hop edges as text facts.

        Seeds = nodes whose `doc_id` is in doc_ids, or whose `name`/`aliases` appear in the question.
        Returns (seed elementIds, facts). Nodes with a label in skip_labels are left out of the facts.
        """
        seeds = self.run(
            """
            MATCH (n)
            WHERE n.doc_id IN $doc_ids
               OR (n.name IS :: STRING AND size(n.name) >= 3 AND toLower($q) CONTAINS toLower(n.name))
               OR any(a IN coalesce(n.aliases, []) WHERE size(a) >= 3 AND toLower($q) CONTAINS toLower(a))
            RETURN elementId(n) AS id
            """,
            q=question, doc_ids=doc_ids,
        )
        seed_ids = [row["id"] for row in seeds]
        edges = self.run(
            """
            MATCH (s)-[r]-(m)
            WHERE elementId(s) IN $ids
              AND none(l IN labels(s) + labels(m) WHERE l IN $skip)
            WITH DISTINCT r LIMIT $limit
            WITH startNode(r) AS a, r, endNode(r) AS b
            RETURN labels(a)[0] AS a_label, coalesce(a.name, a.id) AS a_name, type(r) AS rel,
                   properties(r) AS props, labels(b)[0] AS b_label, coalesce(b.name, b.id) AS b_name
            """,
            ids=seed_ids, skip=list(skip_labels), limit=limit,
        )
        facts = []
        for e in edges:
            props = ", ".join(f"{k}: {v}" for k, v in e["props"].items() if v)
            facts.append(f"({e['a_label']}: {e['a_name']}) -[{e['rel']}{' {' + props + '}' if props else ''}]-> "
                         f"({e['b_label']}: {e['b_name']})")
        return seed_ids, facts

    # ---------------------------------------------------------------- HINT — suggested ontology: writes

    def suggested_constraints(self) -> None:
        for label, key in [("Article", "id"), ("Clause", "id"), ("Crime", "name"), ("Case", "name"),
                           ("Substance", "name"), ("Person", "name"), ("Location", "name")]:
            self.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.{key} IS UNIQUE")

    def add_law_article(self, article: dict) -> None:
        self.run(
            """
            MERGE (a:Article {id: $id}) SET a.title = $title, a.law = $law, a.doc_id = $doc_id
            FOREACH (crime IN CASE WHEN $crime IS NULL THEN [] ELSE [$crime] END |
                MERGE (c:Crime {name: crime}) MERGE (a)-[:DEFINES]->(c))
            WITH a
            UNWIND $clauses AS clause
            MERGE (cl:Clause {id: clause.id})
              SET cl.number = clause.number, cl.penalty = clause.penalty, cl.text = clause.text, cl.doc_id = $doc_id
            MERGE (a)-[:HAS_CLAUSE]->(cl)
            FOREACH (s IN clause.substances | MERGE (sub:Substance {name: s}) MERGE (cl)-[:MENTIONS]->(sub))
            """,
            **article,
        )

    def add_news_case(self, case: dict, doc: Document) -> None:
        self.run(
            """
            MERGE (k:Case {name: $name})
              SET k.summary = $summary, k.date = $date, k.doc_id = $doc_id, k.source_title = $title
            FOREACH (loc IN CASE WHEN $location = '' THEN [] ELSE [$location] END |
                MERGE (l:Location {name: loc}) MERGE (k)-[:LOCATED_IN]->(l))
            FOREACH (crime IN $charges | MERGE (c:Crime {name: crime}) MERGE (k)-[:CHARGED_WITH]->(c))
            FOREACH (s IN $substances | MERGE (sub:Substance {name: s.name}) MERGE (k)-[r:INVOLVES]->(sub)
                SET r.amount = s.amount)
            FOREACH (p IN $people | MERGE (person:Person {name: p.name})
                SET person.aliases = coalesce(p.aliases, [])
                MERGE (person)-[r:INVOLVED_IN]->(k) SET r.role = p.role, r.charge = p.charge, r.sentence = p.sentence)
            """,
            name=case.get("name") or doc.metadata.get("title", doc.id),
            summary=case.get("summary", ""), date=case.get("date", ""), location=case.get("location", ""),
            charges=case.get("charges", []), people=[p for p in case.get("people", []) if p.get("name")],
            substances=[s for s in case.get("substances", []) if s.get("name")],
            doc_id=doc.id, title=doc.metadata.get("title", ""),
        )

    # ---------------------------------------------------------------- own ontology: writes

    def add_article_detailed(self, article: dict) -> None:
        self.run(
            """
            MERGE (a:Article {id: $id}) SET a.title = $title, a.law = $law, a.doc_id = $doc_id
            FOREACH (crime IN CASE WHEN $crime IS NULL THEN [] ELSE [$crime] END |
                MERGE (c:Crime {name: crime}) MERGE (a)-[:DEFINES]->(c))
            WITH a
            UNWIND $clauses AS clause
            MERGE (cl:Clause {id: clause.id})
              SET cl.number = clause.number, cl.penalty = clause.penalty, cl.text = clause.text, cl.doc_id = $doc_id,
                  cl.min_years = clause.min_years, cl.max_years = clause.max_years, cl.life = clause.life,
                  cl.death = clause.death, cl.severity = clause.severity
            MERGE (a)-[:HAS_CLAUSE]->(cl)
            FOREACH (t IN clause.thresholds | MERGE (s:Substance {name: t.substance})
                MERGE (cl)-[r:THRESHOLD {point: t.point}]->(s) SET r.min_g = t.min_g, r.max_g = t.max_g, r.text = t.text)
            FOREACH (s IN clause.mentions | MERGE (sub:Substance {name: s}) MERGE (cl)-[:MENTIONS]->(sub))
            """,
            **article,
        )

    def add_substance_aliases(self) -> None:
        self.run("UNWIND $rows AS row MERGE (s:Substance {name: row.name}) SET s.aliases = row.aliases",
                 rows=[{"name": name, "aliases": aliases} for name, aliases in SUBSTANCE_ALIASES.items()])

    def add_case_detailed(self, case: dict, doc: Document) -> None:
        """add_news_case, but substances are canonical and INVOLVES carries `grams` for threshold matching."""
        self.run(
            """
            MERGE (k:Case {name: $name})
              SET k.summary = $summary, k.date = $date, k.doc_id = $doc_id, k.source_title = $title
            FOREACH (loc IN CASE WHEN $location = '' THEN [] ELSE [$location] END |
                MERGE (l:Location {name: loc}) MERGE (k)-[:LOCATED_IN]->(l))
            FOREACH (crime IN $charges | MERGE (c:Crime {name: crime}) MERGE (k)-[:CHARGED_WITH]->(c))
            FOREACH (s IN $substances | MERGE (sub:Substance {name: s.name}) MERGE (k)-[r:INVOLVES]->(sub)
                SET r.amount = s.amount, r.grams = s.grams)
            FOREACH (p IN $people | MERGE (person:Person {name: p.name})
                SET person.aliases = coalesce(p.aliases, [])
                MERGE (person)-[r:INVOLVED_IN]->(k) SET r.role = p.role, r.charge = p.charge, r.sentence = p.sentence)
            """,
            name=case.get("name") or doc.metadata.get("title", doc.id),
            summary=case.get("summary", ""), date=case.get("date", ""), location=case.get("location", ""),
            charges=case.get("charges", []), people=[p for p in case.get("people", []) if p.get("name")],
            substances=case.get("substances", []), doc_id=doc.id, title=doc.metadata.get("title", ""),
        )

    # ---------------------------------------------------------------- KG-3

    def context(self, question: str, doc_ids: list[str], max_facts: int = 60) -> list[str]:
        """Graph facts: seeds + 1 hop, cases, every case's legal basis picked by quantity threshold."""
        if os.getenv("KG_ONTOLOGY") == "suggested":
            return self.suggested_context(question, doc_ids, max_facts)
        seed_ids, seed_facts = self.seed_facts(question, doc_ids)
        # Shared hub nodes (substance, location, crime) do not pull every case they touch into the legal
        # expansion; cases sharing a substance named in the question are listed by the aggregation fact below.
        cases = self.run(
            """
            MATCH (k:Case)
            WHERE elementId(k) IN $ids OR EXISTS {
                MATCH (s)--(k) WHERE elementId(s) IN $ids AND NOT (s:Substance OR s:Location OR s:Crime) }
            OPTIONAL MATCH (k)-[i:INVOLVES]->(s:Substance)
            OPTIONAL MATCH (k)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(a:Article)
            RETURN elementId(k) AS id, k.name AS name, k.summary AS summary, collect(DISTINCT a.id) AS articles,
                   collect(DISTINCT {name: s.name, amount: i.amount, grams: i.grams}) AS substances
            """,
            ids=seed_ids,
        )
        facts = [f"Vụ việc '{c['name']}': {c['summary']}" for c in cases]

        # Aggregation: every case that involves a substance named in the question (canonical name or alias).
        for row in self.run(
            """
            MATCH (s:Substance)<-[i:INVOLVES]-(k:Case)
            WHERE toLower($q) CONTAINS toLower(s.name)
               OR any(a IN coalesce(s.aliases, []) WHERE size(a) >= 3 AND toLower($q) CONTAINS toLower(a))
            OPTIONAL MATCH (p:Person)-[r:INVOLVED_IN]->(k) WHERE r.role IN ['bị cáo', 'bị can', 'nghi phạm']
            WITH s, k, i, collect(p.name)[..3] AS people
            RETURN s.name AS substance,
                   collect(k.name + CASE WHEN i.amount <> '' THEN ' (' + i.amount + ')' ELSE '' END
                           + CASE WHEN size(people) > 0 THEN ' - ' + reduce(t = head(people), x IN tail(people) | t + ', ' + x) ELSE '' END) AS cases
            """,
            q=question,
        ):
            facts.append(f"Các vụ việc trong graph có {row['substance']}: " + "; ".join(row["cases"]))

        # Bridge: case -> crime -> article -> the clauses that apply; plus articles cited in the question.
        numbers = re.findall(r"[Đđ]iều (\d+)", question)
        cited = [r["id"] for r in self.run(
            "MATCH (a:Article) WHERE any(n IN $numbers WHERE a.id STARTS WITH 'Điều ' + n + ' ') RETURN a.id AS id",
            numbers=numbers)]
        article_ids = sorted({a for c in cases for a in c["articles"]} | set(cited))
        clauses = self.run(
            """
            MATCH (a:Article)-[:HAS_CLAUSE]->(cl:Clause) WHERE a.id IN $ids
            OPTIONAL MATCH (cl)-[t:THRESHOLD]->(s:Substance)
            RETURN a.id AS article, a.title AS title, cl.number AS number, cl.text AS text, cl.severity AS severity,
                   [x IN collect({substance: s.name, point: t.point, min_g: t.min_g, max_g: t.max_g, text: t.text})
                    WHERE x.substance IS NOT NULL] AS thresholds
            """,
            ids=article_ids,
        )
        by_article: dict[str, list[dict]] = {}
        for cl in clauses:
            by_article.setdefault(cl["article"], []).append(cl)

        picked: dict[tuple[str, int], dict] = {}   # (article, clause) -> {"reasons": [...], "points": [...]}

        def pick(cl: dict, reason: str, point: str | None = None) -> None:
            entry = picked.setdefault((cl["article"], cl["number"]), {"clause": cl, "reasons": [], "points": []})
            if reason not in entry["reasons"]:
                entry["reasons"].append(reason)
            if point and point not in entry["points"]:
                entry["points"].append(point)

        def frame(article: str) -> None:
            rows = by_article.get(article, [])
            for cl in rows:
                if cl["number"] == 1:
                    pick(cl, "khung cơ bản")
            if rows and (top := max(rows, key=lambda r: r["severity"] or 0))["severity"]:
                pick(top, "khung cao nhất của điều")

        for article in cited:
            frame(article)
        for case in cases:
            unknown = [f"{s['name']} ({s['amount'] or 'không rõ'})" for s in case["substances"]
                       if s["name"] and s["grams"] is None]
            if unknown and case["articles"]:
                facts.append(f"Vụ '{case['name']}': chưa quy đổi được ra gam khối lượng {', '.join(unknown)}, "
                             "nên chưa xác định được khoản theo khối lượng cho các chất này")
            for article in case["articles"]:
                frame(article)
                rows = by_article.get(article, [])
                named = {t["substance"] for cl in rows for t in cl["thresholds"]}
                for sub in case["substances"]:
                    if not sub["name"] or sub["grams"] is None:
                        continue
                    group = sub["name"] if sub["name"] in named else OTHER_SOLID
                    for cl in rows:
                        for t in cl["thresholds"]:
                            if t["substance"] == group and t["min_g"] <= sub["grams"] and (
                                    t["max_g"] is None or sub["grams"] < t["max_g"]):
                                pick(cl, f"áp dụng cho vụ '{case['name']}': {sub['name']} {sub['amount']} "
                                         f"≈ {sub['grams']:g} gam", f"điểm {t['point']}) {t['text']}")

        for (article, number), entry in sorted(picked.items()):
            cl = entry["clause"]
            fact = f"[{article} - {cl['title']}] khoản {number} ({'; '.join(entry['reasons'])}): {cl['text'].splitlines()[0]}"
            facts.append(fact + "".join(f" | {p}" for p in entry["points"]))
        return list(dict.fromkeys(facts + seed_facts))[:max_facts]

    def suggested_context(self, question: str, doc_ids: list[str], max_facts: int = 60) -> list[str]:
        """HINT ontology version of context(): seeds + 1 hop, then base clause + clauses naming a case substance."""
        seed_ids, seed_facts = self.seed_facts(question, doc_ids)
        cases = self.run(
            """
            MATCH (k:Case)
            WHERE elementId(k) IN $ids OR EXISTS { MATCH (s)--(k) WHERE elementId(s) IN $ids }
            RETURN elementId(k) AS id, k.name AS name, k.summary AS summary
            """,
            ids=seed_ids,
        )
        facts = [f"Vụ việc '{c['name']}': {c['summary']}" for c in cases]
        # Bridge: case -> crime -> article; keep the base clause + clauses naming a substance of the case.
        # Articles cited in the question: base clause + clauses naming a substance from the question.
        clauses = self.run(
            """
            MATCH (k:Case)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(a:Article)-[:HAS_CLAUSE]->(cl:Clause)
            WHERE elementId(k) IN $case_ids
              AND (cl.number = 1 OR EXISTS { (k)-[:INVOLVES]->(:Substance)<-[:MENTIONS]-(cl) })
            RETURN a.id AS article, a.title AS title, cl.number AS number, cl.text AS text
            UNION
            MATCH (a:Article)-[:HAS_CLAUSE]->(cl:Clause)
            WHERE any(n IN $numbers WHERE a.id STARTS WITH 'Điều ' + n + ' ')
              AND (cl.number = 1 OR EXISTS { (cl)-[:MENTIONS]->(s:Substance) WHERE s.name IN $substances })
            RETURN a.id AS article, a.title AS title, cl.number AS number, cl.text AS text
            """,
            case_ids=[c["id"] for c in cases], numbers=re.findall(r"[Đđ]iều (\d+)", question),
            substances=find_substances(question),
        )
        for cl in sorted(clauses, key=lambda r: (r["article"], r["number"])):
            facts.append(f"[{cl['article']} - {cl['title']}] khoản {cl['number']}: {cl['text']}")
        return list(dict.fromkeys(facts + seed_facts))[:max_facts]

# ---------------------------------------------------------------------------------------------- KG-2

def build_graph(graph: Neo4jGraph, law_docs: list[Document], news_docs: list[Document],
                llm_fn: Callable[..., str]) -> None:
    """Load both KBs into an empty graph. llm_fn(prompt, json_mode=False) -> str (metered OpenAI chat).

    KG_ONTOLOGY=suggested in the environment rebuilds the HINT ontology (for ket_qua_benchmark_kg.hint.txt).
    """
    if os.getenv("KG_ONTOLOGY") == "suggested":
        return build_suggested_graph(graph, law_docs, news_docs, llm_fn)
    graph.suggested_constraints()
    articles = [parse_law_article_detailed(d) for d in law_docs]
    for article in articles:
        graph.add_article_detailed(article)
    graph.add_substance_aliases()
    crimes = [a["crime"] for a in articles if a["crime"]]
    for doc in news_docs:
        for case in extract_news_cases(doc, lambda p: llm_fn(p, json_mode=True), crimes):
            graph.add_case_detailed(canonicalize_substances(case), doc)

def build_suggested_graph(graph: Neo4jGraph, law_docs: list[Document], news_docs: list[Document],
                          llm_fn: Callable[..., str]) -> None:
    """HINT ontology, unchanged (the baseline the own ontology is compared against)."""
    graph.suggested_constraints()
    articles = [parse_law_article(d) for d in law_docs]
    for article in articles:
        graph.add_law_article(article)
    crimes = [a["crime"] for a in articles if a["crime"]]
    for doc in news_docs:
        for case in extract_news_cases(doc, lambda p: llm_fn(p, json_mode=True), crimes):
            graph.add_news_case(case, doc)

# ---------------------------------------------------------------------------------------------- KG-4

GRAPH_PROMPT = """Trả lời câu hỏi chỉ dựa trên ngữ cảnh (đoạn văn bản và dữ kiện từ knowledge graph).
Nêu rõ số Điều luật khi có. Nếu ngữ cảnh không đủ, nói không đủ thông tin.

Dữ kiện knowledge graph:
{facts}

Đoạn văn bản:
{chunks}

Câu hỏi: {question}
Trả lời:"""

class GraphRAGAgent:
    """Hybrid GraphRAG: the same vector top-k as flat RAG, plus facts expanded from the graph."""

    def __init__(self, store: EmbeddingStore, graph: Neo4jGraph, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.graph = graph
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        chunks = self.store.search(question, top_k=top_k)
        doc_ids = list(dict.fromkeys(c["metadata"].get("doc_id") for c in chunks if c["metadata"].get("doc_id")))
        facts = self.graph.context(question, doc_ids)
        prompt = GRAPH_PROMPT.format(
            facts="\n".join(f"- {f}" for f in facts) or "(không có)",
            chunks="\n\n".join(f"[{i}] {c['content']}" for i, c in enumerate(chunks, 1)),
            question=question,
        )
        return self.llm_fn(prompt)
