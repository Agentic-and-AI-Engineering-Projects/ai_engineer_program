# AI Engineer Interview Cheatsheet
> Updated as projects progress. Covers concepts, patterns, and gotchas.

---

## Pydantic v2

### What it is
Runtime data validation library. Define a typed schema, Pydantic validates incoming data against it.

### BaseModel
```python
from pydantic import BaseModel

class WeatherInput(BaseModel):
    city: str               # required
    units: str = "celsius"  # optional, has default
```
- Annotations (`city: str`) are stored in `__annotations__` at class definition time
- Pydantic reads those and auto-generates `__init__`, type checking, and validation
- Fields end up as **instance variables**, not class variables

### field_validator
```python
from pydantic import field_validator

@field_validator("units")
@classmethod
def check_units(cls, v: str) -> str:
    if v not in ("celsius", "fahrenheit"):
        raise ValueError("must be celsius or fahrenheit")
    return v  # return value is used as the final field value
```
- Runs before the object is created — no instance exists yet, so `@classmethod` is required
- `v` = the value being validated
- Return the value (can transform it, e.g. `return v.lower()`)

### ValidationError
```python
from pydantic import ValidationError

try:
    validated = WeatherInput(**raw_input)
except ValidationError as e:
    return f"Invalid arguments: {e}"
```
- Raised when type check or field_validator fails
- Always catch at system boundaries (external data, LLM output)

### model_dump()
```python
validated = WeatherInput(city="London", units="celsius")
validated.model_dump()
# → {"city": "London", "units": "celsius"}
```
- Converts Pydantic object → plain dict
- Use `**validated.model_dump()` to unpack as function kwargs

---

## Claude API — tool_use

### How tool_use works (the loop)
```
You → Claude (messages + tools list)
Claude → stop_reason="tool_use"   # wants to call a tool
You → execute tool, collect result
You → Claude (messages + tool result)
Claude → stop_reason="end_turn"   # gives final answer
```
Repeat if Claude calls multiple tools in sequence.

### stop_reason values
| Value | Meaning |
|---|---|
| `"end_turn"` | Claude is done, final answer ready |
| `"tool_use"` | Claude wants to call one or more tools |
| `"max_tokens"` | Hit token limit before finishing |

### Tool schema (JSON Schema)
```python
{
    "name": "get_weather",
    "description": "Get current weather for a city.",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"},
            "units": {"type": "string", "enum": ["celsius", "fahrenheit"]},
        },
        "required": ["city"],
    },
}
```
- `description` is critical — Claude uses it to decide when to call the tool
- `required` lists mandatory fields; omitted fields use defaults

### Tool result message format
```python
{"role": "user", "content": [
    {
        "type": "tool_result",
        "tool_use_id": block.id,   # must match the tool_use block id
        "content": "result string",
    }
]}
```
- Tool results go back as role `"user"` — not `"assistant"`
- `tool_use_id` links result to the specific tool call Claude made

### TOOL_MAP pattern
```python
TOOL_MAP = {
    "get_weather": (get_weather_fn, WeatherInput),
    "calculator":  (calculator_fn,  CalculatorInput),
}

def execute_tool(name, raw_input):
    fn, schema_cls = TOOL_MAP[name]
    validated = schema_cls(**raw_input)   # Pydantic validates
    return fn(**validated.model_dump())   # call with clean args
```
- Single dispatch point for all tools
- Keeps validation and dispatch logic in one place

---

## Anthropic API — Tunable Parameters

The knobs on `client.messages.create(...)` / `.stream(...)`. Group by purpose.

### Sampling (controls randomness)

