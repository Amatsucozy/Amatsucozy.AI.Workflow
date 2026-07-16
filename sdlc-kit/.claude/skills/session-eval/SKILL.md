---
name: session-eval
description: >
  Manually evaluate and score an AI-user conversation session. Use this skill when the user explicitly asks to evaluate, rate, score, analyze, or audit a conversation — phrases like "evaluate this session", "rate our conversation", "how did the AI do", "session review", "analyze this chat", "grade this interaction", or "run an eval on this conversation". This skill produces a structured evaluation report with numerical scores across multiple quality dimensions, a timeline of corrections and misunderstandings, and actionable recommendations. Always use this skill when someone wants retrospective analysis of a conversation — even if they phrase it casually like "how'd we do?" or "was that efficient?". Manual invocation only — never auto-trigger on regular conversations.
---

# Session Evaluation Skill

This skill analyzes a recorded AI-user conversation and produces a structured evaluation report. It is **manually invoked** — never auto-triggered during an active conversation.

## Purpose

When reviewing a session, you want to understand:
- How effectively the AI met the user's needs
- Where communication broke down (misunderstandings, corrections)
- How efficient the exchange was (back-and-forth, redundancy)
- The quality of the AI's responses (clarity, accuracy, conciseness)
- What could be improved in future interactions

---

## Step 1: Identify the Session Source

The user will either:
1. **Paste conversation text** directly into the prompt
2. **Reference a file** (transcript .txt / .md / .json uploaded or on disk)
3. **Ask you to evaluate the current conversation** ("evaluate our session so far")

If the session is the **current conversation**, use the full conversation history visible in your context — including all prior turns. Be objective despite having participated.

If it's a **file**, read it with the appropriate tool before proceeding.

---

## Step 2: Parse and Structure the Session

Extract the following from the raw transcript:

```
session_metadata:
  - start_time: first message timestamp (or "unknown" if absent)
  - end_time: last message timestamp (or "unknown")
  - duration: computed if timestamps available, else "unknown"
  - total_turns: count of distinct user+AI message pairs
  - user_turn_count: messages from user only
  - ai_turn_count: messages from AI only
  - word_count_user: approximate total words from user
  - word_count_ai: approximate total words from AI
  - topic: inferred main topic/goal of the session
```

Then build a **turn-by-turn timeline** (summary only, not a verbatim replay):

```
turn_timeline:
  - turn: 1
    speaker: user / ai
    summary: "brief description of what was said/done"
    flags: [misunderstanding | correction | clarification_request | topic_shift | redundancy | error | success]
```

Flag each turn that exhibits one or more notable behaviors:
- **misunderstanding** — AI misread intent or context
- **correction** — user or AI corrected a prior statement
- **clarification_request** — either party asked for more info before proceeding
- **topic_shift** — conversation changed direction significantly
- **redundancy** — AI repeated information already given
- **error** — factual mistake, hallucination, or broken output
- **success** — particularly effective response or resolution

---

## Step 3: Score the Session

Compute scores for each dimension on a **1–10 scale** (10 = excellent). Use the scoring rubrics below. Be calibrated — 7 is "good", 5 is "mediocre", 3 is "poor".

### Scoring Dimensions

#### 1. Task Effectiveness (weight: 25%)
Did the AI accomplish what the user actually needed?
- 9–10: Goal fully achieved, user expressed satisfaction or outcome was clearly successful
- 7–8: Goal substantially achieved with minor gaps
- 5–6: Partial achievement; key parts missed or required heavy user effort
- 3–4: Goal mostly not achieved; significant rework needed
- 1–2: Goal failed entirely or AI went in wrong direction

#### 2. Response Clarity (weight: 15%)
Were AI responses understandable and well-structured?
- 9–10: Consistently clear, well-organized, appropriate length
- 7–8: Generally clear with occasional verbosity or structure issues
- 5–6: Mixed clarity; some responses hard to parse
- 3–4: Frequently unclear, poorly structured, or over-complicated
- 1–2: Confusing, incoherent, or disorganized throughout

#### 3. Conciseness (weight: 15%)
Did the AI avoid unnecessary verbosity?
- 9–10: Every response tightly matches the complexity of the request
- 7–8: Mostly concise with occasional padding
- 5–6: Noticeably verbose; responses often longer than needed
- 3–4: Frequently over-explains, repeats, or adds filler
- 1–2: Extremely verbose; hard to extract signal from noise

