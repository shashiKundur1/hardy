import os

from langgraph.graph import END, START, StateGraph

from src.agent import nodes
from src.agent.state import AgentState
from src.config import settings

if settings.langsmith_tracing and settings.langsmith_api_key:
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_API_KEY", settings.langsmith_api_key)
    os.environ.setdefault("LANGSMITH_PROJECT", settings.langsmith_project)


def build():
    builder = StateGraph(AgentState)
    builder.add_node("load_behaviour", nodes.load_behaviour)
    builder.add_node("infer_intent", nodes.infer_intent)
    builder.add_node("retrieve", nodes.retrieve)
    builder.add_node("refine_query", nodes.refine_query)
    builder.add_node("generate", nodes.generate)
    builder.add_node("store", nodes.store)

    builder.add_edge(START, "load_behaviour")
    builder.add_edge("load_behaviour", "infer_intent")
    builder.add_conditional_edges(
        "infer_intent", nodes.should_retrieve, {"retrieve": "retrieve", "halt": END}
    )
    builder.add_conditional_edges(
        "retrieve",
        nodes.grade_evidence,
        {"generate": "generate", "refine": "refine_query", "halt": END},
    )
    builder.add_edge("refine_query", "retrieve")
    builder.add_edge("generate", "store")
    builder.add_edge("store", END)
    return builder.compile()


graph = build()


def initial_state(user_id: int, trigger_reason: str, profile_hash: str) -> AgentState:
    return {
        "user_id": user_id,
        "trigger_reason": trigger_reason,
        "profile_hash": profile_hash,
        "events": [],
        "behaviour_summary": "",
        "intent": None,
        "query": "",
        "candidates_raw": [],
        "candidates": [],
        "evidence_ok": False,
        "refine_count": 0,
        "narrative": "",
        "product_ids": [],
        "nodes_visited": [],
    }


async def run(user_id: int, trigger_reason: str, profile_hash: str) -> AgentState:
    return await graph.ainvoke(initial_state(user_id, trigger_reason, profile_hash))
