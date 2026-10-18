# Settle: recovery by attribution {#sec:method}

Settle is a layer between an agent and its tools that turns the constructive side of @sec:theory into a protocol. The agent, scripted or a language model, calls tools as usual. Settle intercepts every write and, in the language-model setting, every deletion the agent requests. It returns one of three observations: *ok* with the effect's id, *unknown* with a reason, or the service's own error when the outcome is known. Settle has six parts.

**Operation identity.** Each logical intent receives one operation id, which is kept across retries, restarts and rephrasings. For the scripted agent, the intent is the plan step. For a language-model agent, a write is bound to an intent by its *intent fields*: the title of an issue, the recipient and subject of a mail, the item of a record. A rephrased re-issue of the same issue therefore maps to the same operation. In my implementation this binding reuses the harness's mapping of model writes onto the task's plan steps by these fields (@sec:agentif). A deployed layer has no plan to map onto and would bind by the intent fields alone. It would then also merge two deliberately identical writes, such as the same reminder sent twice on purpose, unless the agent marks them as distinct. The follow-up study runs this plan-free binding (S-np) and finds identical outcomes (@sec:followup).

**Durable intent journal.** Before the first dispatch, Settle appends `intent → {op id, arguments, aggregate before}` to a journal and calls `fsync`. Each attempt moves the record through the states `dispatching`, then `confirmed`, `in_doubt` or `unknown`. After a crash, a record found `dispatching` or `in_doubt` is resolved before anything is re-issued, which is what Proposition 6 requires.

**Attribution.** Settle uses the strongest attribution that the contract offers. For a class-K write, the op id is the idempotency key: TigerBeetle derives the transfer id from it, and the object store uses a conditional create. For a class-A write, the op id is written into a field that the service persists, such as an `op-id:` line in an issue or comment body, the mail `Message-ID` header, a reference column, a stream field or object metadata. The agent is not told about the tag, although it can see it when it reads the record back. For a class-U write, Settle records the aggregate before the write and uses the change, which is valid only under exclusivity (Proposition 5). A write that can be found only by content (class C in @tbl:map_theory; in my stack, the bulk e-mail) is not attributable. For such writes the implementation falls back to a content match, as the baselines do, and lists the operation as uncertain whenever it had to re-issue it. It does *not* abstain when the content match succeeds at the first check, which is the case a look-alike exploits; @sec:h4 reports the consequence. A design that abstains on every ambiguous class-C write would report these failures, at the cost of reporting uncertainty in every ambiguous class-C episode; the follow-up study measures it (S2).

**Resolution of unknown outcomes.** On an error or timeout, Settle re-issues a keyed write with the same key. For a taggable write, it waits out the read path's documented lag and counts the effects carrying the tag. If there are one or more, the operation is done and the id of the kept effect is returned. If there are none, the write is re-issued under the same tag. For an irreversible write such as an e-mail, Settle first waits until the assumed in-flight bound $\Delta$ has passed since the last attempt, so that a re-issue cannot overtake a late commit (Proposition 3). For an aggregate shared with other writers it stops and returns *unknown*. After three attempts it returns *unknown* in every case.

**Reconciliation horizon.** When the agent finishes, Settle keeps reconciling every operation that was ever in doubt until $t_{\text{last}} + \Delta + \lambda$. For each such operation it counts the effects by tag, re-issues if none exists, and marks surplus effects for compensation. The final sweep also covers operations that were confirmed at once, which catches transport-level redelivery. If no operation was ever in doubt, the sweep runs at once without waiting, so it catches a redelivery only if the duplicate is already visible when the agent finishes. My main redelivery fault delivers the duplicate immediately; a delayed redelivery, as from a queue's visibility timeout, needs the sweep to wait in every episode, which the follow-up study tests (S2).

**Evidence-gated compensation.** A surplus effect is neutralised only if it carries the operation's tag and is not the effect that the operation keeps, which is the one whose id later steps have already received. Compensations are themselves writes. Settle's compensations in my stack are deletions, which are idempotent, and decrements of exclusively written aggregates, which are not. In the experiments every compensation travelled on a fault-free path, so assumption (e) of Proposition 2 was not stressed. Three further consequences follow. An effect that cannot be attributed is never compensated, which avoids the *orphaned compensation* anomaly [@trofimov2026anomalies]. An irreversible surplus is reported as an unrecoverable duplicate instead of being hidden. And in the language-model setting, the same rule guards the agent's own deletion tools: a deletion of an effect that carries none of the task's tags, or of the only effect of a completed operation, is refused with a short explanation. I added this rule on the development split, after observing that a careful agent which sees two identical issues "cleans up" by deleting the other user's issue (@sec:results). Clean-up by content is exactly the unsound compensation of Proposition 4.

The pseudocode below summarises the write path for a taggable, reversible tool; the released code contains the full implementation.

```text
write(intent, args):
  rec = journal.get(intent)
  if rec is None:
    rec = journal.put(intent, op=new_id(), state=intent)
  elif rec.confirmed:                     # done before a crash or re-issue
    return ok(rec.value)
  elif rec.state in (dispatching, in_doubt):    # restart after a crash:
    return resolve(intent)       # wait lag (+ Δ if irreversible), count
  journal.put(intent, state=dispatching)  # write-ahead, before sending
  r = dispatch(args + tag(rec.op))
  if r.ok: return ok(journal.confirm(intent, r.id))
  journal.put(intent, state=in_doubt)
  sleep(lag(tool))
  found = read_by_tag(rec.op)             # attribution, not content
  if found: return ok(journal.confirm(intent, kept(found)))
  return write_again(intent)        # same tag; ≤ 3 attempts, then unknown

finish():
  if journal.ever_in_doubt():
    sleep_until(max(last_attempt) + Δ + λ)    # reconciliation horizon
  for op in journal.ever_in_doubt() ∪ journal.confirmed():
    found = read_by_tag(op)
    if not found: re-issue(op)
    for e in found − {kept(op)}:
      compensate(e)                   # only effects carrying op's tag
  report(unknown = unattributable re-issued ops, shared aggregates,
         irreversible duplicates)
```

**Assumptions and parameters.** Settle does not assume an idempotency key on the service, a well-behaved agent (the agent may retry, rephrase, crash or try to delete things), or a known order of faults. It does assume that the tag survives byte-exact in the persisted field, assumption (b) of Proposition 2, which the environment validation checks per service, and that no one else copies the tag into another record, assumption (g). A tag in a visible body line can be copied, for instance when a user quotes the record; requiring the tag *and* the client's own author account before counting or compensating an effect would close most of this gap, and my implementation does not yet do so. Its parameters are the assumed in-flight bound $\Delta$ and the documented read lags. $\Delta$ was set on the development split to 20 s and frozen before testing. Where it is violated, Propositions 2 and 7 predict the residual risk; the experiments include a heavy-tailed delay distribution to measure that risk, and @sec:horizon traces how it moves with $\Delta$.

**Ablations.** Four ablations each remove one component. S−j keeps the intent journal, and with it the tag, in memory, so by Proposition 6 it tests whether the tag must survive a crash; S−t matches effects by content instead of by tag; S−h verifies once and has no horizon; and S−c flags surplus effects without compensating them. Each ablation should fail in the cells where the theory says its component is needed, and should be close to Settle elsewhere.