| Param | Default | Range | What it does |
|---|---|---|---|
| `temperature` | 1.0 | 0.0–1.0 | Lower = more deterministic. 0.0 ≈ "always pick highest-prob token." Use 0–0.3 for tool calls / structured output / classification. Use 0.7–1.0 for creative writing. |
| `top_p` | 1.0 | 0.0–1.0 | Nucleus sampling — sample only from tokens whose cumulative prob ≥ top_p. Alternative to temperature. **Use one or the other, not both** (Anthropic's recommendation). |
| `top_k` | unset | int | Sample only from top-k highest-prob tokens. Rarely used. Leave alone. |

**Agentic rule of thumb:** `temperature=0` for anything involving tool calls or structured output — you want determinism in the agent loop.

### Length & stopping

| Param | Required? | What it does |
|---|---|---|
| `max_tokens` | **REQUIRED** | Maximum OUTPUT tokens. Doesn't bound input. Each model has its own ceiling (Sonnet 4.6: 64K out). |
| `stop_sequences` | optional | List of strings; generation halts when any matches. Useful for "stop at next `</answer>`" patterns. |

**Gotcha:** input tokens are bounded by the **context window** (200K standard, 1M for some configs). Output tokens are bounded by `max_tokens` + model's output cap. Two separate budgets.

### Prompt caching (the biggest cost lever)

```python
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": large_doc, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": user_question}
    ]
}]
```

- `cache_control: {"type": "ephemeral"}` caches the prefix for **5 minutes** (1-hour TTL is a beta).
- Cache HIT cost: ~**10% of normal** input price. Cache MISS (first write): ~**25% more** than normal. Net win after ≥2 calls.
- Up to **4 cache breakpoints** per request. Only PREFIXES are cached — order matters; stable content must come first.
- System prompts cache too: `system=[{"type":"text","text":"...","cache_control":{"type":"ephemeral"}}]`.

**In agentic systems**, cache the system prompt + tool schemas + early conversation history. Agents replay the same prefix every turn.

### Streaming

```python
with client.messages.stream(...) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    response = stream.get_final_message()   # still needed for stop_reason
```

`stream=True` gives SSE events as tokens arrive. **Gotcha:** still need `get_final_message()` for `stop_reason`, full content blocks, and token usage. The tool loop logic stays the same; streaming is just better UX for the final text response.

### Tool use

| Param | What it does |
|---|---|
| `tools` | List of tool schemas (JSON Schema). |
| `tool_choice` | Force behavior: `{"type":"auto"}` (default, model picks), `{"type":"any"}` (must call SOME tool), `{"type":"tool","name":"X"}` (must call X), `{"type":"none"}` (no tools). |
| `disable_parallel_tool_use` | Boolean. If True, model returns at most one tool_use block per turn. Default False. |

### Extended thinking (Claude 4+ reasoning models)

```python
thinking={"type": "enabled", "budget_tokens": 10000}
```
Lets the model do internal scratchpad reasoning before responding. `budget_tokens` caps the thinking. Counts as output tokens for cost. Visible as `thinking` content blocks if you inspect.

### Batches (cost lever #2)

`client.messages.batches.create(requests=[...])` — submit up to 100K requests, results within 24h, **50% discount**. Use case: offline backfills, eval suites, one-time embedding generation. Not for live serving.

### Other

| Param | What it does |
|---|---|
| `system` | System prompt — separate top-level param, NOT a message with `role:"system"`. |
| `metadata.user_id` | Optional. Anthropic uses it for abuse tracking + per-end-user rate-limit allocation. |
| `betas` header | Opt into beta features (extended cache TTL, computer-use, etc.). |

### Interview talking points

- *"Why temperature=0 in agentic code?"* — determinism in tool calls; same input → same call.
- *"How do you control cost in production?"* — prompt caching (big lever), batches for offline work, smaller models for non-critical steps, max_tokens to cap runaway output.
- *"Why both temperature and top_p?"* — you wouldn't; use one. Anthropic explicitly recommends one or the other.
- *"What's the biggest cost lever you've used?"* — prompt caching for stable prefixes (system prompt + tool schemas + retrieved context). Up to 90% input-cost reduction on repeated calls.

---

## Streaming (Anthropic SDK)

### Non-streaming vs streaming
```python
# Non-streaming — waits for full response
response = client.messages.create(model=..., ...)

# Streaming — prints word by word
with client.messages.stream(model=..., ...) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    response = stream.get_final_message()  # same structure as non-streaming
```
- `get_final_message()` must be called **inside** the `with` block
- Returns same object as `messages.create()` — `.stop_reason`, `.content` all available
- `end=""` prevents newline per token; `flush=True` forces immediate output

### When to stream vs not
- Stream the **final text response** to the user (better UX)
- The tool loop itself works the same — `stop_reason` and `content` come from `get_final_message()`

---

## Python Concepts (relevant to agentic code)

### async/await
```python
async def run_agent(message: str) -> None:
    response = await some_async_call()

asyncio.run(main())   # entry point for async programs
```
- `async def` marks a coroutine — must be awaited or run via `asyncio.run()`
- Lets I/O-bound work (API calls) run without blocking

### @classmethod vs instance method
```python
class Foo:
    def instance_method(self):    # receives object instance
        ...
    @classmethod
    def class_method(cls):        # receives the class itself
        ...
```
- Used in Pydantic validators because no instance exists yet at validation time

### **kwargs unpacking
```python
def greet(name, greeting="Hello"):
    print(f"{greeting}, {name}")

d = {"name": "Rajesh", "greeting": "Hi"}
greet(**d)   # same as greet(name="Rajesh", greeting="Hi")
```

### `in` operator — O(1) on dict/set, O(n) on list/tuple
Same keyword, very different cost. Complexity depends on the right-hand-side type.

| RHS type | What `x in container` does | Complexity |
|---|---|---|
| `list` / `tuple` | Walks the sequence element by element | **O(n)** |
| `set` | Hashes `x`, jumps to bucket, checks equality | **O(1) avg** |
| `dict` | Hashes `x`, jumps to bucket, checks **key** equality | **O(1) avg** |

This is why LeetCode two_sum is O(n), not O(n²):
```python
seen = {}                             # dict — hash table
for i, num in enumerate(nums):
    if target - num in seen:          # O(1) avg, NOT a scan
        return [seen[target - num], i]
    seen[num] = i
```
A dict lookup is not a search; it's `hash(key) → bucket index → direct probe`. Outer loop n × O(1) = O(n) total.

**Worst-case caveat:** dicts degrade to O(n) per call under pathological hash collisions (adversarial inputs). CPython's hash randomization (`PYTHONHASHSEED`) mitigates this. Interview answer: *"O(n) average, O(n²) worst case for dicts; accepted complexity for two_sum is O(n)."*

**Trap to avoid:** swapping `seen` for the original list flips the algorithm to O(n²) — `if target - num in nums:` walks the list every iteration.

---

## System Prompts

### What it is
A permanent instruction given to the LLM **before** the conversation starts. The user never sees it.
Sets persona, constraints, tool guidance, output format, and context for the entire session.

### Mental model
Like a job briefing you give an employee before their first day.
User messages are the work requests that come in after.

### Anthropic — separate `system` parameter
```python
client.messages.create(
    model="claude-opus-4-6",
    system="You are ToolBot, a helpful assistant...",  # ← separate param
    messages=[{"role": "user", "content": "..."}]
)
```

### OpenAI — inside messages list as role "system"
```python
client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are ToolBot..."},  # ← first message
        {"role": "user", "content": "..."}
    ]
)
```

### Gemini — passed in GenerateContentConfig
```python
client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents,
    config=types.GenerateContentConfig(
        system_instruction="You are ToolBot...",  # ← config param
        tools=TOOLS
    )
)
```

### What to put in a system prompt
| Purpose | Example |
|---|---|
| Persona | "You are a senior financial analyst" |
| Constraints | "Never discuss competitor products" |
| Tool guidance | "Always use the calculator tool for math, never compute yourself" |
| Output format | "Respond in bullet points, max 3 bullets" |
| Context | "You are helping Apple employees with internal IT issues" |

### Key gotcha — Anthropic vs OpenAI placement
- Anthropic: `system=` is a **separate top-level parameter**, not in messages list
- OpenAI: system prompt is `{"role": "system", ...}` as the **first item in messages**
- Gemini: `system_instruction=` inside `GenerateContentConfig`

---

## Context Management + Multi-Turn Memory

### The problem
If `messages = []` is created inside `run_agent()`, history resets on every call.
The agent has no memory of previous turns.

### The fix — lift messages to main()
```python
async def run_agent(user_message: str, messages: list) -> None:
    messages.append({"role": "user", "content": user_message})
    # ... rest of loop unchanged

async def main() -> None:
    messages = []   # lives here — persists across all turns
    while True:
        user_input = input("You: ")
        await run_agent(user_input, messages)
```

### Context window limits — simple truncation
```python
MAX_MESSAGES = 20

# After each run_agent call:
if len(messages) > MAX_MESSAGES:
    messages = messages[-MAX_MESSAGES:]  # keep most recent N messages
```

### Why truncation is tricky with tool loops
Tool calls add multiple messages per turn (user → assistant → tool_result → assistant).
Truncating mid-tool-call can corrupt the history.
Safe approach: truncate only after a full turn completes (after `end_turn`).

### Better strategies (for later projects)
| Strategy | How |
|---|---|
| Simple truncation | Keep last N messages (what we do in P1) |
| Token-budget trimming | LangGraph `trim_messages()` — respects token limits |
| Summarization | Use Claude Haiku to summarize old turns into one message |
| Sliding window | Keep system + first N + last M messages |

---

## Message History Pattern
```python
messages = [{"role": "user", "content": user_message}]

# After Claude responds:
messages.append({"role": "assistant", "content": response.content})

# After tool execution:
messages.append({"role": "user", "content": tool_results})
```
- Claude sees the full history on every API call — stateless API, stateful client
- Never mutate existing messages — always append

---

## Agentic Context Engineering — Stateless LLMs, the Harness, and Caching

### The core insight (the foundational interview answer)
- **LLMs are stateless.** Every API call is a fresh inference — there is no session inside the model.
- The illusion of continuity is **entirely engineered by the code around the LLM** — that code is *the harness* (or *the agent*).
- *"You are a stranger to me every call"* — the LLM sees only what the harness chose to put in the prompt.

### What is a "harness"?
The code that wraps the LLM and makes it useful. It:
1. Assembles the prompt (system + history + memory + user message)
2. Calls the LLM API
3. Parses the response → text vs. tool calls
4. **Executes** the tool calls (actually runs `Read`, `Bash`, `Grep`, …)
5. Feeds tool results back as the next message
6. Loops until the LLM stops calling tools
7. Manages cache breakpoints, compaction, subagents

| Harness | What it wraps |
|---|---|
| Claude Code CLI / VS Code extension | Claude + filesystem/shell/web tools |
| LangGraph (P3, P7) | A harness *you write* — the StateGraph IS the harness |
| CrewAI (P5) | Multi-agent harness — coordinates roles/tasks |
| MatchScout Stage 3 | The LangGraph state machine looping Claude over candidates |
| Cursor, Aider, Windsurf | Different harnesses around the same underlying LLMs |

> **Interview line:** *"The agent decides X"* is sloppy. Say *"the harness decides X"* or *"the LLM decides X via tool calls the harness exposes."* That distinction separates a LangChain user from an agent architect.

### The three context-management patterns
| Pattern | Who decides what to include | Example |
|---|---|---|
| **Agent decides deterministically** | Harness rules: last N turns + system prompt + CLAUDE.md | Sliding window, simple chatbots |
| **LLM decides via tools (agentic retrieval)** | LLM emits `search_memory` / `read_file` tool calls | Anthropic Memory tool, Mem0, Letta, Zep — *P9 frameworks* |
| **Hybrid (state of the art)** | Deterministic baseline + LLM retrieval + auto-compaction | Claude Code, modern agents |

### What Claude Code sends to the LLM every turn (concrete walkthrough)
The harness assembles, in order:
1. Tool definitions (Read, Bash, Edit, …)
2. System prompt (behavior rules)
3. Global `~/.claude/CLAUDE.md`
4. Project `CLAUDE.md`
5. `MEMORY.md` index + loaded memory files
6. Full conversation history (verbatim, every prior turn)
7. System reminders (git status, available skills, deferred tools)
8. Current user message

Plus three runtime mechanisms layered on top:
- **Tool-driven retrieval** — LLM calls `Read`/`Grep`/`Glob` only when it needs them (the LLM-decides path)
- **Automatic compaction** — near the window limit, older turns get summarized and replaced with the summary
- **Subagents** — each gets a fresh context window for its task; only the final summary returns to the parent

### Prompt caching — the economics
Without caching, an agentic loop re-sending 30K tokens × 20 turns = **600K** billed input tokens.
With caching: 30K (full price first time) + 19 × ~3K (cache reads) ≈ **87K** — **~7× cheaper**.

| Cache mechanic | Detail |
|---|---|
| Match basis | **Exact prefix match, byte for byte** |
| Cache write cost | ~125% of normal input (one-time populate) |
| Cache read cost | ~10% of normal input (90% discount) |
| TTL | 5 min default · 1 hour at higher cost |
| Scope | Per-org / per-API-key — **not shared across customers** |
| What's NOT cached | Current user message · current assistant response · anything after a divergence point in the prefix |
| What invalidates the cache | Any byte change in the prefix (e.g., editing CLAUDE.md mid-session nukes everything cached after that point) |

### The design principle (memorize this — it's the punchline)
> **Stable content first, volatile content last.**
>
> Order: tool defs → system prompt → CLAUDE.md → memory → history → current message.
>
> Stability = cache hits = cheap iteration. Volatile content at the start of the prefix kills caching for everything downstream.

### Interview phrasings to memorize
- *"LLMs are stateless; agents engineer the illusion of state via prompt assembly."*
- *"Context strategies trade recall vs. token cost vs. attention dilution (lost-in-the-middle)."*
- *"Agentic retrieval pushes the relevance decision to the LLM via tool calls."*
- *"Compaction is lossy summarization; RAG is lossy retrieval — different failure modes."*
- *"Prompt caching turned context engineering from a quality-only problem into a quality-AND-economics problem."*
- *"The harness decides; the LLM decides via tools the harness exposes."*

### Questions this prepares you for
- "How would you build memory for a long-running agent?"
- "Tradeoff between RAG and stuffing the context?"
- "Walk me through what happens when an agent's conversation exceeds the context window."
- "How does Claude Code know what context to send the model each turn?"
- "What changes when you turn on prompt caching?"
- "Where in your projects have you handled context management?" → P1 message-lift to `main()`, P3 LangGraph state, P7 MatchScout prompt assembly, P9 memory framework benchmark.

---

## Anthropic vs OpenAI — Side by Side

### Client setup
```python
# Anthropic
import anthropic
client = anthropic.Anthropic()

# OpenAI
from openai import OpenAI
client = OpenAI()
```

### Tool schema format
```python
# Anthropic
{
    "name": "get_weather",
    "description": "...",
    "input_schema": {           # ← key is "input_schema"
        "type": "object",
        "properties": { ... },
        "required": ["city"],
    }
}

# OpenAI
{
    "type": "function",         # ← extra wrapper
    "function": {
        "name": "get_weather",
        "description": "...",
        "parameters": {         # ← key is "parameters"
            "type": "object",
            "properties": { ... },
            "required": ["city"],
        }
    }
}
```

### API call
```python
# Anthropic
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    tools=TOOLS,
    messages=messages,
)

# OpenAI
response = client.chat.completions.create(
    model="gpt-4o",
    max_tokens=1024,
    tools=TOOLS,
    messages=messages,
)
```

### Streaming
```python
# Anthropic
with client.messages.stream(model=..., ...) as stream:
    for text in stream.text_stream:          # text_stream gives strings directly
        print(text, end="", flush=True)
    response = stream.get_final_message()    # ← get_final_message()

# OpenAI
with client.chat.completions.stream(model=..., ...) as stream:
    for event in stream:                     # yields typed events, not strings
        if event.type == "content.delta":
            print(event.delta, end="", flush=True)
    response = stream.get_final_completion() # ← get_final_completion()
```

### Stop/finish reason
```python
# Anthropic
response.stop_reason == "end_turn"    # done
response.stop_reason == "tool_use"    # wants tools

# OpenAI
response.choices[0].finish_reason == "stop"        # done
response.choices[0].finish_reason == "tool_calls"  # wants tools
```

### Accessing tool calls
```python
# Anthropic — iterate response.content blocks
for block in response.content:
    if block.type == "tool_use":
        name = block.name
        args = block.input          # already a dict
        id   = block.id

# OpenAI — iterate message.tool_calls
for tool_call in response.choices[0].message.tool_calls:
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)  # JSON string → dict
    id   = tool_call.id
```

### Feeding tool results back
```python
# Anthropic — single "user" message with list of results
messages.append({
    "role": "user",
    "content": [
        {"type": "tool_result", "tool_use_id": id, "content": result}
    ]
})

# OpenAI — one "tool" message per result
messages.append({"role": "assistant", "content": ..., "tool_calls": [...]})
messages.append({"role": "tool", "tool_call_id": id, "content": result})
```

### Accessing final text
```python
# Anthropic
for block in response.content:
    if hasattr(block, "text"):
        print(block.text)

# OpenAI
print(response.choices[0].message.content)
```

### Key gotcha — OpenAI streaming events
OpenAI's `stream()` context manager yields typed **event objects**, not raw text.
- `event.type == "content.delta"` → text chunk, access via `event.delta`
- `event.type == "chunk"` → raw chunk object, access via `event.chunk`
- Unlike Anthropic, there is no `text_stream` shortcut

---

## Gemini (google-genai SDK)

### Setup
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
```

### Tool definition — two approaches

**Option 1: Pass Python functions directly (new SDK feature)**
```python
TOOLS = [get_weather, calculator, get_time]
```
The SDK uses Python's `inspect` module to read:
- Function name → tool name
- Parameter names + type hints → schema
- Docstring → description (CRITICAL — without it Gemini guesses from name only)

**Option 2: Explicit schema (like Anthropic/OpenAI)**
```python
# Not needed with new SDK — use docstrings on functions instead
```

### Always add docstrings when passing functions as tools
```python
def get_time(timezone: str = "UTC") -> str:
    """Get the current date and time for a given timezone.

    Args:
        timezone: IANA timezone name e.g. 'America/New_York'. Defaults to UTC.
    """
```
Without a docstring, Gemini only knows the function name and parameter names.
It will guess — and guess wrong on ambiguous or complex tools.

### API call
```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents,           # list, managed manually (no chat session)
    config=types.GenerateContentConfig(tools=TOOLS)
)
```

### Detect function calls
```python
fn_calls = [p for p in response.candidates[0].content.parts
            if p.function_call and p.function_call.name]
