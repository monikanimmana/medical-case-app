# Evaluation Set and Methodology

## Golden Set

**Location**: `eval/golden_set.jsonl`

Each line is a JSON object representing one annotated example:

```json
{
  "example_id": "unique_id",
  "customer_message": "...",
  "conversation_history": ["...", "..."],
  "true_intent": "intent_id",
  "should_escalate": true,
  "escalation_reason": "...",
  "good_reply_should_cover": "...",
  "difficulty": "easy|medium|hard",
  "notes": "..."
}
```

### Sampling Strategy

- **Size**: 150-250 examples
- **Source**: Held-out data not used in KB or classifier training
- **Stratification**: Deliberately stratified across intents to oversample rare intents
- **Seed**: Fixed random seed for reproducibility

### Labeling Criteria

**True Intent**: The primary intent the customer is expressing (tie-breaker: customer's stated need)

**Should Escalate**: Would a human support agent escalate this to a specialist?
- YES if: high-confidence needed, sensitive domain (money/legal/security), repeated unresolved issue, customer very frustrated
- NO if: standard issue with clear precedent available

**Notes**: Any ambiguous cases and how they were resolved

## Metrics Computed

1. **Intent Classification**:
   - Accuracy, Macro F1, Per-class F1
   - Confusion matrix

2. **Escalation Decision**:
   - Precision/Recall of escalation recommendation
   - False positive rate (over-escalation), false negative rate (under-escalation)

3. **Retrieval**:
   - Hit rate@1, @5 (does top-k retrieved case share the true intent?)

4. **Reply Quality** (LLM-as-judge + human spot-check):
   - Grounded in precedent
   - Factually consistent
   - On-topic / addresses issue
   - Appropriate tone
   - 1-5 scale on each, Cohen's kappa with human labels

## Files

- `harness.py`: Main evaluation script
- `judge_agreement.py`: Human vs LLM judge agreement analysis
- Output: `eval_report.json` or `eval_report.md`
