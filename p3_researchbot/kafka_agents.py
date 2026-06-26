"""
Agent-as-Kafka-Consumer pattern — P3 ResearchBot.

Three roles, one process each (started from the CLI):

    producer    — publishes 3 research tasks (one per agent_type) to TASKS_TOPIC
    consumer    — long-running worker subscribed to TASKS_TOPIC; filters tasks
                  for its own agent_type, runs a DuckDuckGo search, and
                  publishes Finding rows to FINDINGS_TOPIC
    aggregator  — long-running collector subscribed to FINDINGS_TOPIC; waits
                  until it has one finding per agent_type, then prints a summary

Why Kafka instead of in-process LangGraph:
- Decoupled producers/consumers — agents can crash, restart, scale independently
- At-least-once delivery via consumer groups + offset commit
- Replay-able event log (auto_offset_reset='earliest' rewinds to the start)
- Each consumer group_id maintains its own offset, so different agent types
  read the same TASKS_TOPIC without stepping on each other

Run three terminals for the agents + one for the producer; aggregator pulls
the results back into a single summary.
"""

import sys
import json
import time
from pydantic import BaseModel
from ddgs import DDGS
from kafka import KafkaProducer, KafkaConsumer


# Kafka broker exposed by the k3s cluster on the home server (NodePort 30092)
BROKER = '192.168.1.156:30092'

# Two topics: tasks flow producer→consumers; findings flow consumers→aggregator
TASKS_TOPIC    = 'research-tasks'
FINDINGS_TOPIC = 'research-findings'


class Finding(BaseModel):
    """One research finding emitted by a consumer agent.

    agent: which agent_type produced this (news / technical / examples)
    title: search-result headline
    body:  search-result snippet
    """
    agent: str
    title: str
    body: str


def producer(subject='quantum computing'):
    """Publish one task per agent_type to TASKS_TOPIC.

    Each task is a small dict {'subject': <research subject>, 'agent': <agent_type>}.
    'subject' is named to avoid overloading with Kafka's "topic" — Kafka topic
    is the channel (TASKS_TOPIC); subject is the research subject being asked about.
    All 3 consumers see every task (they share the Kafka topic), but each filters
    down to the tasks addressed to its own agent_type — fan-out by content.
    """
    # Build a producer that JSON-encodes every value before publishing
    p = KafkaProducer(
        bootstrap_servers=BROKER,
        value_serializer=lambda v: json.dumps(v).encode()
    )

    # Send one task per agent_type
    for agent_type in ['news', 'technical', 'examples']:
        msg = {'subject': subject, 'agent': agent_type}
        p.send(TASKS_TOPIC, msg)
        print(f"[producer] published task → agent={agent_type}, subject={subject}")

    # flush() blocks until every queued message is acknowledged by the broker
    p.flush()
    print("[producer] all 3 tasks published")


def consumer(agent_type):
    """Long-running consumer agent for a single agent_type.

    Subscribes to TASKS_TOPIC as part of a per-agent-type consumer group,
    skips messages addressed to other agents, then runs a web search and
    publishes Finding rows on FINDINGS_TOPIC.

    group_id is per-agent-type ('news-group', 'technical-group', ...) so
    each agent type maintains its own offset — they don't compete for the
    same messages the way workers in one group would.
    """
    # Subscribe to the tasks topic
    c = KafkaConsumer(
        TASKS_TOPIC,
        bootstrap_servers=BROKER,
        # group_id scoped per agent_type → each type tracks its own offset
        group_id=f'{agent_type}-group',
        # 'earliest' rewinds to topic start on a fresh group; useful for demo
        auto_offset_reset='earliest',
        value_deserializer=lambda m: json.loads(m.decode())
    )

    # Same broker, separate producer instance for publishing findings
    p = KafkaProducer(
        bootstrap_servers=BROKER,
        value_serializer=lambda v: json.dumps(v).encode()
    )
    print(f"[{agent_type}_agent] listening on {TASKS_TOPIC}...")

    # `for msg in c` is a blocking iterator — runs forever, polling the broker
    for msg in c:
        task = msg.value

        # Content-based fan-out: ignore tasks for other agent types
        if task['agent'] != agent_type:
            continue
        print(f"[{agent_type}_agent] got task: {task['subject']}")

        # Run a DuckDuckGo search scoped by agent_type ("X news", "X technical", ...)
        findings = []
        with DDGS(timeout=10) as ddgs:
            query = f"{task['subject']} {agent_type} 2024"
            for r in ddgs.text(query, max_results=2):
                findings.append(Finding(agent=agent_type, title=r['title'], body=r['body']))

        # Publish each finding as its own message on the findings topic
        for f in findings:
            p.send(FINDINGS_TOPIC, f.model_dump())
            print(f"[{agent_type}_agent] published finding: {f.title[:60]}")
        p.flush()


def aggregator(expected=3):
    """Collect findings until one per agent_type has arrived, then summarize.

    Uses its own consumer group so the aggregator's offset is independent
    of any consumer agent. Dedupes by agent name so two findings from the
    same agent don't satisfy the 'expected' count.
    """
    # Subscribe with a dedicated group_id
    c = KafkaConsumer(
        FINDINGS_TOPIC,
        bootstrap_servers=BROKER,
        group_id='aggregator-group',
        auto_offset_reset='earliest',
        value_deserializer=lambda m: json.loads(m.decode())
    )
    print(f"[aggregator] waiting for {expected} findings (one per agent type)...")

    # Track both the full list and a set of agent names already seen
    findings = []
    seen = set()

    for msg in c:
        f = Finding(**msg.value)

        # First finding from each agent counts; later ones are ignored
        if f.agent not in seen:
            seen.add(f.agent)
            findings.append(f)
            print(f"[aggregator] received [{f.agent}] {f.title[:60]}")
        else:
            print(f"[aggregator] skipped duplicate [{f.agent}]")

        # Stop once every expected agent has contributed once
        if len(seen) >= expected:
            break

    # Print a compact summary of what we collected
    print(f"\n=== Summary ({len(findings)} findings) ===")
    for f in findings:
        print(f"  [{f.agent}] {f.title}")
        print(f"           {f.body[:100]}")


if __name__ == '__main__':
    # Simple CLI dispatcher — pick a role + optional arg
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    arg  = sys.argv[2] if len(sys.argv) > 2 else ''

    if mode == 'producer':
        producer()
    elif mode == 'consumer' and arg:
        consumer(arg)
    elif mode == 'aggregator':
        aggregator()
    else:
        print("Usage:")
        print("  python kafka_agents.py producer")
        print("  python kafka_agents.py consumer news|technical|examples")
        print("  python kafka_agents.py aggregator")
