# Recovery Checklist — Laptop Migration via Time Machine

**Snapshot date:** 2026-07-01
**Reason:** Old laptop broke; restoring on new laptop via Time Machine.

This file lives IN THE GIT REPO on GitHub, so it's accessible even if Time Machine restore fails. Follow it top-to-bottom on the new laptop to verify everything came back correctly.

---

## Phase 1 — What GitHub has (safe if Time Machine fails)

All of these are pushed to `https://github.com/Agentic-and-AI-Engineering-Projects/ai_engineer_program`:

- All curriculum code (p1_toolbot through p14_managed_agents placeholders)
- All advanced_patterns/ code and HTMLs
- CLAUDE.md
- plan.txt
- Build scripts referenced from /tmp
- P2 Pinecone variant + P2.5 Bedrock primer
- The full master guide source files (kubernetes_primer.html, bedrock_primer.html, vector_db_primer.html, kafka_primer.html, aws_services_primer.html, interview_questions_bank.html, orchestration_patterns_overview.html)

**Latest commit at snapshot time:** `861ef73` (docs: CLAUDE.md — P5 revision started 2026-07-01)

Other repos also on GitHub:
- **ATAF:** `https://github.com/ATAFramework/ataf` (~4,300 LOC, 71 tests, all pushed)
- **HPRC:** repo under `HPRCFramework` GitHub org
- **Onemyle-matchscout:** `https://github.com/Agentic-and-AI-Engineering-Projects/Onemyle-matchscout` (4 PM artifact files were untracked at snapshot — not critical)
- **Onemyle User Chatbot:** separate repo

---

## Phase 2 — What ONLY Time Machine has (must-verify on new laptop)

These files are **local-only** (gitignored or outside repos). Time Machine restore MUST bring these back:

### 2a. Interview prep + master guide artifacts (in `~/ai/ai_engineer_program/`)

| File | Size at snapshot | Notes |
|---|---:|---|
| `AGENTIC_AI_MASTER_GUIDE.html` | 1.16 MB | 14 appendices A–N; rebuildable from source files via `/tmp/build_master_guide.py` |
| `INTERVIEW_STUDY_GUIDE.html` | 379 KB | P1–P3 revision notes patched in |
| `JOB_SEARCH_PREP_PLAN.html` | 34 KB | |
| `APPLE_ASE_PMO_PM_INTERVIEW_PREP.html` | 35 KB | Regeneratable from `~/.claude/projects/.../memory/project_apple_ase_pmo_pm_interview.md` |
| `.env` | 662 bytes | Contains OPENAI, ANTHROPIC, GOOGLE, GEMINI, NEWSAPI, GITHUB, PINECONE keys |
| `Mavic_2_Pro_Zoom_User_Manual_v20_en.pdf` | 22 MB | Test corpus for Pinecone / Qdrant / Chroma variants |
| All `RESUME_*.md`, `RESUME_*.docx`, `RESUME_*.pdf` | varies | 9 tailored resumes across 3 tracks + master version |
| All `COVER_LETTER_*.md/docx/pdf` | varies | Per-application cover letters |

### 2b. Claude memory (crucial — this holds session context)

Directory: `~/.claude/projects/-Users-rajeshramani-ai-ai-engineer-program/memory/`

**~38 memory files at snapshot.** Key ones (read these first in a new Claude session):

- `MEMORY.md` — the index; read first
- `project_p5_revision_2026_07_01.md` — current position; where the queue picks up
- `project_agentic_depth_strategy_2026_06_26.md` — Tier 1/2/3 AI depth strategy
- `project_curriculum_reorder_2026_06_25.md` — locked queue order
- `project_ataf_framework.md` — ATAF v0.1 server complete
- `project_hprc_framework.md` — HPRC portfolio piece
- `project_resume_summary_batch_2026_06.md` — locked profile summary (ATAF + HPRC)
- `project_resume_summary_infra_track.md` — DC/TPM infra summary override
- `project_resume_3_tracks.md` — per-track inclusion rules
- `project_apple_ase_pmo_pm_interview.md` — Apple ASE PMO interview prep (strongest fit)
- `project_apple_agentic_ai_pm_interview.md` — Apple Agentic AI PM prep
- `project_oracle_oci_swat_tpm_application.md` — Oracle OCI SWAT prep
- `project_oracle_sr_principal_tpm_2026_06_26.md` — Oracle Sr Principal TPM prep
- 10 feedback_*.md files with user preferences (code style, comment style, revision workflow, etc.)

### 2c. AWS credentials (`~/.aws/`)

- `~/.aws/credentials` — access key + secret for IAM user AI_ENGINEER_PROGRAM in account 580779787774
- `~/.aws/config` — default region us-east-1
- Verify with: `aws sts get-caller-identity` after Time Machine restore

