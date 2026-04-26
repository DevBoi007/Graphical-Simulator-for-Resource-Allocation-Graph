from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Set, Tuple

import networkx as nx


NodeType = Literal["process", "resource"]
EdgeType = Literal["request", "allocation"]


class Node(BaseModel):
    id: str = Field(..., min_length=1)
    type: NodeType


class Edge(BaseModel):
    source: str
    target: str
    type: EdgeType


class GraphIn(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


class HighlightEdge(BaseModel):
    source: str
    target: str
    type: EdgeType


class AnalyzeOut(BaseModel):
    deadlock: bool
    message: str
    deadlock_cycles: List[List[Tuple[str, str]]]
    highlight: Dict[str, list]  # {"nodes": [...], "edges": [{source,target,type}, ...]}


app = FastAPI(title="RAG Simulator API (single-instance)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


def detect_deadlock_cycles(g: nx.DiGraph) -> List[List[Tuple[str, str]]]:
    """
    Cycle-based deadlock detection for single-instance RAG:
    - Find directed cycles
    - Keep cycles that include at least one allocation edge and at least one request edge
    - Return all such cycles as lists of (u,v) edges
    """
    cycles = list(nx.simple_cycles(g))
    deadlock_cycles: List[List[Tuple[str, str]]] = []

    for cycle in cycles:
        has_allocation = False
        has_request = False
        cycle_edges: List[Tuple[str, str]] = []

        for i in range(len(cycle)):
            u = cycle[i]
            v = cycle[(i + 1) % len(cycle)]
            if g.has_edge(u, v):
                et = g[u][v].get("type")
                cycle_edges.append((u, v))
                if et == "allocation":
                    has_allocation = True
                elif et == "request":
                    has_request = True

        if has_allocation and has_request:
            deadlock_cycles.append(cycle_edges)

    return deadlock_cycles


@app.post("/analyze", response_model=AnalyzeOut)
def analyze(graph: GraphIn):
    try:
        node_set = {n.id for n in graph.nodes}
        node_type = {n.id: n.type for n in graph.nodes}

        for e in graph.edges:
            if e.source not in node_set or e.target not in node_set:
                raise ValueError(f"Edge references unknown node: {e.source} -> {e.target}")

        # Build nx graph
        g = nx.DiGraph()
        for n in graph.nodes:
            g.add_node(n.id, type=n.type)

        for e in graph.edges:
            # Enforce semantics
            if e.type == "request":
                if node_type[e.source] != "process" or node_type[e.target] != "resource":
                    raise ValueError(f"Invalid request edge (must be Process -> Resource): {e.source} -> {e.target}")
            else:  # allocation
                if node_type[e.source] != "resource" or node_type[e.target] != "process":
                    raise ValueError(f"Invalid allocation edge (must be Resource -> Process): {e.source} -> {e.target}")
            g.add_edge(e.source, e.target, type=e.type)

        deadlock_cycles = detect_deadlock_cycles(g)
        deadlock = len(deadlock_cycles) > 0

        highlight_nodes: Set[str] = set()
        highlight_edges: List[HighlightEdge] = []

        if deadlock:
            for cyc in deadlock_cycles:
                for u, v in cyc:
                    highlight_nodes.add(u)
                    highlight_nodes.add(v)
                    highlight_edges.append(HighlightEdge(source=u, target=v, type=g[u][v]["type"]))

        msg = (
            f"Deadlock detected! Cycles found: {len(deadlock_cycles)}"
            if deadlock
            else "No deadlock detected."
        )

        return AnalyzeOut(
            deadlock=deadlock,
            message=msg,
            deadlock_cycles=deadlock_cycles,
            highlight={"nodes": sorted(highlight_nodes), "edges": [he.model_dump() for he in highlight_edges]},
        )

    except Exception as e:
        return AnalyzeOut(
            deadlock=False,
            message=f"Error: {e}",
            deadlock_cycles=[],
            highlight={"nodes": [], "edges": []},
        )