```

### Function call fields
```python
name = part.function_call.name
args = dict(part.function_call.args)   # already a dict — no json.loads() needed
```

### Feed results back
```python
# append assistant response to history
contents.append(response.candidates[0].content)

# collect all tool results into one Content block
tool_results = []
for part in fn_calls:
    result = execute_tool(part.function_call.name, dict(part.function_call.args))
    tool_results.append(types.Part(
        function_response=types.FunctionResponse(
            name=part.function_call.name,
            response={"result": result}
        )
    ))

contents.append(types.Content(parts=tool_results, role="user"))
```

### Final text
```python
print(response.text)
```

### History management
Gemini new SDK has no chat session — you manage `contents` manually, same pattern as Anthropic/OpenAI `messages`.

### Streaming
Gemini streaming with tool calls is not straightforward — use non-streaming for tool loops, add streaming only for pure text responses.

### Current models (as of 2026-03-31)
| Model | Use case |
|---|---|
| `gemini-2.5-flash` | Best price/performance, function calling ✓ |
| `gemini-2.5-pro` | Most capable, complex reasoning |
| `gemini-2.5-flash-lite` | Fastest, most economical |

### Key gotcha — deprecated package
`google-generativeai` is fully deprecated. Use `google-genai`:
```bash
pip install google-genai
```
```python
from google import genai          # new
# NOT: import google.generativeai  # old, deprecated
```

---

## All Three LLMs — Tool Calling Comparison

| | Anthropic | OpenAI | Gemini |
|---|---|---|---|
| Tool args format | dict (`block.input`) | JSON string (`json.loads(...)`) | dict (`dict(part.function_call.args)`) |
| Tool result role | `"user"` | `"tool"` | `"user"` (as Content) |
| Stop signal | `stop_reason == "end_turn"` | `finish_reason == "stop"` | no fn_calls in parts |
| History | manual `messages` list | manual `messages` list | manual `contents` list |
| Streaming helper | `text_stream` (strings) | typed events (`event.type`) | non-trivial with tools |
| Tool schema | explicit JSON Schema | explicit JSON Schema | Python functions or explicit |

---

## Embeddings

### What an embedding is
A list of floats that represents a string's position in semantic space.
- Input: string
- Output: `list[float]` — 1536 numbers for `text-embedding-3-small`
- Vectors with similar meaning point in nearly the same direction

### OpenAI embedding API call
```python
response = client.embeddings.create(input=text, model="text-embedding-3-small")
vector = response.data[0].embedding   # list[float], length 1536
```

### Local embeddings (no API, no cost)
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")  # 384 dimensions
vector = model.encode("some text")   # runs on your machine
```
Use local when: cost matters, data is sensitive, or no internet.

### Embedding model comparison
| Model | Dims | Type | Cost |
|---|---|---|---|
| OpenAI `text-embedding-3-small` | 1536 | API | Per token |
| OpenAI `text-embedding-3-large` | 3072 | API | Per token |
| Google `text-embedding-004` | 768 | API | Per token |
| `all-MiniLM-L6-v2` | 384 | Local | Free |
| Anthropic Claude | — | N/A | **No embedding API** |

### Hard rule: never mix embedding models
You must use the same model for indexing AND querying. Different models produce vectors in incompatible spaces — mixing them makes cosine similarity scores meaningless.

```
✅  Index with text-embedding-3-small → query with text-embedding-3-small
❌  Index with text-embedding-3-small → query with all-MiniLM-L6-v2
```

### Cosine similarity
```python
def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(a[i] * b[i] for i in range(len(a)))
    mag_a = math.sqrt(sum(x**2 for x in a))
    mag_b = math.sqrt(sum(x**2 for x in b))
    return dot / (mag_a * mag_b)
```
- Measures **cos(θ)** — the angle between vectors, not distance. Direction encodes semantics; magnitude doesn't.
- **Range is [-1, +1]**, NOT [0, 1]. +1 same direction, 0 orthogonal, -1 opposite.
- Magnitude formula is **n-dimensional Pythagoras** — `sqrt(v₁² + v₂² + ... + vₙ²)`.
- In practice with modern dense embeddings (OpenAI text-embedding-3, Sentence-BERT), values almost always fall in **[0, 1]** — these models live in the positive cone of the hypersphere.

#### Practical score guide (modern embeddings)
| Range | Interpretation |
|---|---|
| 0.95–1.00 | Near-duplicates / paraphrases |
| 0.75–0.95 | Same topic, similar meaning (includes antonyms — they share topic) |
| 0.50–0.75 | Loosely related / same domain |
| 0.30–0.50 | Different topics, overlapping vocabulary |
| 0.00–0.30 | Unrelated |
| Negative | Rare with modern models; treat as definitely unrelated |

#### Antonym paradox (interview gotcha)
Antonyms do NOT come out at -1. "Today is hot" vs "today is cold" → cosine ≈ **0.85**, not -0.85. Reason: distributional hypothesis — antonyms share context (same sentence structure, same topic, same register), so the model embeds them close. Dense embeddings encode contextual co-occurrence, NOT logical polarity. For negation/antonym detection use an NLI model or fine-tuned classifier, not raw embedding cosine.

#### Cosine ↔ Euclidean equivalence (interview-defining fact)
For L2-normalized (unit-length) vectors:
```
|a - b|² = |a|² + |b|² - 2(a·b) = 1 + 1 - 2·cos(θ) = 2 - 2·cos(θ)
```
Euclidean distance is a **monotonic decreasing function of cosine** when vectors are unit-normalized → they're **rank-equivalent for retrieval**. Top-K by cosine = Top-K by Euclidean.

#### Production optimization: cosine → dot product
Pre-normalize every vector to unit length at insert time. Then `|a| = |b| = 1` and:
```
cos(θ) = (a · b) / (1 · 1) = a · b      # plain dot product
```
No sqrt, no division — SIMD-friendly. Every production vector DB (Qdrant, Pinecone, FAISS) does this internally when you select "cosine" distance.

**Bonus:** OpenAI `text-embedding-3-small/large` returns L2-normalized vectors by default. Cosine ≡ dot product out of the box — the `mag_a · mag_b` denominator in naive implementations is technically redundant.

#### Unit vector vs standard basis vector
Two different things both called "unit":
- **Unit vector** — length 1, ALL dimensions can be non-zero. E.g. `[3,4,0]` normalized is `[0.6, 0.8, 0]`. This is the one that matters for cosine.
- **Standard basis vector** — exactly one dimension = 1, rest are 0. E.g. `[1,0,0,...]`. A special case, not what "normalize a vector" means.

#### Why semantically related sentences cluster
**Distributional hypothesis** (Firth, 1957): "a word is known by the company it keeps." Training pushes vectors of contextually co-occurring tokens into similar directions. This is why "cat sat on mat" and "feline rested on rug" embed at ~0.65 despite zero word overlap — and also why antonyms paradoxically cluster.

---

## RAG (Retrieval Augmented Generation)

### What it solves
LLMs don't know your private documents and can't fit a 100-page PDF in a prompt. RAG retrieves the relevant parts first, then sends only those to the LLM.

### Two-phase pipeline
```
INDEXING (once):   document → chunk → embed each chunk → store in vector DB
QUERYING (per Q):  question → embed → find top-K similar chunks → LLM → answer
```

### Why chunks, not full documents
- Token limits on embedding APIs
- A small focused chunk scores higher similarity than a large unfocused one
- Precision: find 2–3 sentences that answer the question, not the whole document

