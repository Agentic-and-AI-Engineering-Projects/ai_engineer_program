"""
Advanced Pattern 02 — Supervisor (CrewAI Process.hierarchical)

Same use case as A1 Orchestrator-Worker (research a topic, produce a report).
Different orchestration shape: instead of one LLM decomposition + parallel
workers + one synthesizer, a MANAGER agent dynamically delegates to three
distinct specialists (researcher, writer, editor) one at a time, looping
back to decide each next move.

Run:
    python advanced_patterns/02_supervisor_crewai/pattern.py "quantum computing"

Requires: ANTHROPIC_API_KEY in .env, crewai, ddgs.
"""
import os
import sys

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from ddgs import DDGS

load_dotenv()


# ---------------------------------------------------------------------------
# A simple web-search tool the researcher will use
# (CrewAI tools must subclass BaseTool — same shape as in P5 ReviewCrew)
# ---------------------------------------------------------------------------

class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search the web for information. Pass a query string. "
        "Returns the top 3 results with title and snippet."
    )

    def _run(self, query: str) -> str:
        with DDGS(timeout=10) as ddgs:
            results = []
            for r in ddgs.text(query, max_results=3):
                results.append(f"- {r['title']}: {r['body'][:200]}")
            return "\n".join(results) if results else "No results."


# ---------------------------------------------------------------------------
# LLM — using Claude through CrewAI's LLM wrapper
# ---------------------------------------------------------------------------

# CrewAI accepts model strings in litellm format
LLM_MODEL = "anthropic/claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# The three specialist agents + the manager agent
# ---------------------------------------------------------------------------

researcher = Agent(
    role="Senior Research Analyst",
    goal=(
        "Find authoritative, current sources on the assigned topic. "
        "Return concrete facts with brief citations."
    ),
    backstory=(
        "You are a detail-oriented research analyst with 10+ years of experience. "
        "You prefer primary sources, distinguish hype from substance, and always "
        "cite where each fact came from."
    ),
    tools=[WebSearchTool()],
    llm=LLM(model=LLM_MODEL),
    verbose=True,
    allow_delegation=False,   # researcher doesn't delegate further
)

writer = Agent(
    role="Technical Writer",
    goal=(
        "Draft a clear, well-structured 5-paragraph report from research findings. "
        "Aim for an informed-non-expert audience."
    ),
    backstory=(
        "You are an award-winning technical writer. You weave findings into a "
        "narrative, avoid jargon when possible, and structure the report with a "
        "lead, three body sections, and a conclusion."
    ),
    llm=LLM(model=LLM_MODEL),
    verbose=True,
    allow_delegation=False,
)

editor = Agent(
    role="Senior Editor",
    goal=(
        "Polish the draft for clarity, accuracy, tone, and flow. "
        "Flag any unsupported claims that should be sent back for more research."
    ),
    backstory=(
        "You are a senior copy editor with a sharp eye for unsupported claims "
        "and unclear prose. You tighten without losing substance, and you "
        "explicitly identify gaps that need additional research."
    ),
    llm=LLM(model=LLM_MODEL),
    verbose=True,
    allow_delegation=False,
)

# The manager is just another agent — but it sees the goal + the agent pool
# and decides who runs when. With Process.hierarchical, CrewAI automatically
# uses the manager_llm (or manager_agent) to make these delegation decisions.
manager = Agent(
    role="Content Production Manager",
    goal=(
        "Coordinate research, writing, and editing to produce a polished, "
        "factually grounded report on the given topic. Decide who runs when, "
        "loop back for revisions if needed."
    ),
    backstory=(
        "You are an experienced editorial manager. You know when research is "
        "thin, when a draft needs more substance, and when a piece is ready "
        "to ship. You are decisive but willing to send work back for revision "
        "when quality demands it."
    ),
    llm=LLM(model=LLM_MODEL),
    verbose=True,
    allow_delegation=True,   # ← key flag: manager CAN delegate to specialists
)


# ---------------------------------------------------------------------------
# The crew task — note this is ONE goal, NOT pre-decomposed.
# The manager will figure out how to delegate it.
# ---------------------------------------------------------------------------

def build_crew(topic: str) -> Crew:
    research_task = Task(
        description=(
            f"Produce a polished 5-paragraph report on the topic: '{topic}'. "
            "The report should be factually grounded, clearly written, and "
            "edited for accuracy and flow. Manager: delegate to the appropriate "
            "specialists (researcher, writer, editor) in whatever order makes "
            "sense, and revise as needed."
        ),
        expected_output=(
            "A polished 5-paragraph report with concrete facts cited inline. "
            "Body covers the topic's core principles, current state, and "
            "real-world implications."
        ),
        agent=None,   # NO agent assigned — manager decides
    )

    crew = Crew(
        agents=[researcher, writer, editor],   # the specialist pool
        tasks=[research_task],
        manager_agent=manager,                  # the supervising LLM
        process=Process.hierarchical,           # ← supervisor pattern
        verbose=True,
        max_rpm=20,                             # rate limiting
    )

    return crew


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "the role of agentic AI in enterprise software"

    print(f"\n=== Supervisor pattern: producing report on {topic!r} ===\n")
    print("Watch the [DEBUG]: Working Agent lines to see the manager's delegation decisions.")
    print("Watch how the manager picks researcher → writer → editor (and possibly loops back).\n")

    crew = build_crew(topic)
    result = crew.kickoff()

    print("\n=== Final Report ===\n")
    print(result.raw if hasattr(result, "raw") else result)

    print("\n=== Stats ===")
    if hasattr(result, "token_usage"):
        print(f"Token usage: {result.token_usage}")
    if hasattr(result, "tasks_output"):
        print(f"Number of task outputs: {len(result.tasks_output)}")


if __name__ == "__main__":
    main()
