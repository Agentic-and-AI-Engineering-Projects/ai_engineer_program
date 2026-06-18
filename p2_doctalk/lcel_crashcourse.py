"""
LCEL Crash Course — 5 progressive examples.

LCEL (LangChain Expression Language) = the `|` pipe syntax for composing
"Runnables" into chains. This file demystifies it by going from "build the
mechanism yourself" → "use real LangChain components" → "real LLM chain"
→ "the doctalk fan-out pattern with parallel branches."

Each example is a standalone function. Run them individually or all at once.

Mental model to carry through: the `|` operator builds a Runnable object that
holds a list of steps. `.invoke(x)` walks the list, feeding output of each step
into the next. Inert until invoked. Like a Unix pipe for Python objects.
"""

import os
from dotenv import load_dotenv

from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
    RunnableBranch,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_anthropic import ChatAnthropic

load_dotenv()


# ============================================================================
# EXAMPLE 1 — Build your own Runnable / RunnableSequence from scratch.
# Purpose: prove there's no magic. The `|` operator is just Python's __or__,
# overloaded on a base class. ~15 lines of Python = the core of LCEL.
# ============================================================================
def example_1_from_scratch():
    """No LangChain. Build the |-mechanism yourself."""

    class Runnable:
        # Overload | so `a | b` returns a sequence object holding [a, b].
        def __or__(self, other):
            return RunnableSequence([self, other])

        # Subclasses must define what "running" means for them.
        def invoke(self, x):
            raise NotImplementedError

    class RunnableSequence(Runnable):
        def __init__(self, steps):
            # Just a list of Runnables, in order.
            self.steps = steps

        # Keep the sequence flat when more steps are piped on.
        def __or__(self, other):
            return RunnableSequence(self.steps + [other])

        # Walk the steps. Output of each = input of the next.
        def invoke(self, x):
            result = x
            for step in self.steps:
                result = step.invoke(result)
            return result

    # Three concrete Runnables — trivial math operations.
    class AddOne(Runnable):
        def invoke(self, x):
            return x + 1

    class Double(Runnable):
        def invoke(self, x):
            return x * 2

    class Square(Runnable):
        def invoke(self, x):
            return x ** 2

    # Compose with | — same syntax as real LCEL.
    chain = AddOne() | Double() | Square()

    print("Example 1 — from-scratch Runnable")
    print(f"  type(chain) = {type(chain).__name__}")
    print(f"  steps       = {[type(s).__name__ for s in chain.steps]}")
    print(f"  invoke(3)   = {chain.invoke(3)}    # ((3+1)*2)**2 = 64")
    print()


# ============================================================================
# EXAMPLE 2 — Real LangChain. RunnableLambda wraps plain Python functions
# so they can sit in a chain.
# ============================================================================
def example_2_runnable_lambda():
    """Three plain functions composed with | via RunnableLambda."""

    # Each function takes one input and returns one output.
    add_one = RunnableLambda(lambda x: x + 1)
    double = RunnableLambda(lambda x: x * 2)
    square = RunnableLambda(lambda x: x ** 2)

    # Same composition as Example 1, but using real LangChain Runnables.
    chain = add_one | double | square

    print("Example 2 — RunnableLambda")
    print(f"  type(chain) = {type(chain).__name__}")
    print(f"  invoke(3)   = {chain.invoke(3)}    # same 64")
    print()


# ============================================================================
# EXAMPLE 3 — RunnableParallel: fan one input out into multiple branches,
# collect results into a dict. This is what `{...}` becomes inside a chain.
# ============================================================================
def example_3_parallel_dict():
    """One input, three transformations, results bundled into a dict."""

    # Three independent transforms on the same string.
    to_upper = RunnableLambda(lambda s: s.upper())
    reverse = RunnableLambda(lambda s: s[::-1])
    length = RunnableLambda(lambda s: len(s))

    # RunnableParallel: every value-runnable receives the SAME input,
    # results are gathered into a dict with the same keys.
    analyze = RunnableParallel(
        upper=to_upper,
        reverse=reverse,
        length=length,
    )

    result = analyze.invoke("hello")

    print("Example 3 — RunnableParallel (fan-out)")
    print(f"  input  = 'hello'")
    print(f"  output = {result}")
    print(f"  Note: every branch got the same 'hello' as input.")
    print()