### Chunk size tradeoff
| Smaller chunks | Larger chunks |
|---|---|
| More precise retrieval | More context per chunk |
| May lose surrounding context | May dilute the similarity score |
| More API calls to embed | Fewer chunks to manage |

Typical starting point: 2–5 sentences, or 256–512 tokens.

### Chunking strategy
Never embed full documents or individual sentences — embed *chunks* (3–10 sentences / 256–512 tokens).

| Granularity | Problem |
|---|---|
| Single sentences | Too little context — not self-contained |
| Full document | Answer gets diluted in averaged vector |
| **Chunks** | Self-contained + specific = high retrieval precision |

**Default starting point:** 256–512 tokens, 50-token overlap between chunks.

**Overlap matters:** consecutive chunks share 50 characters/tokens — so context at the end of one chunk is repeated at the start of the next. Answers that straddle a boundary aren't lost.

**Self-contained test:** read the chunk in isolation — would it make sense as a standalone answer?

**LangChain splitter:**
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_text(text)
```

### RAG vs fine-tuning
| | RAG | Fine-tuning |
|---|---|---|
| Updates knowledge | Add to vector DB | Retrain model |
| Cost | Embedding + retrieval | Expensive GPU training |
| Accuracy | Cites sources | Bakes in knowledge |
| Use when | Dynamic documents, Q&A | Style/behavior changes |

### LangChain + Qdrant RAG stack (used in DocTalk)

| Component | Package | Role |
|---|---|---|
| `PyPDFLoader` | `langchain-community` | Loads PDF → list of `Document` objects (one per page) |
| `RecursiveCharacterTextSplitter` | `langchain-text-splitters` | Splits pages into chunks |
| `OpenAIEmbeddings` | `langchain-openai` | Calls OpenAI API to convert text → 1536-float vector |
| `QdrantClient` | `qdrant-client` | Creates/manages in-memory vector store |
| `QdrantVectorStore` | `langchain-qdrant` | LangChain wrapper over Qdrant — add/search documents |

**LangChain's role:** orchestration + unified API. Actual vector storage and cosine math is Qdrant's job. LangChain lets you swap Qdrant for Pinecone by changing one line.

**In-memory Qdrant** (`QdrantClient(":memory:")`) — no API key, no server, runs in RAM. Only needs a key for Qdrant Cloud.

**`text-embedding-3-small`** — preferred OpenAI embedding model (better and cheaper than `ada-002`). Outputs 1536 dimensions → `VectorParams(size=1536, distance=Distance.COSINE)`.

### Full RAG pipeline with generation (doctalk.py pattern)

```python
# 1. Index
loader = PyPDFLoader("doc.pdf")
documents = loader.load()
chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(documents)
client = QdrantClient(":memory:")
client.create_collection("docs", vectors_config=VectorParams(size=1536, distance=Distance.COSINE))
embedding = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = QdrantVectorStore(client=client, collection_name="docs", embedding=embedding)
vector_store.add_documents(chunks)

# 2. Retrieve
results = vector_store.similarity_search_with_score(question, k=3)

# 3. Format context with citations
context = ""
for doc, score in results:
    context += f"[Page {doc.metadata.get('page','?')}, score: {score:.4f}]\n{doc.page_content}\n\n---\n\n"

# 4. Generate with Claude
response = anthropic.Anthropic().messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="Answer using only the context provided. Cite page numbers.",
    messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}]
)
print(response.content[0].text)
```

**Why cosine similarity is fast:** embedding is slow (neural network + API call, done once at index time). Cosine similarity is just a dot product on vectors already in RAM — milliseconds regardless of corpus size.

**Citation pattern:** page numbers come from `doc.metadata['page']` — injected into the context string so Claude can reference them in its answer.

---

## LLM Evaluation

### The eval-tier hierarchy
Use the highest tier you can afford given your problem.

| Tier | Method | When | Bias |
|---|---|---|---|
| 1 | **Outcome eval** | You can observe downstream success (sale, click, gig completion) | None — market is judge |
| 2 | **Human eval** | High-stakes, low volume | Disagreement among humans |
| 3 | **LLM-as-judge** | High volume, no outcome signal | 6 known biases (see below) |
| 4 | **Heuristic** | Format/citation/length checks | None but narrow |

### The 6 LLM-as-judge biases (memorize for interviews)

| # | Bias | Plain meaning | Fix |
|---|---|---|---|
| 1 | Position | Judge picks whichever response is shown first ~10-15% more often | Run both orderings, require agreement |
| 2 | Verbosity | Longer answer wins even when info-equivalent | Rubric scoring, not "which is better" |
| 3 | Self-preference | Claude-judge rates Claude output 10-25% higher | Cross-family judge (Claude generates → GPT judges) |
| 4 | Style | Markdown tables + formal tone beat casual prose with same content | Strip formatting before judging |
| 5 | Calibration drift | Judge model update → all scores shift | Pin judge version, treat as versioned dependency |
| 6 | Preference leakage | Same training family → up to 28.7% bias (ICLR 2026) | Cross-family, audit shared training data |

### Component vs system vs outcome eval (RAG)

```
Component (retrieval) → recall@k, precision@k against gold-labeled chunks
Component (generation) → faithfulness given fixed perfect context
System (end-to-end)   → full pipeline; what grade_answer() does
Outcome              → did user succeed? (MatchScout style)
```

When end-to-end regresses, you can't tell if retrieval or generation broke. Run component evals to localize.

### Golden dataset — the 7-step build

1. **Define the task as a contract** — what properties must hold? (factual grounding, citation correctness, refusal behavior)
2. **Sample inputs from production distribution** — buckets: 60% happy / 25% edge / 15% adversarial
3. **Humans write expected outputs** — domain experts, ~50-500 examples
4. **Pick storage form** (table below)
5. **Write deterministic grading function** — push as much grading from probabilistic (LLM-judge) to deterministic (field equality, regex)
6. **Wire into CI as non-gating job + dashboard** — track pass rate weekly, by bucket, by failure mode
7. **Maintain it** — gold sets rot in 6 months without ~10% maintenance budget

### Storage forms for "expected" output

| Form | Match | When |
|---|---|---|
| Exact string | `==` | Math, classification |
| Required substrings | `all(kw in output)` | Fact-bearing Q&A |
| Structured fields (JSON) | per-field equality | **Best general answer** |
| Reference text | cosine similarity ≥ threshold | Paraphrase-tolerant tasks |
| Rubric | LLM-judge against rubric | Open generation |

**Cosine-similarity caveat:** "Press for 2 seconds" vs "Press for 20 seconds" cosine ≈ 0.97. Numbers/negation/named-entities get averaged out. Bad for fact-precise Q&A; good for summary/style match.

### Structured output for grading

Don't grade prose — force JSON via tool_use, grade fields. Trivial, deterministic, no regex.

```python
tools = [{
    "name": "answer",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["press", "press_hold", "double_tap"]},
            "target": {"type": "string"},
            "duration_seconds": {"type": "number"},
            "natural_language_answer": {"type": "string"},
            "page_citations": {"type": "array", "items": {"type": "integer"}}
        },
        "required": ["action", "target", "page_citations"]
    }
}]
tool_choice = {"type": "tool", "name": "answer"}

# Grading collapses to:
fields_correct = sum(actual[k] == expected[k] for k in expected) / len(expected)
```

### Citation extraction (deterministic, no LLM-judge)

```python
import re
def extract_pages(model_output: str) -> set[int]:
    pattern = r"[Pp](?:age|p\.?)\.?\s*(\d+)(?:\s*[-–]\s*(\d+))?"
    pages = set()
    for m in re.finditer(pattern, model_output):
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else start
        pages.update(range(start, end + 1))
    return pages

# Use issubset — extra citations OK, missing not OK
citation_correct = set(expected).issubset(extract_pages(output))
```

Brittle without enforced format. Production move: structured output → `cited_pages: list[int]` field, no regex.

### Prompt iteration — 5 tiers

| Tier | Method | When |
|---|---|---|
| 1 | Manual loop — bucket failures, fix dominant bucket, re-measure | Baseline |
| 2 | Few-shot examples in prompt | Anchors format + refusal behavior; cheapest big lift |
| 3 | Structural: chain-of-thought, decomposition, output schema, negative constraints | Multi-hop, fact precision |
| 4 | Programmatic: **DSPy** (auto-optimize few-shots + instructions), **Promptfoo** (side-by-side A/B), **TextGrad** (gradient-like updates) | Manual plateaued |
| 5 | Versioned prompts + outcome A/B (MatchScout pattern) | Production with observable outcomes |

Fall back to fine-tuning only when all 5 plateau.

### Interview talking points

- *"Use the highest eval tier the problem allows — outcome > human > LLM-judge > heuristic — and don't pretend a lower tier is the higher one."*
- *"LLM-as-judge has 6 biases. The fixes don't eliminate them, they reduce them. Always pair with deterministic checks and human spot-checks."*
- *"For RAG, run component evals (retrieval recall@k, generation faithfulness with fixed context) and system eval. End-to-end alone can't localize regressions."*
- *"For grading, push everything you can from probabilistic to deterministic: structured output → field equality, citation regex, JSON schema, length bounds."*
- *"In MatchScout I chose outcome eval over LLM-judge — two-arm A/B, chi-squared significance — because gigs give observable success signal. LLM judges are dev-time tools, not release gates."*

---

## LangGraph

### What it is
A framework for building stateful multi-step agent workflows as directed graphs. Replaces LangChain's old Chains/agents API. Built on LangChain core.

### Core pattern
```
State (TypedDict) → flows through → Nodes (functions) → connected by → Edges
```

### Key concepts

| Concept | What it is |
|---|---|
| `StateGraph(Schema)` | Creates the graph. Argument is the state schema — NOT inheritance |
| `TypedDict` | Defines the shape of the shared state dict |
| Node | Plain Python function: takes full state, returns dict of changed fields only |
| Fixed edge | `add_edge("a", "b")` — always go from a to b |
| Conditional edge | `add_conditional_edges("a", router_fn)` — branch based on state |
| `set_entry_point()` | Which node runs first |
| `END` | Terminal constant — graph stops when an edge points here |
| `compile()` | Validates graph, returns a Runnable with `.invoke()` |

### State update rules
- Scalar fields (`str`, `int`) — **overwritten** when a node returns them
- List fields with `Annotated[list, operator.add]` — **appended** when a node returns them
- Fields not returned by a node — **unchanged**

```python
from typing import TypedDict, Annotated
import operator

