"""
LangGraph orchestration workflow — Phase 7.

Graph topology (sequential — avoids concurrent state write conflicts):
    START → supervisor → business_agent → finance_agent → market_agent → scheme_agent → synthesizer → END

Each agent checks required_agents and skips itself if not needed.
This is simpler and produces deterministic, correct behavior.
"""
from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from app.agents.business_agent import business_agent_node
from app.agents.finance_agent  import finance_agent_node
from app.agents.market_agent   import market_agent_node
from app.agents.scheme_agent   import scheme_agent_node
from app.agents.state          import AgentState
from app.agents.supervisor     import supervisor_node
from app.agents.synthesizer    import synthesizer_node

logger = logging.getLogger(__name__)


def build_advisory_graph() -> StateGraph:
    """
    Build and compile the advisory graph.

    Architecture: sequential chain — each specialist agent self-skips if not required.
    This avoids LangGraph InvalidUpdateError from concurrent writes to shared state keys.

    business_agent → finance_agent: finance can use business results
    market_agent uses location from state (independent)
    scheme_agent → benefits from both business + finance results
    """
    builder = StateGraph(AgentState)

    # Nodes
    builder.add_node("supervisor",     supervisor_node)
    builder.add_node("business_agent", business_agent_node)
    builder.add_node("finance_agent",  finance_agent_node)
    builder.add_node("market_agent",   market_agent_node)
    builder.add_node("scheme_agent",   scheme_agent_node)
    builder.add_node("synthesizer",    synthesizer_node)

    # Sequential edges
    builder.add_edge(START,            "supervisor")
    builder.add_edge("supervisor",     "business_agent")
    builder.add_edge("business_agent", "finance_agent")
    builder.add_edge("finance_agent",  "market_agent")
    builder.add_edge("market_agent",   "scheme_agent")
    builder.add_edge("scheme_agent",   "synthesizer")
    builder.add_edge("synthesizer",    END)

    return builder.compile()


# Module-level singleton — compiled once, used by all requests
advisory_graph = build_advisory_graph()
