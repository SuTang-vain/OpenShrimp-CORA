from typing import Optional, Dict, Any, List
from neo4j import GraphDatabase

from backend.shared.secure_store import load_credentials


class Neo4jClient:
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        self._driver = GraphDatabase.driver(uri, auth=(username, password))
        self._database = database

    @classmethod
    def from_store(cls) -> Optional["Neo4jClient"]:
        creds = load_credentials("neo4j") or {}
        uri = creds.get("connectionUrl")
        user = creds.get("username")
        pwd = creds.get("password")
        db = creds.get("database") or "neo4j"
        if not (uri and user and pwd):
            return None
        try:
            client = cls(uri, user, pwd, db)
            client.verify_connectivity()
            client.ensure_schema()
            return client
        except Exception:
            return None

    def close(self):
        try:
            self._driver.close()
        except Exception:
            pass

    def verify_connectivity(self):
        with self._driver.session(database=self._database) as session:
            session.run("RETURN 1 AS ok").consume()

    def ensure_schema(self):
        with self._driver.session(database=self._database) as session:
            # 唯一约束：Term.name、Source.id、Entity.name
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:Term) REQUIRE t.name IS UNIQUE").consume()
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE").consume()
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE").consume()

    # --- 简单术语共现 ---
    def upsert_terms(self, terms: List[str]) -> int:
        if not terms:
            return 0
        with self._driver.session(database=self._database) as session:
            tx = session.begin_transaction()
            for name in terms:
                tx.run("MERGE (:Term {name: $name})", name=name)
            tx.commit()
        return len(terms)

    def upsert_source(self, source_id: Optional[str]) -> bool:
        if not source_id:
            return False
        with self._driver.session(database=self._database) as session:
            session.run("MERGE (:Source {id: $id})", id=source_id).consume()
        return True

    def add_cooccurrence(self, source: str, target: str, source_id: Optional[str] = None):
        cypher = (
            "MERGE (a:Term {name: $a}) "
            "MERGE (b:Term {name: $b}) "
            "MERGE (a)-[r:CO_OCCURS]->(b) "
            "ON CREATE SET r.weight = 1 "
            "ON MATCH SET r.weight = coalesce(r.weight, 0) + 1 "
            "WITH r "
            "SET r.source_id = coalesce($sid, r.source_id)"
        )
        with self._driver.session(database=self._database) as session:
            session.run(cypher, a=source, b=target, sid=source_id).consume()

    def query_subgraph_by_terms(self, terms: List[str], limit: int = 40) -> Dict[str, Any]:
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        with self._driver.session(database=self._database) as session:
            result = session.run(
                "MATCH (t:Term) WHERE t.name IN $terms "
                "MATCH (t)-[r:CO_OCCURS]->(u:Term) "
                "RETURN t.name AS s, u.name AS t, r.weight AS w "
                "LIMIT $limit",
                terms=terms, limit=limit
            )
            for record in result:
                s = record["s"]
                t = record["t"]
                w = record["w"] or 1
                if s not in nodes:
                    nodes[s] = {"id": s, "label": s, "weight": 1}
                if t not in nodes:
                    nodes[t] = {"id": t, "label": t, "weight": 1}
                edges.append({"source": s, "target": t, "weight": w, "type": "cooccurrence"})
        return {"nodes": list(nodes.values()), "edges": edges, "evidence": []}

    # --- 实体/关系抽取与查询 ---
    def upsert_entity(self, name: str, etype: Optional[str] = None):
        with self._driver.session(database=self._database) as session:
            session.run("MERGE (e:Entity {name: $name}) ON CREATE SET e.type = $type", name=name, type=etype).consume()

    def add_relation(self, src: str, rel_type: str, dst: str, source_id: Optional[str] = None):
        cypher = (
            "MERGE (a:Entity {name: $a}) "
            "MERGE (b:Entity {name: $b}) "
            "MERGE (a)-[r:RELATES {type: $rt}]->(b) "
            "ON CREATE SET r.weight = 1 "
            "ON MATCH SET r.weight = coalesce(r.weight, 0) + 1 "
            "WITH r SET r.source_id = coalesce($sid, r.source_id)"
        )
        with self._driver.session(database=self._database) as session:
            session.run(cypher, a=src, b=dst, rt=rel_type, sid=source_id).consume()

    def query_neighbors(self, terms: List[str], relation_types: Optional[List[str]] = None, depth: int = 1, limit: int = 100) -> Dict[str, Any]:
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        with self._driver.session(database=self._database) as session:
            if depth <= 1:
                where_rel = "" if not relation_types else " WHERE r.type IN $rtypes"
                result = session.run(
                    "MATCH (e:Entity) WHERE e.name IN $terms "
                    "MATCH (e)-[r:RELATES]->(u:Entity)" + where_rel + " "
                    "RETURN e.name AS s, u.name AS t, r.type AS rt, r.weight AS w "
                    "LIMIT $limit",
                    terms=terms, rtypes=relation_types, limit=limit
                )
                for record in result:
                    s = record["s"]; t = record["t"]; rt = record["rt"]; w = record["w"] or 1
                    if s not in nodes: nodes[s] = {"id": s, "label": s}
                    if t not in nodes: nodes[t] = {"id": t, "label": t}
                    edges.append({"source": s, "target": t, "weight": w, "type": rt or "RELATES"})
            else:
                # 变量长度路径查询，限制最大跳数；返回边的起止与属性
                where_rel = "" if not relation_types else " WHERE ALL(rel IN relationships(p) WHERE rel.type IN $rtypes)"
                result = session.run(
                    "MATCH (e:Entity) WHERE e.name IN $terms "
                    "MATCH p=(e)-[r:RELATES*1..$depth]->(u:Entity) " + where_rel + " "
                    "UNWIND relationships(p) AS rel "
                    "RETURN startNode(rel).name AS s, endNode(rel).name AS t, rel.type AS rt, rel.weight AS w "
                    "LIMIT $limit",
                    terms=terms, rtypes=relation_types, depth=depth, limit=limit
                )
                for record in result:
                    s = record["s"]; t = record["t"]; rt = record["rt"]; w = record["w"] or 1
                    if s and s not in nodes: nodes[s] = {"id": s, "label": s}
                    if t and t not in nodes: nodes[t] = {"id": t, "label": t}
                    if s and t:
                        edges.append({"source": s, "target": t, "weight": w, "type": rt or "RELATES"})
        return {"nodes": list(nodes.values()), "edges": edges, "evidence": []}

    def shortest_path(self, a: str, b: str, max_hops: int = 5, relation_types: Optional[List[str]] = None) -> Dict[str, Any]:
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        with self._driver.session(database=self._database) as session:
            where_rel = "" if not relation_types else " WHERE ALL(rel IN relationships(p) WHERE rel.type IN $rtypes)"
            result = session.run(
                "MATCH (a:Entity {name: $a}),(b:Entity {name: $b}) "
                "MATCH p=shortestPath((a)-[:RELATES*1..$depth]->(b)) " + where_rel + " "
                "UNWIND relationships(p) AS rel "
                "RETURN startNode(rel).name AS s, endNode(rel).name AS t, rel.type AS rt, rel.weight AS w",
                a=a, b=b, depth=max_hops, rtypes=relation_types
            )
            for record in result:
                s = record["s"]; t = record["t"]; rt = record["rt"]; w = record["w"] or 1
                if s and s not in nodes: nodes[s] = {"id": s, "label": s}
                if t and t not in nodes: nodes[t] = {"id": t, "label": t}
                if s and t:
                    edges.append({"source": s, "target": t, "weight": w, "type": rt or "RELATES"})
        return {"nodes": list(nodes.values()), "edges": edges, "evidence": []}