class ResearchState(TypedDict):
    topic: str                                       # overwrite
    search_queries: Annotated[list[str], operator.add]   # append
    findings: Annotated[list[str], operator.add]         # append
    summary: str                                     # overwrite
```

### Node signature
```python
def my_node(state: ResearchState) -> dict:
    # read from state
    topic = state['topic']
    # return only what changed
    return {"search_queries": ["query1", "query2"]}
```

### State passing — immutability rule
Python passes dicts by object reference, so `state` inside a node *is* the live dict. But **never mutate it in place** — always return a delta:
```python
# CORRECT — return a delta dict
def generate_queries(state: ResearchState) -> dict:
    return {"search_queries": ["q1", "q2"]}

# WRONG — mutating in place
def generate_queries(state: ResearchState) -> dict:
    state["search_queries"] = ["q1", "q2"]  # breaks reducers, checkpointing, parallel nodes
    return {}
```
Why it breaks:
- **Reducers** (`operator.add`) never run — the merge step is bypassed
- **Checkpointing** — LangGraph saves state snapshots between nodes; in-place mutation corrupts them
- **Parallel branches** — two nodes running concurrently would race on the same dict

Mental model: treat state as **read-only inside a node**. Return only what changed. Same pattern as React's `setState`.

### Execution flow
```
invoke(initial_state)
    │
    ▼
Node 1 → reads state, returns partial update → LangGraph merges
    │
    ▼  (edge)
Node 2 → reads updated state, returns partial update → LangGraph merges
    │
    ▼  (edge)
Node 3 → reads updated state, returns partial update → LangGraph merges
    │
    ▼  (edge to END)
invoke() returns final state dict
```

### Conditional edges — routing
```python
def route_summary(state: ResearchState) -> str:
    if len(state['findings']) >= 11:
        return "detailed_summary"
    else:
        return "brief_summary"

# Without dict — router return values must match node names exactly
graph.add_conditional_edges("research", route_summary)

# With dict — translation layer (router returns readable strings, dict maps to node names)
graph.add_conditional_edges("research", route_summary, {
    "enough": "detailed_summary",
    "not_enough": "brief_summary"
})
# The dict is a lookup table — LangGraph reads it, not Python
```
- Router is pure logic — reads state, returns a string, no side effects
- Both terminal nodes need their own `add_edge(..., END)`

### Mermaid diagram
```python
print(app.get_graph().draw_mermaid())  # paste output into mermaid.live
```
- `-->` solid arrow = fixed edge
- `-.->` dashed arrow = conditional edge (decided at runtime by router)
- Shows graph shape only — condition logic inside router is NOT in the diagram
- Edge labels not auto-generated — edit raw Mermaid output by hand to add them

### LangGraph vs LangChain Chains
| | Chains | LangGraph |
|---|---|---|
| Structure | Linear only | Graph — branch + loop |
| State | Implicit | Explicit TypedDict |
| Human-in-the-loop | Awkward | Built-in |
| Checkpointing | No | Yes |

### "Runnable" — not a Python built-in
`Runnable` is a LangChain/LangGraph concept — any object with `.invoke()`. `graph.compile()` returns a Runnable. In plain Python the equivalent is any callable (object with `__call__`). LangGraph standardises on `.invoke()` as the interface.

---

### HITL — Checkpointing, update_state, and resume

**How it works:**
```python
# 1. Compile with checkpointer and interrupt point
checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer, interrupt_before=["human_review"])
config = {"configurable": {"thread_id": "1"}}

# 2. First invoke — runs until interrupt, saves checkpoint
app.invoke({"topic": "quantum computing"}, config)

# 3. Inject human input into the paused state
app.update_state(config, {"findings": [extra]})

# 4. Resume — picks up the updated checkpoint
app.invoke(None, config)
```

**Key mechanics:**
- `thread_id` is the checkpoint key — same thread_id = same conversation/run
- `interrupt_before=["node_name"]` — graph pauses BEFORE that node executes
- `app.update_state(config, {...})` — writes directly into the checkpoint; next resume sees updated state
- `app.invoke(None, config)` — `None` means "no new input, resume from checkpoint"
- `MemorySaver` stores checkpoints in memory; use `SqliteSaver` / `PostgresSaver` for persistence

**Annotated reducers + update_state:**
```python
findings: Annotated[list[str], operator.add]  # reducer = list concatenation
```
- `update_state(config, {"findings": [extra]})` → **appends** to existing list (reducer runs)
- Plain field with no reducer → **replaces** the value entirely
- The reducer determines whether update_state adds or overwrites

**Why this matters in interviews:**
HITL is how you build agents that pause for human approval before taking irreversible actions (sending emails, executing trades, deploying code). The checkpoint is the mechanism — not a callback, not a flag, but actual state persistence that survives process restarts.

---
---

## LangGraph — State Immutability Deep Dive

### Two valid patterns for returning state

**Pattern 1 — Immutable (create new dict):**
```python
def gather_data(state: AgentState) -> AgentState:
    price = get_price_data(state["ticker"])
    return {
        **state,              # spread all existing key-value pairs
        "price_data": price,  # override specific keys (last definition wins)
    }
```
- `**state` unpacks the dict into key=value pairs inside the new `{}`
- Creates a **brand new dict** — original state is untouched
- Safest for parallel branches sharing the same state object

**Pattern 2 — Mutable (modify in place):**
```python
def gather_data(state: AgentState) -> AgentState:
    state["price_data"] = get_price_data(state["ticker"])
    return state
```
- Modifies the **same dict** in memory (Python passes dicts by reference)
- Simpler and more readable
- Safe for linear graphs (nodes run one at a time)

**When to use which:**
| Situation | Pattern |
|-----------|---------|
| Linear graph, one node at a time | Either — use Pattern 2 for readability |
| Parallel branches sharing state | Pattern 1 (immutable) — prevents race conditions |
| Using `Annotated` reducers | Return a delta dict (not full state) |

---

## Python — `*` vs `**` Unpacking

| Operator | Used with | Meaning |
|----------|-----------|---------|
| `*`  | list / tuple | Unpack into positional arguments |
| `**` | dict | Unpack into keyword (key=value) arguments |

```python
# * unpacks a list into positional args
nums = [1, 2, 3]
print(*nums)           # same as print(1, 2, 3)

# ** unpacks a dict into keyword args
d = {"name": "Rajesh", "greeting": "Hi"}
greet(**d)             # same as greet(name="Rajesh", greeting="Hi")

# ** in a dict literal — spreads and overrides
base = {"a": 1, "b": 2, "c": 3}
merged = {**base, "b": 99}
print(merged)          # {"a": 1, "b": 99, "c": 3}  ← b is overridden
```

`**` is NOT a pointer (no relation to C/C++). It is Python-only syntax for dict spreading.

---

## Python — Pass by Reference vs Value

Python always passes objects (dicts, lists) **by reference**, not by value.

```python
def modify(state):
    state["key"] = "new_value"   # modifies the ORIGINAL dict
    return state

s = {"key": "old"}
modify(s)
print(s["key"])   # "new_value" — original was changed
```

- **By reference:** same object in memory — function modifies the caller's dict
- **By value (not Python):** would copy the dict — caller's dict unchanged
- Primitive types (`int`, `str`, `float`) behave like pass-by-value because they are immutable

---

---

## Multi-Tool Orchestration (P4 Pattern)

### Routing vs Orchestration
| | P3 Routing | P4 Orchestration |
|---|---|---|
| Tools called | One at a time, conditionally | All at once, always |
| Decision | "Should I search again?" | "Synthesize all results" |
| LLM role | Decides next step | Reasons over combined data |

### Pattern
```
User request
    → Call ALL tools (price, news, fundamentals, earnings)
    → Feed ALL results to Claude in one prompt
    → Claude returns structured recommendation
```

### Key design rule
Build domain tools first (pure Python, no LLM), wire them into the agent after. Tools do one thing well — the LLM synthesizes.

---

## Technical Indicators (Stock Analysis)

| Indicator | What it measures | Signal |
|-----------|-----------------|--------|
| RSI (14) | Momentum (0–100) | >70 overbought, <30 oversold |
| MACD | Trend direction | MACD > signal line = bullish |
| SMA50 | 50-day moving average | Support/resistance level |
| SMA200 | 200-day moving average | Long-term trend |
| Golden Cross | SMA50 > SMA200 | Bullish signal |

**Data window matters:** SMA200 needs ~200 trading days (~1 year). 3 months = ~60 days = SMA200 is null.

```python
import yfinance as yf
import pandas_ta as ta

tick = yf.Ticker("AAPL")
hist = tick.history(period="1y")   # need 1y for SMA200
rsi = hist.ta.rsi(length=14)
macd_df = hist.ta.macd()
sma_50 = hist.ta.sma(length=50)
sma_200 = hist.ta.sma(length=200)
```

---

## Sentiment Models — Domain Mismatch

**Problem:** General sentiment models trained on movie reviews score financial headlines incorrectly.

| Model | Trained on | Use for |
|-------|-----------|---------|
| `distilbert-sst-2` | Movie reviews | General text only |
| `ProsusAI/finbert` | Financial news | Stock/finance sentiment ✅ |

```python
# Production — use finbert
from transformers import pipeline
classifier = pipeline("sentiment-analysis", model="ProsusAI/finbert")
```

---

## Local Embeddings (sentence-transformers)

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")  # 384 dimensions, ~80MB, CPU-friendly
vector = model.encode("some text")   # returns numpy array of 384 floats
```

