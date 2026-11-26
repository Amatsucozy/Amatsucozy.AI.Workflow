---
name: session-eval
description: Evaluate and score an AI-user conversation on explicit request — "evaluate this session", "rate our conversation", "how did the AI do", "session review", "grade this interaction", or casual variants like "how'd we do?". Produces weighted 1–10 scores across six dimensions, a flagged turn timeline, an issues log, and recommendations. Manual invocation only — never auto-trigger.
---

# Session Evaluation

Evaluate a recorded AI-user conversation, only when asked.

## Source

Pasted text, a transcript file (read it first), or the current conversation.
For the current conversation, say if earlier history was summarized or is
missing, limit conclusions to visible evidence, stay objective despite having
participated, and open the report with: **"Note: This is a self-evaluation of
the current session."**

## Scoring

Score each dimension 1–10. Calibrate: 7 is good, 5 mediocre, 3 poor; a normal
productive session lands around 7.0–7.5 overall, and 9+ is reserved for
genuinely exceptional work. Overall = Σ(score × weight).

| Dimension | Weight | 9–10 | ~5 | ≤3 |
|---|---|---|---|---|
| Task Effectiveness | 25% | goal fully achieved | partial; key parts missed or heavy user effort | mostly not achieved or wrong direction |
| Response Clarity | 15% | consistently clear, well organized | mixed; some responses hard to parse | frequently confusing |
| Conciseness | 15% | every response matches the request's complexity | noticeably verbose | signal buried in filler |
| Conversation Efficiency | 20% | intent understood first time | 3–4 avoidable rounds | most turns were corrections or restarts |
| Accuracy & Reliability | 15% | no noticeable errors | errors needing user correction | outputs untrustworthy |
| Tone & Adaptability | 10% | register matched throughout | inconsistent or slow to adapt | persistently mismatched |

In code-heavy sessions, give Accuracy more weight in the narrative (the
numeric weights stay fixed). Under 5 turns, note that scores are less
meaningful.

Flag turns as: ✅ success, ⚠️ clarification request, ❌ error (factual,
hallucination, broken output), 🔄 correction, 🔁 redundancy, 📍 topic shift,
❓ misunderstanding.

## Report

```
╔══════════════════════════════════════════════════════╗
║          SESSION EVALUATION REPORT                   ║
╚══════════════════════════════════════════════════════╝

SESSION OVERVIEW
───────────────
Topic:         [inferred goal]
Start / End:   [timestamps — omit these lines if none recorded]
Duration:      [computed — omit if no timestamps]
Total Turns:   [N] (User: [N] | AI: [N])
User Words:    ~[N]
AI Words:      ~[N]
AI/User Ratio: [ratio]

SCORE SUMMARY
─────────────
┌─────────────────────────────┬───────┬────────┐
│ Dimension                   │ Score │ Weight │
├─────────────────────────────┼───────┼────────┤
│ Task Effectiveness          │  X/10 │  25%   │
│ Response Clarity            │  X/10 │  15%   │
│ Conciseness                 │  X/10 │  15%   │
│ Conversation Efficiency     │  X/10 │  20%   │
│ Accuracy & Reliability      │  X/10 │  15%   │
│ Tone & Adaptability         │  X/10 │  10%   │
├─────────────────────────────┼───────┼────────┤
│ OVERALL (weighted)          │  X/10 │ 100%   │
└─────────────────────────────┴───────┴────────┘
Letter Grade: [A/B/C/D/F]   A ≥ 8.5   B ≥ 7.0   C ≥ 5.5   D ≥ 4.0   F < 4.0

TURN TIMELINE
─────────────
Turn 1 [User]: <summary, under ~80 chars>
Turn 2 [AI]:   <summary> <flags>

ISSUES & CORRECTIONS
────────────────────
[N misunderstandings | N corrections | N errors]
<one short paragraph per issue: what happened, which turns, how resolved>

HIGHLIGHTS
──────────
✅ What worked well: <2–4 bullets citing turns>
⚠️  What could be improved: <2–4 bullets citing turns>

RECOMMENDATIONS
───────────────
For the AI: <2–3 concrete suggestions>
For the User: <0–2 prompting tips; omit if the prompts were clear>

EFFICIENCY METRICS
──────────────────
Turns to first useful output:   [N]
Avoidable clarification rounds: [N]
Self-corrections by AI:         [N]
Corrections by user:            [N]
Topics covered:                 [list]
Unresolved threads:             [list or "none"]
```

"Brief eval" / "quick eval": only the Score Summary, a 3-sentence narrative,
and the top 2 recommendations.

Default output is chat. If a file is requested, save to the path given, else
`docs/reports/session-eval-<topic>.md`, and give the path.
