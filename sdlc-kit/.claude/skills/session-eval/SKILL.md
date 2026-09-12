---
name: session-eval
description: Evaluate and score an AI-user conversation on explicit request — "evaluate this session", "rate our conversation", "how did the AI do", "session review", "grade this interaction", or casual variants like "how'd we do?". Produces weighted 1–10 scores across six dimensions, a flagged turn timeline, an issues log, and recommendations. Manual invocation only — never auto-trigger.
---

# Session Evaluation

Analyze a recorded AI-user conversation and produce a structured evaluation
report. Manually invoked only — never during an active conversation without a
request.

## Step 1: Identify the Session Source

The session is one of:
1. **Pasted conversation text** in the prompt.
2. **A transcript file** (.txt / .md / .json) — Read it before proceeding.
3. **The current conversation** ("evaluate our session so far") — use the full
   history visible in context. State when earlier history has been
   summarized or is missing, and limit conclusions to visible evidence. Be
   objective despite having participated.

## Step 2: Parse and Structure the Session

Extract session metadata:

```
session_metadata:
  - start_time / end_time / duration: from timestamps, else "unknown"
  - total_turns: count of distinct user+AI message pairs
  - user_turn_count / ai_turn_count
  - word_count_user / word_count_ai: approximate
  - topic: inferred main goal of the session
```

Then build a turn-by-turn timeline (summaries, not a verbatim replay):

```
turn_timeline:
  - turn: 1
    speaker: user / ai
    summary: "brief description of what was said/done"
    flags: [misunderstanding | correction | clarification_request | topic_shift | redundancy | error | success]
```

Flag definitions:
- **misunderstanding** — AI misread intent or context
- **correction** — user or AI corrected a prior statement
- **clarification_request** — either party asked for more info before proceeding
- **topic_shift** — conversation changed direction significantly
- **redundancy** — AI repeated information already given
- **error** — factual mistake, hallucination, or broken output
- **success** — particularly effective response or resolution

## Step 3: Score the Session

Score each dimension 1–10 (10 = excellent) using the rubrics below. Be
calibrated: 7 is "good", 5 is "mediocre", 3 is "poor". Overall = sum of
(score × weight); weights total 100%.

#### 1. Task Effectiveness (25%) — did the AI accomplish what the user needed?
- 9–10: Goal fully achieved; user satisfied or outcome clearly successful
- 7–8: Substantially achieved with minor gaps
- 5–6: Partial; key parts missed or heavy user effort required
- 3–4: Mostly not achieved; significant rework needed
- 1–2: Failed entirely or went in the wrong direction

#### 2. Response Clarity (15%) — were responses understandable and well-structured?
- 9–10: Consistently clear, well-organized, appropriate length
- 7–8: Generally clear; occasional verbosity or structure issues
- 5–6: Mixed; some responses hard to parse
- 3–4: Frequently unclear, poorly structured, or over-complicated
- 1–2: Confusing or incoherent throughout

#### 3. Conciseness (15%) — did the AI avoid unnecessary verbosity?
- 9–10: Every response tightly matches the request's complexity
- 7–8: Mostly concise; occasional padding
- 5–6: Noticeably verbose; often longer than needed
- 3–4: Frequently over-explains, repeats, or adds filler
- 1–2: Extremely verbose; signal buried in noise

#### 4. Conversation Efficiency (20%) — turns needed relative to necessary?
- 9–10: Minimal unnecessary turns; intent understood first time
- 7–8: 1–2 avoidable clarification rounds
- 5–6: 3–4 avoidable rounds; noticeable friction
- 3–4: Frequent unnecessary back-and-forth; poor first-pass accuracy
- 1–2: Most turns were corrections or restarts

#### 5. Accuracy & Reliability (15%) — were claims, code, and outputs correct?
- 9–10: No noticeable errors; outputs verified or clearly correct
- 7–8: Minor errors, self-corrected or easily caught
- 5–6: Some errors needing user correction; hallucination present
- 3–4: Multiple significant errors; outputs unreliable
- 1–2: Systematic errors; outputs untrustworthy

#### 6. Tone & Adaptability (10%) — did the AI match the user's register?
- 9–10: Tone matched throughout; adapted smoothly over the session
- 7–8: Mostly appropriate; minor mismatches
- 5–6: Inconsistent or slow to adapt
- 3–4: Frequently mismatched — over-formal, condescending, or robotic
- 1–2: Persistently inappropriate

## Step 4: Compile the Issues Log

One entry per misunderstanding, correction, or error:

```
issues_log:
  - turn: 3
    type: misunderstanding
    description: "AI interpreted 'summary' as full document instead of 1-paragraph overview"
    resolved_by_turn: 5
    resolution: "User clarified; AI re-did the summary"
```

## Step 5: Generate the Report

Output exactly this structure:

```
╔══════════════════════════════════════════════════════╗
║          SESSION EVALUATION REPORT                   ║
╚══════════════════════════════════════════════════════╝

SESSION OVERVIEW
───────────────
Topic:         [inferred topic/goal]
Start Time:    [timestamp or "not recorded"]
End Time:      [timestamp or "not recorded"]
Duration:      [computed or "unknown"]
Total Turns:   [N] (User: [N] | AI: [N])
User Words:    ~[N]
AI Words:      ~[N]
AI/User Ratio: [ratio — higher means AI was more verbose relative to user]


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

Letter Grade: [A/B/C/D/F]
  A = 8.5–10   B = 7.0–8.4   C = 5.5–6.9   D = 4.0–5.4   F = below 4.0


TURN TIMELINE
─────────────
[One line per turn, under ~80 chars, with emoji flags:
  ✅ success   ⚠️ clarification   ❌ error   🔄 correction
  🔁 redundancy   📍 topic shift   ❓ misunderstanding]

Turn 1 [User]: ...
Turn 2 [AI]:   ... ✅
Turn 3 [User]: ...
Turn 4 [AI]:   ... ❓ misunderstanding


ISSUES & CORRECTIONS
────────────────────
[N misunderstandings | N corrections | N errors]

[One short paragraph per issue: what happened, which turns, how resolved]


HIGHLIGHTS
──────────
✅ What worked well:
[2–4 specific bullets, citing turns]

⚠️  What could be improved:
[2–4 specific bullets, citing turns]


RECOMMENDATIONS
───────────────
For the AI:
[2–3 concrete suggestions]

For the User (prompting tips, if relevant):
[0–2 suggestions — omit entirely if the user's prompts were clear]


EFFICIENCY METRICS
──────────────────
Turns to first useful output:       [N]
Avoidable clarification rounds:     [N]
Self-corrections by AI:             [N]
Corrections initiated by user:      [N]
Topics covered:                     [list]
Unresolved threads (if any):        [list or "none"]
```

## Scoring Notes

- No timestamps → omit time-based fields entirely rather than guessing.
- Very short sessions (< 5 turns): say so and note that scores are less
  meaningful.
- Code-heavy sessions: weight Accuracy & Reliability more in the narrative
  even though numerical weights are fixed.
- Don't inflate. A normal productive session scores around 7.0–7.5 overall;
  reserve 9+ for genuinely exceptional interactions.
- Self-evaluating the current session → flag it explicitly:
  **"Note: This is a self-evaluation of the current session."**

## Output Format

Default: the report as formatted text in the chat. If the user asks for a
file, save it to the path they name, else `docs/reports/session-eval-<topic>.md`
in the workspace, and give them the path.

"Brief eval" / "quick eval": only the Score Summary table, a 3-sentence
narrative, and the top 2 recommendations — skip the timeline and issues log.