**vs OpenAI embeddings:**
| | sentence-transformers | OpenAI API |
|---|---|---|
| Cost | Free | Per token |
| Dimensions | 384 (MiniLM) | 1536 (text-embedding-3-small) |
| Offline | Yes | No |
| Quality | Good | Better |

---

## Chroma Vector Store (local)

```python
import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.Client()          # in-memory, no server needed
model = SentenceTransformer("all-MiniLM-L6-v2")

# Index
collection = client.create_collection("earnings")
embeddings = model.encode(chunks).tolist()
collection.add(documents=chunks, embeddings=embeddings, ids=["chunk_0", "chunk_1"])

# Query
query_embedding = model.encode(["What did management say about AI?"]).tolist()
results = collection.query(query_embeddings=query_embedding, n_results=3)
chunks = results["documents"][0]    # list of top-3 matching chunks
```

**Which chunks are returned:** cosine similarity between query vector and every stored chunk vector. Highest scores win. `n_results` caps the count.

---

## Structured Output with Pydantic (LLM responses)

Pattern: tell Claude to return JSON, parse + validate with Pydantic.

```python
class StockAnalysis(BaseModel):
    ticker: str
    recommendation: str    # "BUY" | "HOLD" | "SELL"
    confidence: str        # "HIGH" | "MEDIUM" | "LOW"
    reasoning: str

# Strip markdown fences Claude sometimes adds
raw = response.content[0].text.strip()
if raw.startswith("```"):
    raw = raw.split("```")[1]
    if raw.startswith("json"):
        raw = raw[4:]
    raw = raw.strip()

analysis = StockAnalysis(**json.loads(raw))   # parse + validate
```

**Gotcha:** Claude often wraps JSON in ` ```json ``` ` fences. Always strip before parsing.

---

## FastAPI — sync def vs async def

```python
# Use async def when you have real await calls
@app.post("/data")
async def get_data():
    result = await async_db_query()   # actual I/O await
    return result

# Use plain def for blocking calls — FastAPI runs in threadpool automatically
@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    result = agent.invoke(...)        # blocking call — no await
    return result
```

**Rule:** `async def` without any `await` inside is lying to FastAPI — it blocks the event loop on every request.

---

## async/await — How it works

```
Event Loop (one thread)
    ├── Coroutine A: hits await → pauses, hands control back
    ├── Coroutine B: runs now
    └── Coroutine A: response arrived → resumes
```

- `async def` — marks a coroutine (can be paused)
- `await` — pause here, let others run until this completes
- Only helps for **I/O-bound** work (network, DB, files)
- CPU-bound work (math, ML inference) — async does nothing, use threads/multiprocessing

**Global variable danger in async:**
```python
current_ticker = ""   # shared across ALL users

async def analyze(ticker: str):
    current_ticker = ticker           # User A sets "AAPL"
    result = await slow_api()         # yields here — User B sets "TSLA"
    return analyze(current_ticker)    # User A gets TSLA's data!

# Fix: always use local variables inside handlers
```

---

---

## CrewAI — Multi-Agent Teams (P5 ReviewCrew)

### The Agentic AI Stack

Three levels — you've worked at all of them:

| Level | Framework | What you define |
|-------|-----------|----------------|
| Low | Raw tool_use / function_calling | Every token of the LLM loop |
| Mid | LangGraph | Nodes, edges, typed state, routing |
| High | CrewAI | Agent roles, task goals, crew process |

CrewAI sits on top of LangGraph — in production they're often combined.

### Core Concepts

**Agent** — an AI worker with a role, goal, backstory, and tools:
```python
from crewai import Agent

reviewer = Agent(
    role="Senior Code Reviewer",
    goal="Find bugs, security issues, and bad patterns in code changes",
    backstory="You are an experienced engineer who has reviewed thousands of PRs.",
    tools=[github_tool],
    llm="claude-opus-4-6",
    verbose=True,
    allow_delegation=False   # True only for manager agents
)
```

**Task** — a specific job assigned to an agent:
```python
from crewai import Task

review_task = Task(
    description="Review the following PR diff: {pr_diff}",
    expected_output="Markdown list of issues with severity, file, line, explanation",
    agent=reviewer,
    context=[fetch_task],        # wait for this task, use its output
    output_pydantic=ReviewResult # optional: validate output
)
```

**Crew** — coordinates agents and tasks:
```python
from crewai import Crew, Process

crew = Crew(
    agents=[fetcher, reviewer, summarizer],
    tasks=[fetch_task, review_task, summary_task],
    process=Process.sequential,
    verbose=True
)
result = crew.kickoff(inputs={"pr_url": "https://github.com/org/repo/pull/42"})
print(result.raw)   # final output as string
```

### Process Modes

| Mode | How it works | When to use |
|------|-------------|-------------|
| `Process.sequential` | Tasks run one after another in order | Default; task A output feeds task B |
| `Process.parallel` | Independent tasks run simultaneously | Tasks don't depend on each other |
| `Process.hierarchical` | Manager agent delegates to others | Complex workflows with dynamic routing |

### CrewAI vs LangGraph

| | LangGraph | CrewAI |
|--|-----------|--------|
| Mental model | State machine — nodes and edges | Team — agents and tasks |
| Agent specialization | No — nodes are generic functions | Yes — role, goal, backstory per agent |
| Tool scoping | All tools everywhere | Each agent gets its own tools list |
| Parallelism | Manual (Annotated reducers) | Built-in `Process.parallel` |
| Best for | HITL, checkpointing, complex branching | Rapid multi-agent prototyping, parallel work |

### Output Passing with context=

```python
# CrewAI appends the output of fetch_task into review_task's prompt automatically
review_task = Task(
    description="Review the PR diff for bugs",
    agent=reviewer,
    context=[fetch_task]   # fetch_task must complete first; its output is injected here
)
```

### Custom Tool

```python
from crewai import tool

@tool("fetch_pr_diff")
def fetch_pr_diff(pr_url: str) -> str:
    """Fetches the diff for a GitHub pull request given its URL."""
    # ... implementation ...
    return diff_text
```

---

---

## CrewAI @tool Decorator — How It Works Internally

### Docstrings are real Python objects

```python
def fetch_pr_details(pr_url: str) -> str:
    """Fetches the title, description, changed files, and diff for a GitHub PR."""
    pass

print(fetch_pr_details.__doc__)          # "Fetches the title..."
print(fetch_pr_details.__annotations__)  # {'pr_url': str, 'return': str}
```

Docstrings are not comments — they are string objects stored on the function, readable at runtime via `.__doc__`.

### @tool replaces the function with a Tool object

```python
# This:
@tool("fetch_pr_details")
def fetch_pr_details(pr_url: str) -> str:
    """Fetches the title..."""
    return "..."

# Is equivalent to:
def fetch_pr_details(pr_url: str) -> str:
    """Fetches the title..."""
    return "..."
fetch_pr_details = tool("fetch_pr_details")(fetch_pr_details)
# Name now points to a Tool object — not the original function
```

Internally the Tool object does:
```python
self.description = func.__doc__           # from docstring
self.args_schema = func.__annotations__   # from type hints
self._func = func                         # stores original function

def run(self, input):
    return self._func(input)              # calls original body
```

### Execution sequence

```
Import time (once at startup):
  1. def statement runs → function object created, __doc__ populated
  2. @tool decorator runs → reads __doc__, builds Tool object
  3. Name rebound → "fetch_pr_details" now points to Tool object

Agent run time (every tool call):
  4. LLM decides to call the tool
  5. CrewAI calls fetch_pr_details.run(url)
  6. Tool.run() calls original function body
  7. Result returned to LLM
```

### How to call in tests vs agents

```python
fetch_pr_details.run(pr_url)    # correct — Tool object's .run() method
fetch_pr_details(pr_url)        # TypeError — Tool object is not callable directly
```

### vs P1 tool_use — same idea, different API

| | P1 Raw tool_use | P5 CrewAI @tool |
|--|----------------|-----------------|
| Tool description | Written manually as a dict | Read from docstring automatically |
| Input schema | Written manually as JSON schema | Read from type hints automatically |
| Tool call loop | You write it | CrewAI handles it |

---

---

## CrewAI Agent Internals — What an Agent Really Is

An Agent is a **configuration object that builds a system prompt** — not autonomous code. The LLM provides the intelligence; the agent configuration shapes how it responds.

```python
# What you write:
code_reviewer = Agent(
    role="Senior Code Reviewer",
    goal="Find bugs and bad patterns",
    backstory="15 years experience reviewing production code...",
    tools=[],
    llm="claude-opus-4-6"
)

# What CrewAI sends to the LLM:
"""
You are a Senior Code Reviewer.
Your goal is: Find bugs and bad patterns.
Background: 15 years experience...
Tools available: [none]
Task: [task description]
"""
```

### ReAct Loop — same as P1, just automated

```
Task assigned
    ↓
LLM: Thought → Action (tool call) → Observation (result) → repeat
    ↓ (until "Final Answer")
