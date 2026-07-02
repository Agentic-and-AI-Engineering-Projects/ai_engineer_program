"""
P5 ReviewCrew — Hierarchical variant.

Third orchestration mode for the same PR-review problem.

Modes side-by-side in P5:
  crew.py               — Process.sequential          (fixed order: fetch → review → write)
  crew_parallel.py      — Process.sequential + async  (parallel specialists → sequential summary)
  crew_hierarchical.py  — Process.hierarchical        (manager LLM delegates dynamically) ← this file

The hierarchical shape:
  - You DECLARE the specialist pool (fetcher + 3 reviewers + writer)
  - You DO NOT pre-assign tasks to specific agents
  - You give the CREW ONE high-level goal
  - A MANAGER agent looks at the goal + specialist pool and decides who runs when
  - The manager can loop — send the report back for another review, request more detail, etc.
  - The manager can revise its plan mid-flight based on what each specialist returns

Run:
    python crew_hierarchical.py "https://github.com/OWNER/REPO/pull/N"

Requires: ANTHROPIC_API_KEY in .env, crewai, GITHUB_TOKEN for the fetch tool.
"""
import os
os.environ["LITELLM_LOG"] = "DEBUG"

import sys
from dotenv import load_dotenv
from crewai import Agent, Crew, Task, Process, LLM
from agents import code_fetcher, tech_writer
from tools import fetch_pr_details, post_pr_comment

load_dotenv()


# Same three specialists as crew_parallel.py — apples-to-apples
# security_reviewer, style_reviewer, perf_reviewer.

security_reviewer = Agent(
    role="Security Specialist",
    goal="Find security vulnerabilities, hardcoded secrets, and unsafe patterns",
    backstory=(
        "You are a security engineer focused exclusively on vulnerabilities. "
        "You look for hardcoded credentials, injection risks, insecure protocols, "
        "and unsafe data handling."
    ),
    tools=[],
    llm="anthropic/claude-opus-4-7",
    verbose=True,
    allow_delegation=False,   # specialists do NOT delegate
)

style_reviewer = Agent(
    role="Code Style Specialist",
    goal="Find code style issues, naming violations, and maintainability problems",
    backstory=(
        "You are a senior engineer who enforces clean code standards. "
        "You look for naming conventions, missing type hints, dead code, "
        "and readability issues."
    ),
    tools=[],
    llm="anthropic/claude-opus-4-7",
    verbose=True,
    allow_delegation=False,
)

perf_reviewer = Agent(
    role="Performance Specialist",
    goal="Find performance issues, inefficient patterns, and resource leaks",
    backstory=(
        "You are a performance engineer. You look for unclosed resources, "
        "inefficient loops, unnecessary computations, and memory issues."
    ),
    tools=[],
    llm="anthropic/claude-opus-4-7",
    verbose=True,
    allow_delegation=False,
)


# The manager — this is what makes it hierarchical.
# The manager sees the goal and the specialist pool and decides who runs when.
# allow_delegation=True is the key flag — it means "you can hand work to others."

manager = Agent(
    role="PR Review Coordinator",
    goal=(
        "Coordinate the review of a GitHub PR by delegating to the right specialists. "
        "Decide who should fetch, who should review which dimension, and when to "
        "hand off to the writer. Loop back for more detail if a specialist's output "
        "is too shallow to make a merge/reject decision."
    ),
    backstory=(
        "You are an experienced engineering manager. You understand the trade-off "
        "between fast merges and thorough reviews. You know when a security concern "
        "is a blocker and when a style issue is not. You are decisive but willing "
        "to send work back for more depth when the quality demands it."
    ),
    llm=LLM(model="anthropic/claude-opus-4-7"),
    verbose=True,
    allow_delegation=True,   # ← key flag: manager CAN delegate
)


def run_hierarchical_review(pr_url: str) -> str:
    """Run the hierarchical PR review.

    ONE task, no per-task agent assignments. The manager reads the goal
    and dispatches specialists in whatever order it decides.
    """
    review_goal = Task(
        description=(
            f"Coordinate a complete PR review for: {pr_url}\n\n"
            "The goal is to produce a well-structured markdown report covering:\n"
            "1. A brief summary of the PR (2-3 sentences)\n"
            "2. Security issues found (with severity + file:line)\n"
            "3. Code style issues found (with severity + file:line)\n"
            "4. Performance issues found (with severity + file:line)\n"
            "5. A final recommendation: APPROVE / REQUEST CHANGES / COMMENT\n\n"
            "You have these specialists available to delegate to:\n"
            "- code_fetcher: retrieves the PR title, description, and full diff\n"
            "- security_reviewer: hunts vulnerabilities and unsafe patterns\n"
            "- style_reviewer: enforces code style and maintainability\n"
            "- perf_reviewer: finds performance issues and resource leaks\n"
            "- tech_writer: assembles the final formatted report\n\n"
            "Decide the order. Decide when to hand off. If any specialist's output "
            "is too shallow to reach a merge decision, send it back for more detail."
        ),
        expected_output=(
            "A complete markdown PR review report with sections for Summary, "
            "Security Issues, Style Issues, Performance Issues, and Recommendation."
        ),
        agent=None,   # ← NO agent assignment — manager decides
    )

    crew = Crew(
        agents=[code_fetcher, security_reviewer, style_reviewer,
                perf_reviewer, tech_writer],
        tasks=[review_goal],
        manager_agent=manager,
        process=Process.hierarchical,   # ← the supervisor pattern
        verbose=True,
        max_rpm=20,                     # rate limiting; manager loops can burn RPM
    )

    result = crew.kickoff()

    # Post to GitHub via plain Python — not an AI reasoning task
    post_result = post_pr_comment._run(pr_url=pr_url, comment=result.raw)
    print(f"\nGitHub: {post_result}")

    return result.raw


if __name__ == "__main__":
    pr_url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "https://github.com/rrvenkatrama/agentic_ai_projects/pull/1"
    )
    print("\n" + "=" * 60)
    print("HIERARCHICAL REVIEW CREW REPORT")
    print("=" * 60)
    print("Watch [DEBUG]: Working Agent lines to see the manager's delegation decisions.")
    print("Watch the manager pick fetcher → reviewers → writer, and possibly loop back.\n")
    print(run_hierarchical_review(pr_url))