#### 4. Conversation Efficiency (weight: 20%)
How many turns were needed relative to what was necessary?
- 9–10: Minimal unnecessary turns; AI correctly understood intent first time
- 7–8: 1–2 avoidable clarification rounds
- 5–6: 3–4 avoidable rounds; noticeable friction
- 3–4: Frequent unnecessary back-and-forth; poor first-pass accuracy
- 1–2: Highly inefficient; most turns were corrections or restarts

#### 5. Accuracy & Reliability (weight: 15%)
Were the AI's factual claims, code, and outputs correct?
- 9–10: No noticeable errors; outputs verified or clearly correct
- 7–8: Minor errors that were self-corrected or easily caught
- 5–6: Some errors requiring user correction; hallucination present
- 3–4: Multiple significant errors; outputs unreliable
- 1–2: Systematic errors; outputs untrustworthy

#### 6. Tone & Adaptability (weight: 10%)
Did the AI adapt its style appropriately to the user?
- 9–10: Tone perfectly matched user's register; adapted smoothly over the session
- 7–8: Mostly appropriate; minor tone mismatches
- 5–6: Inconsistent tone or slow to adapt
- 3–4: Tone frequently mismatched; over-formal, condescending, or robotic
- 1–2: Persistently inappropriate tone

---

## Step 4: Compile Error & Correction Log

List every identified misunderstanding or correction with context:

```
issues_log:
  - turn: 3
    type: misunderstanding
    description: "AI interpreted 'summary' as full document instead of 1-paragraph overview"
    resolved_by_turn: 5
    resolution: "User clarified; AI re-did the summary"

  - turn: 7
    type: correction
    description: "AI provided Python 2 syntax; user corrected to Python 3"
    resolved_by_turn: 8
    resolution: "AI acknowledged and fixed"
```

---

## Step 5: Generate the Report

Output the final report using this exact structure. Write in prose where indicated; use structured data where indicated.

---

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

Letter Grade: [A/B/C/D/F mapped from overall score]
  A = 8.5–10   B = 7.0–8.4   C = 5.5–6.9   D = 4.0–5.4   F = below 4.0


TURN TIMELINE
─────────────
[Compact turn-by-turn summary with flags. Keep each line under ~80 chars.
Use emoji flags for at-a-glance scanning:
  ✅ success   ⚠️ clarification   ❌ error   🔄 correction
  🔁 redundancy   📍 topic shift   ❓ misunderstanding]

Turn 1 [User]: ...
Turn 2 [AI]:   ... ✅
Turn 3 [User]: ...
Turn 4 [AI]:   ... ❓ misunderstanding
...


ISSUES & CORRECTIONS
────────────────────
[N misunderstandings | N corrections | N errors]

[For each issue, a short paragraph: what happened, which turns, how resolved]


HIGHLIGHTS
──────────
✅ What worked well:
[2–4 bullet points on strengths — be specific, cite turns]

⚠️  What could be improved:
[2–4 bullet points on weaknesses — be specific, cite turns]


RECOMMENDATIONS
───────────────
For the AI:
[2–3 concrete suggestions that would improve future performance]

For the User (prompt engineering tips, if relevant):
[0–2 suggestions — skip entirely if user's prompts were clear and effective]


EFFICIENCY METRICS
──────────────────
Turns to first useful output:       [N]
Avoidable clarification rounds:     [N]
Self-corrections by AI:             [N]
Corrections initiated by user:      [N]
Topics covered:                     [list]
Unresolved threads (if any):        [list or "none"]
```

---

## Scoring Notes

- When timestamps are unavailable, omit time-based fields entirely rather than guessing.
- For very short sessions (< 5 turns), note this and acknowledge scores may be less meaningful.
- For code-heavy sessions, weight Accuracy & Reliability more in your narrative even though numerical weights are fixed.
- Avoid inflating scores. A normal productive session should score around 7.0–7.5 overall. Reserve 9+ for genuinely exceptional interactions.
- When evaluating the current conversation you participated in, flag this explicitly: **"Note: This is a self-evaluation of the current session."** Maintain objectivity.

---

## Output Format Options

By default, output the report as **formatted text in the chat**. If the user asks for a file, save to `/mnt/user-data/outputs/session-eval-[topic].md` and call `present_files`.

If the user says "brief eval" or "quick eval", produce a condensed version: just the Score Summary table, a 3-sentence narrative, and the top 2 recommendations. Skip the full turn timeline and issues log.