Task output returned to Crew
```

- Agent WITH tools: loops through Thought/Action/Observation
- Agent WITHOUT tools: single pass, Final Answer directly
- P1 difference: you wrote the loop manually; CrewAI handles it automatically

---

## Framework Comparison — CrewAI vs MCP vs LangChain vs LangGraph

| Problem | Framework | Used in |
|---------|-----------|---------|
| Coordinate multiple agents as a team | CrewAI | P5 ReviewCrew |
| Stateful graph workflows, HITL | LangGraph | P3, P4 |
| Chain LLM calls + RAG pipelines | LangChain (LCEL) | P2 DocTalk |
| Standardize tool exposure to LLMs | MCP | P6 (upcoming) |
| Direct LLM ↔ tool calls, no framework | Raw tool_use | P1 ToolBot |

### CrewAI vs MCP — completely different problems

| | CrewAI | MCP |
|--|--------|-----|
| What it is | Multi-agent orchestration | Protocol/standard for tool exposure |
| Solves | "Which agent does which task" | "How tools advertise to any LLM" |
| Analogy | Project manager organizing a team | USB standard — any plug, any port |
| Work together? | Yes — CrewAI agent can use MCP-exposed tool | |

**Mental model:** MCP = the plug standard. CrewAI = the team using the plugs.

### CrewAI vs LangChain

- **LangChain** — chains LLM calls + retrievals into pipelines (LCEL: `prompt | llm | parser`)
- **CrewAI** — coordinates multiple agents collaborating on a goal
- They're complementary — CrewAI can use LangChain retrievers internally

---

---

## CrewAI "Branching" — How It Really Works

**There is no real branching in CrewAI sequential mode. Every task always runs.**

### description vs role/goal/backstory

| | What it shapes | When used |
|--|----------------|-----------|
| `role` / `goal` / `backstory` | WHO the agent is — system prompt persona | Once, permanent |
| `description` | WHAT to do right now — task instruction | Per task, changes each task |

Full prompt = Agent identity (system) + Task description (user message) + context from prior tasks.

### The "conditional task" trick

```python
review_task = Task(
    description="""Review the diff.
    If HIGH severity issues found, say 'NEEDS_SECURITY_REVIEW'.
    Otherwise say 'READY_TO_MERGE'.""",
    agent=reviewer
)
security_task = Task(
    description="Only act if previous review said 'NEEDS_SECURITY_REVIEW'.",
    agent=security_specialist,
    context=[review_task]   # LLM reads review output and self-directs
)
```

**What actually happens:** `security_task` ALWAYS runs. The LLM reads the context and decides whether to act. You pay for the LLM call either way. This is not deterministic — it depends on the LLM following the instruction.

### Real branching — use LangGraph

```python
def route_after_review(state):
    if "NEEDS_SECURITY_REVIEW" in state["review_output"]:
        return "security_node"   # runs
    return "summary_node"        # security_node truly skipped — zero cost

graph.add_conditional_edges("review_node", route_after_review)
```

| | CrewAI "branching" | LangGraph conditional edges |
|--|-------------------|----------------------------|
| Skipped task truly skipped? | No — always runs | Yes — never executes |
| Routing done by | LLM following instructions | Your Python code |
| Cost | Pay for every task | Pay only for nodes that run |
| Reliability | Non-deterministic | Deterministic |

**Production pattern:** LangGraph for outer workflow routing → CrewAI crew as one node inside.

---

---

## CrewAI BaseTool vs @tool — Multi-Argument Tools

### The problem with @tool for multiple arguments

`@tool` auto-generates schema from docstring — gives LLM one text blob, no per-field descriptions. LLM may ignore arguments. Use `BaseTool` when you have 2+ arguments and need reliability.

### BaseTool pattern

```python
from crewai.tools import BaseTool      # CrewAI
from pydantic import BaseModel, Field  # Pydantic

class PostCommentInput(BaseModel):
    pr_url: str = Field(description="The full GitHub PR URL")
    comment: str = Field(description="The full markdown text to post as a comment")

class PostPRCommentTool(BaseTool):
    name: str = "post_pr_comment"
    description: str = "Posts a comment on a GitHub PR. Requires pr_url and comment."
    args_schema: type[BaseModel] = PostCommentInput   # explicit schema

    def _run(self, pr_url: str, comment: str) -> str:
        # actual implementation
        ...

post_pr_comment = PostPRCommentTool()   # instantiate — used as tools=[post_pr_comment]
```

### What the LLM sees — @tool vs BaseTool

```
@tool (blob):          {"name": "...", "description": "Input: pr_url, comment..."}

BaseTool (per-field):  {"name": "...", "description": "...",
                        "parameters": {
                          "pr_url":  {"type": "string", "description": "The full GitHub PR URL"},
                          "comment": {"type": "string", "description": "The full markdown text..."}
                        },
                        "required": ["pr_url", "comment"]}
```

### Where each comes from

| | Package | What it provides |
|--|---------|-----------------|
| `BaseTool` | `crewai.tools` | Base class — tool interface CrewAI expects |
| `BaseModel` | `pydantic` | Data model — validation + schema generation |
| `Field` | `pydantic` | Per-field metadata — description, constraints |

CrewAI depends on Pydantic internally — all Agent, Task, Crew objects are Pydantic models. Mixing them is intentional.

### When to use each

| Situation | Use |
|-----------|-----|
| Single argument tool | `@tool` decorator — simpler |
| Multiple arguments, LLM must pass all | `BaseTool` — explicit per-field schema |
| Need validation constraints (min, max, regex) | `BaseTool` with `Field(...)` |

---

*Last updated: 2026-04-26 — P5 ReviewCrew: BaseTool vs @tool, Pydantic Field schema, multi-argument tool reliability*

---

## MCP (Model Context Protocol) — P6

### The 3 primitives
| Primitive | Server defines | Client calls | Purpose |
|---|---|---|---|
| **Tools** | `@mcp.tool()` | `session.call_tool(name, input)` | LLM-driven actions |
| **Resources** | `@mcp.resource("uri")` or `@mcp.resource("uri/{param}")` | `session.list_resources()` (static) or `list_resource_templates()` (dynamic) | Browsable context for generic clients (Claude Desktop) |
| **Prompts** | `@mcp.prompt()` returns `str` | `session.get_prompt(name, args)` | Reusable system/user prompts served by MCP |

### FastMCP gotchas
- `host`/`port` go on `FastMCP("name", host=..., port=...)` constructor, NOT `.run()`
- Transport: `mcp.run(transport="streamable-http")` — endpoint is `/mcp`, NOT `/sse`
- Dynamic resources with `{param}` in URI → use `list_resource_templates()`, NOT `list_resources()`
- Prompt template MUST return plain `str` — returning explicit `list[PromptMessage]` causes double-wrapping

### MCP role spec
- Roles in messages are fixed by spec: `"user"` or `"assistant"` only
- No `"system"` role exists in MCP — system prompt lives at the LLM API call level (client controls it)

### Generic agentic loop pattern (works for ANY MCP server)
```python
async with streamablehttp_client(url) as (r, w, _):
    async with ClientSession(r, w) as session:
        await session.initialize()

        # Discover schemas — no hardcoding
        tools = await session.list_tools()
        claude_tools = [{"name": t.name, "description": t.description,
                         "input_schema": t.inputSchema} for t in tools.tools]

        messages = [{"role": "user", "content": prompt}]
        while True:
            r = client.messages.create(model=..., tools=claude_tools, messages=messages)
            if r.stop_reason == "end_turn": break
            messages.append({"role": "assistant", "content": r.content})
            tool_results = []
            for block in r.content:
                if block.type == "tool_use":
                    result = await session.call_tool(block.name, block.input)  # generic dispatch
                    tool_results.append({"type": "tool_result",
                                         "tool_use_id": block.id,
                                         "content": result.content[0].text})
            messages.append({"role": "user", "content": tool_results})
```

### Why Resources exist when Tools could do the same job
Functionally identical. The distinction is **UI semantics in generic clients**:
- Claude Desktop renders Resources as browsable/attachable items (paperclip icon)
- Tools are invisible to the user — only LLM sees them
- Choose Resource for "data the user might browse/attach", Tool for "action the LLM should take"

### MCP architecture (5-phase tool call lifecycle)
1. Client calls `list_tools()` → gets schemas from server
2. Client passes schemas to LLM as `tools=[...]`
3. LLM responds with `stop_reason="tool_use"` and tool_use blocks
4. Client dispatches each block via `session.call_tool(name, input)`
5. Tool result appended as `"user"` role; loop continues until `stop_reason="end_turn"`

### Chroma persistence pattern
```python
from pathlib import Path
import chromadb

# Bad: relative path, depends on CWD
_chroma_client = chromadb.Client()  # ephemeral — lost on restart

# Good: absolute, co-located with code
_chroma_client = chromadb.PersistentClient(
    path=str(Path(__file__).parent / "data" / "chroma_db")
)
```
Files only created when a collection is actually written, not when client is constructed.

---

## Curriculum v6 — Eval, Production & Framework Comparison (added 2026-04-29)

### Eval frameworks (P7 expanded)
| Tool | What it tests | Example metric |
|---|---|---|
| **Ragas** | RAG-specific quality | Context precision, faithfulness, answer relevancy |
| **DeepEval** | LLM unit tests | `assert_relevancy(output, query, threshold=0.8)` |
| **Promptfoo** | A/B prompt testing | Run same input through 5 prompt variants, score each |
| **LangSmith** | Tracing + dataset evals | Span hierarchy, evaluator functions |
| **LangFuse** | Open-source observability | Self-hosted dashboards, cost tracking |

### Production reliability patterns (P10 expanded)
- **Retry**: `tenacity` — exponential backoff with jitter, retry on 429/5xx only
- **Circuit breaker**: `pybreaker` — open after N failures, recover after timeout
- **Provider fallback**: Claude → GPT-4o on rate limit / outage (unified abstraction)
- **Cost tracking**: log input + output tokens per request, calculate USD by provider
- **Multi-cloud LLM routing**: AWS Bedrock (Claude) + Azure OpenAI (GPT-4o) + GCP Vertex (Gemini)

### Framework decision matrix (P12 NEW)
| Need | Best framework |
|---|---|
| Stateful workflow with branches/loops | **LangGraph** |
| Role-based multi-agent collaboration | **CrewAI** |
| Conversational multi-agent debate | **AutoGen** |
| Single LLM with tools (no orchestration) | Raw Anthropic SDK |

---

*Last updated: 2026-04-29 — P6 MCP complete; v6 curriculum (P7+P10 expanded, NEW P12); eval frameworks; reliability patterns; framework comparison*

---

## Decorators (#69 Section 4)

### Mental model
A decorator is **a function that takes a function and returns a (usually wrapped) function**. The `@` is sugar for `func = decorator(func)`.

```python
@my_decorator
def greet(): ...

