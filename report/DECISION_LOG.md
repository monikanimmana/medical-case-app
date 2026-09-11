# Decision Log

**Format**: Key decisions and rationale, updated after each phase.

To be populated with 10-15 non-obvious choices:
- Brand selection rationale
- Clustering parameters (k, algorithm)
- Taxonomy design decisions
- Classifier architecture choices
- Retrieval strategy
- Escalation threshold rationale
- Golden set sampling method
- Evaluation metric choices
- Omissions and trade-offs

---

## Phase 0 (Scaffolding)

1. **Stack choice**: Python + FastAPI + PostgreSQL + pgvector
   - Rationale: Minimal dependencies, transparent, easy to modify live
   - Swap client for different LLM providers (Gemini default, easy to change)

2. **Docker Compose for DB**:
   - One `docker-compose up` command stands up Postgres + pgvector
   - Eliminates manual DB setup friction

3. **Prompt files in `/src/prompts/`**:
   - All LLM prompts are reviewable, versionable, modifiable without code change
   - One file per function (classify, draft, judge)

4. **Explicit rule-based escalation**:
   - Not a single LLM call; combines confidence, grounding, intent sensitivity, frustration signals
   - Each decision includes a reason code + human text

5. **Stub-first structure**:
   - All phase files exist with signatures and docstrings
   - Reduces back-and-forth; clear interface contracts

---

(More decisions to be added after each phase)
