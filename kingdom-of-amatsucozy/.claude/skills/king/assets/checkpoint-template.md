# Session Checkpoint · {feature_id}

**feature_id:** {kebab-case name derived from task at *sw time, e.g. worker-retry-logic}  
**phase:** {Design | Planning | Implementation}  
**auto:** {true | false}  
**design_doc:** {docs/tasks/{feature_id}.md | none}  
**plan_doc:** {docs/tasks/{feature_id}-plan.md | none}  
**last_step:** {Step N title | none — only set during Implementation phase}  
**timestamp:** {ISO 8601}

---

## Resume instructions

On session resume, King reads this file and restores state without replaying conversation history.

- If phase is `Design` and design_doc is `none`: restart from Scout scope_map
- If phase is `Design` and design_doc exists: design doc was written, gate check required
- If phase is `Planning` and plan_doc is `none`: spawn Steward
- If phase is `Planning` and plan_doc exists: plan was written, gate check required
- If phase is `Implementation`: spawn Knight with plan_doc path; Knight finds resume point via first `[ ]` checkbox