# Identical to:
def greet(): ...
greet = my_decorator(greet)
```

Decorators are closures with a specific shape — the wrapper "captures" the original function via closure.

### Basic 2-layer pattern (no config)
```python
from functools import wraps

def loud(func):
    @wraps(func)                          # always include
    def wrapper(*args, **kwargs):
        print(">>> calling")
        result = func(*args, **kwargs)
        print("<<< done")
        return result
    return wrapper

@loud
def add(x, y): return x + y
```

### 3-layer pattern (with config — `@retry(max_attempts=3)`)
```python
def retry(max_attempts):              # LAYER 1: receives config
    def decorator(func):              # LAYER 2: receives the function
        @wraps(func)
        def wrapper(*args, **kwargs): # LAYER 3: runs at call time
            for _ in range(max_attempts):
                try: return func(*args, **kwargs)
                except Exception: continue
            raise
        return wrapper
    return decorator

@retry(max_attempts=3)
def call_llm(prompt): ...
```

| Layer | Receives | Runs |
|---|---|---|
| 1 | Config | Once at decoration |
| 2 | Function | Immediately after layer 1 |
| 3 | Call args | Every call |

### Why config goes in layer 1, not the wrapper
If `max_attempts` were a wrapper parameter, every caller would pass it: `call_llm("Hi", max_attempts=3)`. The wrapper's signature must match the original's so callers don't know about decoration. Outer layer captures config via closure.

### Always use `@functools.wraps(func)`
Without it, `func.__name__`, `__doc__`, `__module__` show wrapper's info — breaks debuggers, FastAPI, Pydantic.

### Stacking — order is bottom-up
```python
@upper          # outer — runs LAST on result
@exclaim        # inner — runs FIRST on result
def greet(name): ...

# Equivalent to: greet = upper(exclaim(greet))
```

### Registry pattern (how MCP/CrewAI/FastAPI work)
```python
TOOLS = {}

def tool(name):
    def decorator(func):
        TOOLS[name] = func              # ← side effect: register
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

@tool("get_price")
def get_stock_price(ticker): ...
```

Decoration runs at module load → builds the registry. Use cases: `@mcp.tool()`, `@app.post("/path")`, `@tool` (CrewAI).

### Common builtins to know
| Decorator | What it does |
|---|---|
| `@staticmethod` | No self/cls binding |
| `@classmethod` | Auto-pass cls |
| `@property` | Method that looks like attribute |
| `@functools.cache` / `@lru_cache` | Memoize |
| `@dataclass` | Auto-generate `__init__`/`__repr__`/`__eq__` |
| `@abstractmethod` | Mark required-to-override |

### Top gotchas
- **Forgetting parens** on parameterized decorators: `@retry` passes the function as `max_attempts`. Always `@retry()` or `@retry(...)`.
- **Forgetting `@wraps`** breaks introspection.
- **Decoration runs at module load**, not per call. Wrapper runs per call.

---

*Last updated: 2026-04-30 — Section 4 (Decorators) complete: 3-layer pattern, @wraps, registry pattern (MCP/CrewAI), common builtins*

---

## async / await (#69 Section 6)

### Mental model
Single-threaded cooperative concurrency. `await` yields control to OTHER coroutines on the same event loop, NOT to other threads. The event loop runs on ONE thread, juggling coroutines at `await` points.

This is why FastMCP/uvicorn can serve thousands of concurrent connections on one thread — each is a coroutine, OS multiplexes I/O via epoll/kqueue.

### 5 essential patterns
| Pattern | Use |
|---|---|
| `asyncio.run(main())` | Top-level entry point — runs main() ONCE |
| `await coro()` | Sequential — wait for one |
| `await asyncio.gather(*coros)` | Concurrent — fan out independent calls |
| `asyncio.create_task(coro())` | Fire-and-forget background work |
| `async with` / `async for` | Async resources / iterators (MCP sessions, LLM streams) |

### Sequential vs concurrent
```python
# Sequential — 3s total
for t in tickers:
    result = await fetch(t)

# Concurrent — ~1s total
results = await asyncio.gather(*[fetch(t) for t in tickers])
```

### When async helps
- Server with many clients (each a coroutine)
- Multiple coroutines coexisting (background tasks during awaits)
- Async-only libraries (MCP, httpx, asyncpg)
- Cancellation/timeouts via `asyncio.timeout(s)`

### When async DOESN'T help
- Standalone script with one linear flow, no concurrency
- CPU-bound work (use threads/processes via `asyncio.to_thread`)

### Top gotchas
- Forgetting `await` → returns coroutine OBJECT, not result
- `time.sleep()` in async → blocks the entire event loop
- Use `await asyncio.to_thread(blocking_fn, args)` to bridge sync code

---

## Pydantic Essentials (#69 Section 7)

### What it does
Runtime validation + serialization based on type hints. Used by every AI/web framework (Anthropic, OpenAI, FastAPI, MCP, LangChain, CrewAI).

### Define model
```python
from pydantic import BaseModel, Field

class Stock(BaseModel):
    ticker: str = Field(min_length=1, max_length=5, description="Ticker symbol")
    price: float = Field(gt=0)
    quantity: int = Field(ge=0, default=0)
```

`ticker`/`price` are INSTANCE fields (not class variables). Pydantic's metaclass reads `__annotations__` and generates `__init__` that validates + creates per-instance attributes.

### Three ways to create
| Input | Method |
|---|---|
| Python literals | `Stock(ticker="AAPL", price=150)` |
| dict | `Stock.model_validate(data)` |
| JSON string | `Stock.model_validate_json(json_str)` |

All return the same kind of validated instance. `model_validate` and `model_validate_json` are inherited from BaseModel automatically.

### Serialize
```python
s.model_dump()        # → dict
s.model_dump_json()   # → JSON string
```

### Optional field patterns (4 combinations)
| Annotation | None allowed? | Required? |
|---|---|---|
| `price: float` | ❌ | ✅ |
| `price: float = 0.0` | ❌ | ❌ (defaults to 0.0) |
| `price: Optional[float]` | ✅ | ✅ (must explicitly pass) |
| `price: Optional[float] = None` | ✅ | ❌ (defaults to None) |

`Optional[X]` means TYPE allows None — NOT that the field is skippable. To make it skippable you need a default.

### Field() — constraints + metadata
```python
Field(gt=0, le=100)           # numeric range
Field(min_length=1, max_length=50)
Field(pattern=r"^[A-Z]+$")
Field(description="...")       # CRITICAL — becomes part of LLM-visible JSON schema
Field(default_factory=list)    # for mutable defaults
```

`description` is prompt engineering for the LLM — included in the schema sent to Claude/GPT.

### Custom validators
```python
@field_validator("ticker")
@classmethod                              # always include in v2
def ticker_uppercase(cls, v):
    if not v.isupper():
        raise ValueError("Must be uppercase")
    return v
```

### Tool input schemas (the agentic AI killer pattern)
A complete tool def has 3 parts. Pydantic generates only the third:

```python
tool = {
    "name": "get_stock_price",                       # YOU
    "description": "Get current price of a stock",   # YOU
    "input_schema": GetPriceInput.model_json_schema()  # PYDANTIC
}
```

Frameworks like `@mcp.tool()` assemble all three from a decorated function automatically.

### When to use Pydantic vs alternatives
| Use case | Tool |
|---|---|
| External boundary (LLM tools, API requests, config files) | Pydantic BaseModel |
| Internal data containers, no validation needed | `@dataclass` |
| Behavior-heavy classes (engines, orchestrators) | Plain class |

### Pydantic v1 → v2 method renames (if you see old code)
| v1 | v2 |
|---|---|
| `parse_obj(d)` | `model_validate(d)` |
| `parse_raw(s)` | `model_validate_json(s)` |
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `.schema()` | `.model_json_schema()` |
| `validator()` | `field_validator()` |

---

## Python Packaging & Distribution (PyPI, pip, venv) — added 2026-05-31

**PyPI (Python Package Index)** — `pypi.org`, the official **public repository of Python packages**. `pip install X` downloads X from here. It's a single global namespace, so every package name must be unique (like the npm registry, but for Python). Checking if a name is "free on PyPI" = checking if that package name is unclaimed.

| Term | One-liner |
|---|---|
| **PyPI** | The public index `pip` installs from (`pypi.org`). Global, unique package names. |
| **pip** | Python's package installer — resolves + installs from PyPI (or another index). |
| **venv** | Per-project isolated environment so deps don't collide: `python -m venv .venv && source .venv/bin/activate`. |
| **sdist** | Source distribution (a `.tar.gz`); built on the user's machine at install time. |
| **wheel** (`.whl`) | Pre-built binary distribution — no build step, faster install. `pip` prefers wheels. |
| **pyproject.toml** | Modern build/metadata manifest (PEP 517/518/621): name, deps, **extras**, build backend. |
| **extras** | Optional dependency groups: `pip install "pkg[dev]"` → installs the `dev` extra. |
| **editable install** | `pip install -e .` — links the package to your source so edits take effect with no reinstall (dev workflow). |
| **TestPyPI** | A separate sandbox index (`test.pypi.org`) for rehearsing a release. |

**Publishing flow:** `python -m build` (creates sdist + wheel) → `twine upload dist/*` (uploads to PyPI; needs a unique name + API token). Rehearse on **TestPyPI** first.

**Related tooling:** `conda` (alt package + env manager, science-heavy) · `uv` / `poetry` / `pip-tools` (faster installs, lockfiles) · `requirements.txt` (pinned dep list).

**Interview soundbite:** *"PyPI is to `pip` what the npm registry is to `npm` — the central place packages are published to and installed from. You isolate per project with a venv, declare deps in `pyproject.toml`, install your own package editable with `pip install -e .` during dev, and publish with `build` + `twine`."*

---

*Last updated: 2026-05-31 — added Python Packaging & Distribution (PyPI/pip/venv). Prior: Sections 6 (async/await) and 7 (Pydantic) complete; #69 Python Fundamentals DONE.*