### 2d. Local server .144 GPU box (external to this laptop, still fine)

- The Onemyle Chatbot orchestrator runs at 192.168.1.144 (RAM repaired 2026-06-23)
- The k3s cluster runs at 192.168.1.156
- Both external — laptop broken doesn't affect them

---

## Phase 3 — Verification steps on new laptop (in order)

Once Time Machine restore completes, run these checks:

### Step 1 — Repo intact
```bash
cd ~/ai/ai_engineer_program
git status
git log --oneline -5      # should show 861ef73 as most recent
```

### Step 2 — Venv works
```bash
source .venv/bin/activate
python -c "import anthropic, openai, boto3, langchain, langgraph, pinecone; print('all imports OK')"
```

If venv is corrupted, rebuild:
```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # or reinstall the key packages
```

### Step 3 — API keys work
```bash
grep -c "=" .env    # should be at least 7 (OPENAI, ANTHROPIC, GOOGLE, GEMINI, NEWSAPI, GITHUB, PINECONE)
aws sts get-caller-identity    # should return your IAM user ARN
```

### Step 4 — Claude memory intact
```bash
ls ~/.claude/projects/-Users-rajeshramani-ai-ai-engineer-program/memory/ | wc -l    # should be ~38 files
cat ~/.claude/projects/-Users-rajeshramani-ai-ai-engineer-program/memory/MEMORY.md | head -10
```

### Step 5 — Master guide loads
```bash
open ~/ai/ai_engineer_program/AGENTIC_AI_MASTER_GUIDE.html
# Should render with sidebar navigation. If missing, rebuild:
# python3 /tmp/build_master_guide.py
```

### Step 6 — Interview prep intact
```bash
open ~/ai/ai_engineer_program/APPLE_ASE_PMO_PM_INTERVIEW_PREP.html
# Should show the dark banner + Q1-Q12 answers
```

### Step 7 — External services still reachable
```bash
ping -c 3 192.168.1.144    # GPU box (Onemyle chatbot orchestrator)
ping -c 3 192.168.1.156    # k3s cluster (Kanban, Kafka, MongoDB)
sshpass -p 'yanni123' ssh rajramani@192.168.1.144 "echo ok"    # if needed
```

---

## Phase 4 — Resume the work

**Current position** (per `project_p5_revision_2026_07_01.md`):

- P2 Pinecone variant — ✅ done (2026-06-29)
- P2.5 Bedrock primer — ✅ done (2026-07-01)
- **P5 ReviewCrew revision — IN PROGRESS**
  - All 3 orchestration modes now in `p5_reviewcrew/` (`crew.py`, `crew_parallel.py`, `crew_hierarchical.py`)
  - Awaiting Phase A on Concept 1 (Agent/Task/Crew abstractions)

**To resume in a new Claude session:**

1. Open `~/ai/ai_engineer_program/` in your editor
2. Start Claude Code
3. Say: **"resume normal programming — kick off Phase A on P5 Concept 1"**

Claude will read the memory files (auto-loaded from `~/.claude/projects/.../memory/`), see the current position, and drop the Phase A questions.

---

## Phase 5 — If Time Machine restore fails partially

Fallback rebuild instructions for the local-only files:

### Rebuild the master guide
```bash
python3 /tmp/build_master_guide.py    # if /tmp/build_master_guide.py exists
# If /tmp is empty, download the script from an earlier Claude session's transcript,
# OR reconstruct by joining the source primer HTMLs in advanced_patterns/
```

### Rebuild the Apple ASE PMO prep HTML
```bash
# Content lives in the memory file — regenerate via pandoc + Python wrapper
# The exact rebuild command is in the Claude conversation history from 2026-06-30
```

### Recreate the .env
Regenerate keys individually from each provider's console:
- Anthropic: https://console.anthropic.com/settings/keys
- OpenAI: https://platform.openai.com/api-keys
- Pinecone: https://app.pinecone.io → API Keys
- Google/Gemini: https://ai.google.dev/
- GitHub: https://github.com/settings/tokens

### Recreate AWS credentials
1. Sign in to https://console.aws.amazon.com (account 580779787774)
2. IAM → Users → AI_ENGINEER_PROGRAM → Security credentials → Create access key
3. `aws configure` with the new key

---

## Snapshot summary at 2026-07-01

- **Master guide:** 1.16 MB, 14 appendices (A–N)
- **P2 Pinecone variant:** shipped
- **P2.5 Bedrock primer:** shipped (Bedrock 12.2s vs Direct 15.2s captured in Appendix L §10.5)
- **P5 revision:** in progress, all 3 CrewAI modes consolidated
- **Active job apps:** 8 (Apple ASE PMO is strongest fit)
- **Standing rule:** recruiter response → drop revision work, load application prep memory, start mocking

Good luck with the migration. See you on the other side.