# ============================================================================
# EXAMPLE 4 — RunnablePassthrough: keep the original input alongside
# transformed versions. The identity function as a Runnable.
# ============================================================================
def example_4_passthrough():
    """Why RunnablePassthrough exists — preserve the input across the fan-out."""

    upper = RunnableLambda(lambda s: s.upper())
    word_count = RunnableLambda(lambda s: len(s.split()))

    # Without Passthrough, the original string is gone after the fan-out.
    # Passthrough keeps it accessible under the "original" key.
    analyze = RunnableParallel(
        original=RunnablePassthrough(),
        upper=upper,
        word_count=word_count,
    )

    result = analyze.invoke("the quick brown fox")

    print("Example 4 — RunnablePassthrough (identity Runnable)")
    print(f"  input  = 'the quick brown fox'")
    print(f"  output = {result}")
    print(f"  Note: 'original' branch returned the input unchanged.")
    print()


# ============================================================================
# EXAMPLE 5 — A real LLM chain: prompt | llm | parser.
# This is the minimal LLM-using LCEL chain you'll see in the wild.
# ============================================================================
def example_5_llm_chain():
    """Minimal LCEL chain with a real LLM call."""

    # Prompt template with one placeholder: {concept}.
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a concise teacher. Answer in exactly one sentence."),
        ("human", "Explain {concept} like I'm 12."),
    ])

    # Haiku — cheap and fast, good for examples.
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001")

    # Pulls .content out of the AIMessage, returns a plain string.
    parser = StrOutputParser()

    # The chain: prompt fills the template, llm calls Claude, parser extracts text.
    chain = prompt | llm | parser

    # `.invoke()` needs a dict whose keys match the prompt's placeholders.
    answer = chain.invoke({"concept": "photosynthesis"})

    print("Example 5 — prompt | llm | parser")
    print(f"  question = 'Explain photosynthesis like I'm 12.'")
    print(f"  answer   = {answer}")
    print()


# ============================================================================
# EXAMPLE 6 — The doctalk fan-out pattern (parallel dict + LLM).
# Same shape as the real doctalk_langchain.py chain, but with fake retrieval
# so you can see the pattern without needing PDFs, embeddings, or vector DBs.
# ============================================================================
def example_6_fanout_with_llm():
    """Fan-out pattern: retrieve context + pass through question, feed both to LLM."""

    # Fake "retriever" — looks up a hardcoded fact based on the question.
    def fake_retrieve(question: str) -> str:
        facts = {
            "ocean": "The Pacific Ocean is the largest body of water on Earth.",
            "moon": "The moon is Earth's only natural satellite, about 384,000 km away.",
            "sun": "The sun is a G-type main-sequence star at the center of our solar system.",
        }
        for keyword, fact in facts.items():
            if keyword in question.lower():
                return fact
        return "No information found."

    # Prompt expects two keys — context and question — matching the dict shape below.
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer the question using only the provided context. Be concise."),
        ("human", "Context: {context}\n\nQuestion: {question}"),
    ])

    llm = ChatAnthropic(model="claude-haiku-4-5-20251001")
    parser = StrOutputParser()

    # The fan-out: same question goes to both branches, results bundled into a dict.
    # The dict's keys ("context", "question") must match the prompt's placeholders.
    chain = (
        {
            "context": RunnableLambda(fake_retrieve),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | parser
    )

    answer = chain.invoke("How far away is the moon?")

    print("Example 6 — Fan-out + LLM (the doctalk pattern, simplified)")
    print(f"  question = 'How far away is the moon?'")
    print(f"  answer   = {answer}")
    print()


# ============================================================================
# EQUIVALENT WITHOUT LCEL — same as Example 6, written as plain top-to-bottom
# Python with explicit .invoke() calls. Identical behavior, no | operator.
# ============================================================================
def example_6_equivalent_without_lcel():
    """Example 6 rewritten without the | operator. Same result, more readable."""

    def fake_retrieve(question: str) -> str:
        facts = {
            "ocean": "The Pacific Ocean is the largest body of water on Earth.",
            "moon": "The moon is Earth's only natural satellite, about 384,000 km away.",
            "sun": "The sun is a G-type main-sequence star at the center of our solar system.",
        }
        for keyword, fact in facts.items():
            if keyword in question.lower():
                return fact
        return "No information found."

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer the question using only the provided context. Be concise."),
        ("human", "Context: {context}\n\nQuestion: {question}"),
    ])
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001")

    question = "How far away is the moon?"

    # Step 1: retrieve (the "context" branch of the fan-out).
    context = fake_retrieve(question)

    # Step 2: fill the prompt template with the two pieces of data.
    formatted_prompt = prompt.invoke({"context": context, "question": question})

    # Step 3: call Claude.
    response = llm.invoke(formatted_prompt)

    # Step 4: extract the text.
    answer = response.content

    print("Example 6-equivalent — same chain, written without |")
    print(f"  question = '{question}'")
    print(f"  answer   = {answer}")
    print()


