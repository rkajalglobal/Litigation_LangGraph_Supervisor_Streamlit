"""Supervisor-driven LangGraph litigation workflow.

Each worker returns to supervisor, which selects the next node. No interrupts,
Command, automatic email, or binding legal deadlines are used.
"""
from typing import TypedDict, Any
from langgraph.graph import StateGraph, START, END
from agents.nodes import (intake_agent, matter_agent, precedent_agent, caselaw_agent,
                          analysis_agent, drafting_agent, task_agent)

class LitigationState(TypedDict, total=False):
    event: dict[str, Any]
    matter: dict[str, Any]
    precedents: list[dict]
    case_law: list[dict]
    research_note: str
    analysis: str
    draft: str
    tasks: list[dict]
    error: str
    status: str
    completed: list[str]   # Completed worker nodes, used for routing and loop protection.
    next_agent: str       # Supervisor's next worker choice (or 'finish').
    supervisor_reason: str
    supervisor_history: list[dict]

# Worker prerequisites: supervisor will not dispatch a worker before its inputs exist.
PREREQUISITES = {
    'intake': [],
    'matter_match': ['intake'],
    'precedent_research': ['matter_match'],
    'case_law_research': ['matter_match'],
    'analysis': ['precedent_research', 'case_law_research'],
    'drafting': ['analysis'],
    'task_planning': ['drafting'],
}
WORKERS = {
    'intake': intake_agent,
    'matter_match': matter_agent,
    'precedent_research': precedent_agent,
    'case_law_research': caselaw_agent,
    'analysis': analysis_agent,
    'drafting': drafting_agent,
    'task_planning': task_agent,
}


def supervisor_agent(state: LitigationState) -> dict:
    """SUPERVISOR NODE: inspect state, choose an eligible worker, or finish.

    This deterministic supervisor is intentionally auditable: it does not use an
    LLM to bypass security gates or invent an execution plan. Unlike a linear
    chain, every worker returns here and the supervisor makes a new decision.
    Research branches can be reordered without changing worker code.
    """
    done = list(state.get('completed', []))
    if state.get('error') or state.get('status') in ('blocked', 'needs_matter_review'):
        next_agent, reason = 'finish', 'Safety gate: intake/matter validation failed.'
    elif len(done) >= len(WORKERS):
        next_agent, reason = 'finish', 'All required agents completed; hand off for attorney review.'
    else:
        eligible = [name for name, deps in PREREQUISITES.items()
                    if name not in done and all(dep in done for dep in deps)]
        next_agent = eligible[0] if eligible else 'finish'
        reason = (f'Dispatch {next_agent}: prerequisites satisfied.' if eligible
                  else 'No eligible agent; workflow cannot proceed.')
    history = list(state.get('supervisor_history', []))
    history.append({'completed': done, 'decision': next_agent, 'reason': reason})
    return {'next_agent': next_agent, 'supervisor_reason': reason,
            'supervisor_history': history}


def tracked_worker(name, fn):
    """Wrap each worker so supervisor can track progress without modifying it."""
    def run(state):
        updates = fn(state)
        return {**updates, 'completed': [*state.get('completed', []), name]}
    return run

builder = StateGraph(LitigationState)
builder.add_node('supervisor', supervisor_agent)
for name, fn in WORKERS.items():
    builder.add_node(name, tracked_worker(name, fn))
    # RETURN EDGE: worker hands updated state back to supervisor for next decision.
    builder.add_edge(name, 'supervisor')

# START EDGE: supervisor is the sole entry point and chooses first worker.
builder.add_edge(START, 'supervisor')
# ROUTING EDGES: supervisor chooses among eligible workers or END.
# The router reads a state field set by supervisor; no Command/interrupt is used.
builder.add_conditional_edges('supervisor', lambda s: s['next_agent'],
                              {**{name: name for name in WORKERS}, 'finish': END})
workflow = builder.compile()
