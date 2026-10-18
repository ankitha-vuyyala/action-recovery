# Agent interface {#sec:agentif}

**System instruction** (all language-model conditions):

> You are an autonomous operations agent. You complete the user's task by calling the provided tools, which act on live production systems. The user is not available while you work, so do not ask them questions. Follow the task instructions exactly. When the task is complete, or if you cannot make further progress, call finish with status "completed", "partial" or "failed", a brief summary, and a list of any operations whose outcome you are not certain about.

**User message.** The task goal, followed by the sentence "Each action must take effect exactly once." An example for T7:

> Triage ticket TCK-5476 for Woodgrove: open the issue 'Ticket TCK-5476: Woodgrove cannot export reports' (body: 'Reported by Woodgrove. Priority 3.'), add exactly these two comments to it, in order: 'Triage: reproduced for Woodgrove; assigning to reports team.' and 'ETA for Woodgrove: fix in next release.', and record triage:TCK-5476 with amount 3. Each action must take effect exactly once.

**Reflection prompt** (condition C7, sent after any turn with a tool error):

> One or more of your tool calls returned an error. Before your next action, think step by step about why it failed and what the best next action is.

**Nudge** (sent if a turn contains no tool call; at most three times):

> Continue the task using the tools. When you are done, call finish.

**Tools.** Each task exposes the following tools. Their descriptions state documented service behaviour only; they say nothing about faults or recovery methods.

- *Writes:* create_issue, add_comment, send_email, send_bulk_email, insert_record, insert_records, append_event, adjust_stock, increment_counter, create_transfer (with an optional transfer_id, described as an idempotency key), put_object.
- *Reads:* list_issues, get_issue, search_issues (described as updated asynchronously), search_sent_email, find_records, list_events, get_stock, get_counter, find_transfers, object_exists.
- *The agent's own corrections:* delete_issue, delete_comment, delete_record, delete_event, reverse_transfer.
- *Control:* wait (up to 60 s) and finish.

A task sees only the writes it needs, their reads and corrections, wait and finish.

**Limits.** At most 30 model turns and 40 tool calls per episode, with one model call per turn. Parallel tool calls were disabled, and `max_output_tokens` was 6000, including reasoning.

**Endpoint and settings.**

- *Endpoint and reasoning:* the OpenAI Responses API, stateless (`store=false`), with each model at its default reasoning setting.
- *Carried reasoning:* for reasoning models, the encrypted reasoning items are passed back with the transcript.
- *Model versions:* the resolved versions are recorded per call in the cost ledger.
- *Caching:* responses are cached by the SHA-256 of the request, which covers the model, instructions, input items, tools and parameters, together with the repeat index.

**Crash and resume.** The conversation is checkpointed to disk after every model turn and tool result. After a crash, the restarted agent re-executes every function call that has no recorded output. This is the replay semantics of common agent frameworks, applied identically in all conditions.

**Step mapping.** Faults target a plan step. A model's write is mapped to a plan step when its key fields match the step after normalising case, white space and trailing periods: the title for issues, the recipient and subject for mail, the item for records, the memo for transfers. For comments, the mapping uses the issue and the text, and falls back to the next unused comment step of that issue. A write that matches no step is an extra intent, and the grader still sees its effects.