# ============================================================================
# EXAMPLE 7 — RunnableBranch: the "if/elif/else" of LCEL.
# Picks ONE chain to run, based on the input. Once chosen, the pipeline moves
# forward — no looping back, no revisiting.
# ============================================================================
def example_7_branch():
    """Route input through different chains based on a predicate."""

    # Three different transforms — one will be picked per input.
    short_chain = RunnableLambda(lambda s: f"SHORT  ({len(s)} chars): {s.upper()}")
    medium_chain = RunnableLambda(lambda s: f"MEDIUM ({len(s)} chars): {s.title()}")
    long_chain = RunnableLambda(lambda s: f"LONG   ({len(s)} chars): {s.lower()}")

    # RunnableBranch takes (predicate, chain) tuples + a final default chain.
    # First predicate that returns True wins. Default fires if none match.
    router = RunnableBranch(
        (lambda s: len(s) < 5, short_chain),
        (lambda s: len(s) < 15, medium_chain),
        long_chain,  # default
    )

    print("Example 7 — RunnableBranch (conditional routing)")
    print(f"  'hi'                         → {router.invoke('hi')}")
    print(f"  'hello world'                → {router.invoke('hello world')}")
    print(f"  'the quick brown fox jumps'  → {router.invoke('the quick brown fox jumps')}")
    print()


# ============================================================================
# EXAMPLE 8 — .with_fallbacks(): try one chain, fall back on error.
# Useful for multi-cloud LLM routing (try Anthropic, fall back to OpenAI, etc.)
# or any "try-A-then-B" recovery pattern.
# ============================================================================
def example_8_fallbacks():
    """Try a flaky chain, fall back to a backup chain on any exception."""

    # Primary chain — deliberately throws every time.
    flaky = RunnableLambda(lambda x: 1 / 0)

    # Backup chain — handles whatever the primary couldn't.
    backup = RunnableLambda(lambda x: f"BACKUP succeeded with input: {x}")

    # .with_fallbacks() attaches fallback runnables; first non-erroring wins.
    chain = flaky.with_fallbacks([backup])

    print("Example 8 — with_fallbacks (error-driven routing)")
    print(f"  invoke('hello') → {chain.invoke('hello')}")
    print()


# ============================================================================
# WHEN TO LEAVE LCEL AND SWITCH TO LANGGRAPH
# ============================================================================
# LCEL is a LINEAR PIPELINE language. Even RunnableBranch picks ONE branch and
# the pipeline marches forward — no going back, no looping, no shared mutable
# state across steps. If you need any of the below, switch to LangGraph:
#
#   - Loops / cycles
#       e.g. an agent that calls a tool, observes the result, decides whether
#       to call another tool, and loops until satisfied.
#
#   - Shared state across steps
#       e.g. multiple nodes reading and writing a common state object —
#       LangGraph's StateGraph is built for this.
#
#   - Conditional revisiting of earlier steps
#       e.g. "if the answer fails fact-check, re-retrieve with a refined query."
#
#   - Human-in-the-loop checkpoints
#       Pause the graph, wait for human approval, resume from where you stopped.
#       LangGraph has first-class checkpointing for this; LCEL does not.
#
#   - Persistent memory across runs
#       Save and restore graph state between invocations (LangGraph checkpointer).
#
#   - Streaming intermediate node state to a UI
#       LangGraph streams every node's output as it produces it; LCEL streams
#       only the final chain output.
#
# Rule of thumb:
#   One forward pass with fan-out and maybe a static route   →  LCEL.
#   Anything cyclic, stateful, or with checkpoints           →  LangGraph.
#
# In this curriculum:
#   - P2 DocTalk uses LCEL because the chain is linear: retrieve → format → LLM.
#   - P3 ResearchBot uses LangGraph because it loops (search → reflect → refine
#     → search again) and has shared state.
#   - P7 MatchScout uses LangGraph for the same reasons (multi-stage pipeline
#     with arm routing, state across stages, conditional re-tries).


