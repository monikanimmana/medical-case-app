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

## Phase 1 (Data Acquisition & Cleaning)

6. **Brand selection: AmazonHelp**
   - Rationale: 169k tweets (largest dataset), 50% company reply rate, diverse issues
   - Gives strong signal for intent classification and retrieval KB

7. **Subsample size: 10k tweets**
   - Rationale: Enough for meaningful intent discovery + evaluation, fast iteration (<5 min per phase)
   - Fixed seed (42) for reproducibility

8. **Conversation threading**
   - Included both inbound (customer) and outbound (brand) tweets
   - Reconstructed via tweet_id / in_response_to_tweet_id relationships
   - Result: 9,542 threads from 9,763 tweets

9. **"Resolved" heuristic**
   - Brand replied + no escalation signals in last customer message
   - Escalation signals: "still waiting", "not resolved", "refuse", "this is unacceptable"
   - Positive signals: "thank", "solved", "fixed", "perfect"
   - Result: 213/9542 (2.2%) marked resolved
   - **Limitation**: Noisy heuristic; many unresolved-looking threads may actually be resolved in reality. Documented as such.

10. **Data cleaning**
    - Removed duplicates (237 removed)
    - Removed empty/malformed tweets
    - Kept @mentions as [MENTION] tokens (not removed) for context
    - Removed URLs

---

(More decisions to be added after each phase)
