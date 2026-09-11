# AI Support Agent — Hiver Take-Home Assignment

A customer support agent that classifies incoming messages, drafts grounded replies, and decides escalation, built for the "Customer Support on Twitter" Kaggle dataset.

## Stack

- **Language**: Python 3.9+
- **API**: FastAPI
- **Database**: PostgreSQL + pgvector (Docker Compose)
- **LLM**: Google Gemini (API key required; provider swappable)
- **ML**: scikit-learn, sentence-transformers, pandas

## Quick Start

### Prerequisites

- Python 3.9+
- Docker + Docker Compose
- [Google Gemini API key](https://makersuite.google.com/app/apikey)

### Setup (5 minutes)

```bash
# 1. Clone and install
git clone https://github.com/monikanimmana/twitter-support-agent.git
cd twitter-support-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Environment
cp .env.example .env
# Edit .env: add your GEMINI_API_KEY, set BRAND once known (Phase 1)

# 3. Database
docker-compose up -d

# 4. Run the full pipeline (end-to-end, ~15 min on laptop)
python -m src.pipeline --brand [BRAND] --sample-size 5000
```

### Output

```
eval_report.md          # Metrics + visualizations
eval_report.json        # Structured results
eval/golden_set.jsonl   # 150-250 hand-labelled examples
report/REPORT.md        # Full analysis
report/DECISION_LOG.md  # Implementation decisions
```

## Phases

| Phase | Goal | Status |
|-------|------|--------|
| 0 | Repo scaffold, Docker, config | ✅ Complete |
| 1 | Brand selection, thread reconstruction | 🔄 Next |
| 2 | Intent taxonomy via clustering | 🔄 Next |
| 3 | Intent classifiers (baseline + LLM) | ⏳ Pending |
| 4 | Retrieval KB, grounded drafting | ⏳ Pending |
| 5 | Escalation policy (rule-based) | ⏳ Pending |
| 6 | Golden eval set (stratified sampling) | ⏳ Pending |
| 7 | Evaluation harness + judge agreement | ⏳ Pending |
| 8 | Report, decision log, README | ⏳ Pending |

## File Structure

```
.
├── src/
│   ├── ingest.py           # Load CSV, filter brand, reconstruct threads
│   ├── taxonomy.py         # Intent schema
│   ├── classify.py         # 3 classifiers
│   ├── retrieve.py         # pgvector KB + similarity search
│   ├── draft.py            # Grounded reply generation
│   ├── decide.py           # Escalation policy
│   ├── pipeline.py         # Orchestration
│   └── prompts/            # LLM prompts (classify, draft, judge)
├── eval/
│   ├── harness.py          # Metrics + LLM-as-judge
│   ├── judge_agreement.py  # Human vs judge agreement
│   ├── golden_set.jsonl    # 150-250 hand-labelled examples
│   └── README.md           # Eval methodology
├── report/
│   ├── REPORT.md           # Max 6 pages, results + failure modes
│   └── DECISION_LOG.md     # 10-15 key decisions
├── data/
│   ├── raw/                # Original Kaggle CSV (gitignored)
│   ├── processed/          # Cleaned threads (gitignored)
│   └── sample/             # Small public sample (tracked)
├── tests/                  # Unit tests
├── docker-compose.yml      # Postgres + pgvector
├── requirements.txt
├── .env.example
├── CREDITS.md              # Citations for borrowed code/prompts
└── README.md               # This file
```

## Key Design Decisions

- **No LangChain**: Direct Gemini API calls + explicit retrieval logic for transparency
- **Rule-based escalation**: Combines confidence, grounding, intent sensitivity — not a black-box LLM call
- **All prompts in `/src/prompts/`**: Reviewable, versionable, modifiable without code change
- **Reproducible sampling**: Fixed seed, documented heuristics, stratified golden set
- **Proof > cleverness**: Emphasis on eval metrics, judge agreement, honest limitations write-up

## Development Notes

- **Dataset**: Kaggle "Customer Support on Twitter" (3M tweets) — this agent is built on a documented subsample (5k–20k tweets)
- **Evaluation****: Stratified golden set (150-250 examples), LLM-as-judge with human spot-check, Cohen's kappa agreement
- **"Resolved" heuristic**: Documented as noisy; limitations clearly stated in report
- **Config-driven thresholds**: Confidence, grounding, escalation rules all in `.env` or config files

## Report & Evaluation

See:
- `/report/REPORT.md`: Problem framing, results, failure modes, limitations, next steps
- `/report/DECISION_LOG.md`: 10-15 key non-obvious decisions
- `/eval/README.md`: Sampling strategy, annotation criteria, metric definitions
- Run `python -m eval.harness` to see full metrics + judge agreement

## Citations

See `CREDITS.md` for attribution of borrowed code, prompts, and patterns.

---

**Status**: Actively in development (Phase 1 next).
**Contact**: [Your name/email]