# ============================================================================
# EXAMPLE 9 — Multiple FULL chains, routed conditionally.
# Each branch is its own complete LCEL chain (prompt | llm | parser).
# This is a common production pattern: a "router" that picks the right
# specialist chain based on what the user asked.
# ============================================================================
def example_9_branch_full_chains():
    """Three specialist chains (math, history, general), routed by input."""

    # Shared model + parser across all three branches.
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001")
    parser = StrOutputParser()

    # Branch 1: Math questions — explicit step-by-step system prompt.
    math_chain = (
        ChatPromptTemplate.from_messages([
            ("system", "You are a math tutor. Show your work step by step. Be concise."),
            ("human", "{question}"),
        ])
        | llm
        | parser
    )

    # Branch 2: History questions — different system prompt for historical context.
    history_chain = (
        ChatPromptTemplate.from_messages([
            ("system", "You are a history teacher. Include dates and context. Be concise."),
            ("human", "{question}"),
        ])
        | llm
        | parser
    )

    # Branch 3: Default catch-all — one-sentence general answer.
    general_chain = (
        ChatPromptTemplate.from_messages([
            ("system", "Answer in exactly one sentence."),
            ("human", "{question}"),
        ])
        | llm
        | parser
    )

    # Predicates inspect the input dict and return True/False.
    # First matching predicate wins. If none match, default fires.
    def is_math_question(x):
        keywords = ["calculate", "solve", "math", "+", "-", "*", "/", "equation"]
        return any(word in x["question"].lower() for word in keywords)

    def is_history_question(x):
        keywords = ["when did", "history", "war", "century", "ancient", "empire"]
        return any(word in x["question"].lower() for word in keywords)

    # The router IS a Runnable — it can be composed into bigger chains too.
    router = RunnableBranch(
        (is_math_question, math_chain),
        (is_history_question, history_chain),
        general_chain,
    )

    # Three different questions, each routed to a different specialist chain.
    questions = [
        "Solve: 2x + 5 = 17",
        "When did World War II end?",
        "What is the capital of France?",
    ]

    print("Example 9 — Routing between FULL chains (math / history / general)")
    for q in questions:
        answer = router.invoke({"question": q})
        print(f"  Q: {q}")
        print(f"  A: {answer}")
        print()


# ============================================================================
# NOTES ON ROUTING PATTERNS IN LCEL
# ============================================================================
# Example 9 uses *predicate routing* — cheap, fast, deterministic, but
# limited to keyword/regex/Python rules. Two upgrade paths exist:
#
# (a) LLM-classifier routing — let an LLM decide which branch to take.
#     Build a tiny "classifier" chain that returns "math" / "history" / etc.,
#     then route based on its output:
#
#         classifier = (
#             ChatPromptTemplate.from_messages([
#                 ("system", "Classify the question as 'math', 'history', or 'general'."),
#                 ("human", "{question}"),
#             ])
#             | llm
#             | parser
#         )
#         # Then route on classifier's output:
#         router = RunnableBranch(
#             (lambda x: x["category"] == "math",    math_chain),
#             (lambda x: x["category"] == "history", history_chain),
#             general_chain,
#         )
#         # Compose:
#         full = {"question": RunnablePassthrough(),
#                 "category": classifier} | router
#
#     Smarter routing, but every request costs an extra LLM call.
#
# (b) Embedding-based routing — embed the question, find the closest "anchor"
#     embedding among ["math example", "history example", "general example"],
#     route to whichever is nearest. Cheaper than (a), smarter than predicates.
#
# Composition rule: a RunnableBranch is itself a Runnable, so it can sit
# anywhere in a chain: preprocess | router | postprocess. You can also
# nest branches inside branches if you need a decision tree.


def main():
    """Run all examples in order."""
    example_1_from_scratch()
    example_2_runnable_lambda()
    example_3_parallel_dict()
    example_4_passthrough()
    example_5_llm_chain()
    example_6_fanout_with_llm()
    example_6_equivalent_without_lcel()
    example_7_branch()
    example_8_fallbacks()
    example_9_branch_full_chains()


if __name__ == "__main__":
    main()
