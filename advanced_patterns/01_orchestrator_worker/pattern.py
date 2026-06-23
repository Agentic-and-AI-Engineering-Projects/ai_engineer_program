"""
Advanced Pattern A1 — Orchestrator-Worker

A research agent where the ORCHESTRATOR (LLM) decides at runtime how many
research questions to spawn, then the SEND API fans out one worker per question.
Workers run in parallel, each given a task-specific payload (their own question).
The SYNTHESIZER (LLM) folds all findings into a coherent answer.

Run:
    python advanced_patterns/01_orchestrator_worker/pattern.py "quantum computing"

Requires: ANTHROPIC_API_KEY in .env, langgraph, anthropic, ddgs.
"""
import os
import sys
import json
import operator
from typing import TypedDict, Annotated

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.types import Send
from anthropic import Anthropic
from ddgs import DDGS

load_dotenv()


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------

class ResearchState(TypedDict):
    topic: str                                              # input
    questions: list[str]                                    # set by orchestrator
    findings: Annotated[list[dict], operator.add]           # accumulated by workers
    summary: str                                            # produced by synthesizer


class WorkerState(TypedDict):
    """The slice of state each worker receives via Send API."""
    question: str


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

ORCHESTRATOR_PROMPT = """You are a research planner. Given a topic, decompose it into 3-5 specific research questions that, taken together, give a complete picture of the topic.

Return ONLY a JSON array of strings, no preamble, no markdown fences.

Topic: {topic}

Example for topic "quantum computing":
["What are the core principles of quantum computing?","What are the most promising hardware approaches (superconducting, ion-trap, photonic)?","What real-world problems can quantum computers solve today?","What are the main challenges keeping quantum computers from broader adoption?"]
"""


def orchestrator(state: ResearchState) -> dict:
    """LLM call: decompose the topic into N research questions dynamically."""
    print(f"\n[Orchestrator] Decomposing topic: {state['topic']}")
    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": ORCHESTRATOR_PROMPT.format(topic=state["topic"])}]
    )
    raw = response.content[0].text.strip()
    # Tolerant parse — strip code fences if present
    if raw.startswith("```"):
        raw = raw.strip("`").lstrip("json").strip()
    questions = json.loads(raw)
    print(f"[Orchestrator] Generated {len(questions)} research questions:")
    for q in questions:
        print(f"  - {q}")
    return {"questions": questions}


def dispatch_workers(state: ResearchState) -> list[Send]:
    """Conditional-edge function: fan out one worker per question via Send API.

    Returning a list of Send objects tells LangGraph: spawn N parallel
    invocations of the named node, each with the given payload as its state.
    This is the dynamic fan-out primitive — N is determined at runtime
    by what the orchestrator returned, NOT hardcoded in the graph.
    """
    return [Send("worker", {"question": q}) for q in state["questions"]]


def worker(state: WorkerState) -> dict:
    """Per-question research worker. Receives only its own slice of state.

    Note the signature: state here is WorkerState (just the question),
    NOT ResearchState. Each parallel worker is isolated — it sees only
    what the Send payload gave it.
    """
    q = state["question"]
    print(f"[Worker] Researching: {q[:80]}...")
    findings = []
    with DDGS(timeout=10) as ddgs:
        for r in ddgs.text(q, max_results=2):
            findings.append({
                "question": q,                       # provenance — which Q this finding answers
                "title": r["title"],
                "body": r["body"][:300],
            })
    return {"findings": findings}                    # operator.add reducer accumulates across workers


SYNTHESIZER_PROMPT = """You are a research synthesizer. Below are findings from {n} parallel researchers, each investigating a different aspect of "{topic}". Each finding is tagged with the question it answers.

Write a coherent 5-7 sentence synthesis that weaves the findings together. Do NOT list findings one by one — integrate them. Cite which question(s) each claim comes from inline as [Q: <question excerpt>].

Findings:
{findings}
"""


def synthesizer(state: ResearchState) -> dict:
    """LLM call: synthesize all worker findings into a coherent answer."""
    print(f"\n[Synthesizer] Folding {len(state['findings'])} findings into a summary...")
    findings_text = "\n".join(
        f"- [Q: {f['question'][:60]}] {f['title']}: {f['body']}"
        for f in state["findings"]
    )
    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": SYNTHESIZER_PROMPT.format(
                n=len(state["questions"]),
                topic=state["topic"],
                findings=findings_text,
            ),
        }],
    )
    return {"summary": response.content[0].text}


# ---------------------------------------------------------------------------
# Graph wiring
# ---------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("orchestrator", orchestrator)
    graph.add_node("worker", worker)
    graph.add_node("synthesizer", synthesizer)

    graph.set_entry_point("orchestrator")

    # Dynamic fan-out: dispatch_workers returns a list of Send objects;
    # LangGraph spawns one "worker" invocation per Send in parallel.
    # The third arg (["worker"]) declares which nodes the conditional edge
    # can target — required when using Send API.
    graph.add_conditional_edges("orchestrator", dispatch_workers, ["worker"])

    # Fan-in: all parallel workers feed into the synthesizer.
    # LangGraph automatically waits for ALL workers to complete before
    # running synthesizer (sync barrier), and the operator.add reducer
    # on findings merges their parallel writes.
    graph.add_edge("worker", "synthesizer")

    graph.add_edge("synthesizer", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "the role of agentic AI in enterprise software"
    app = build_graph()

    print("\n=== Graph topology ===")
    print(app.get_graph().draw_mermaid())

    print(f"\n=== Running orchestrator-worker on: {topic!r} ===")
    result = app.invoke({
        "topic": topic,
        "questions": [],
        "findings": [],
        "summary": "",
    })

    print("\n=== Final Synthesis ===\n")
    print(result["summary"])

    print(f"\n=== Stats ===")
    print(f"Questions generated by orchestrator: {len(result['questions'])}")
    print(f"Findings collected across workers:    {len(result['findings'])}")


if __name__ == "__main__":
    main()
