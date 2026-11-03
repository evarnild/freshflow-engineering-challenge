# Intents

One folder per piece of work. It holds the artefacts that carry the work
from "what do we want" to "merged". This is freshflow-engineering-challenge's slice of the
AI-native SDLC: each stage ends by writing something the next stage reads,
and the chain is the audit trail of who asked for what and who approved it.

`plan.md` at the repo root is the **coordinator view**: snapshot, queue,
backlog and shipped list. It never holds a work item's detail. Its queue rows
point here.

## Layout

```
intents/
  <id>-<slug>/
    intent.md      what we want and why: the problem, in the originator's words
    spec.md        what we will build (features only)
    plan.md        how we will build it, approved before code; ends with ## Progress
    review.md      the review report (written by /review, updated in place)
    metadata.yml   id, type, status, gates, links
  _templates/      what the skills fill in; usable raw by hand
```

**The id is a `§` number**, one more than the highest used in `plan.md`
or `intents/`. Commit messages use the same numbering, so `§2`,
`intents/2-…/` and `feat/2-…` all name the same thing. §1 is the stack
decision.

## Types

Every intent declares a type. The type decides which artefacts and gates
apply, so the heavy path is paid only where it earns its keep. **When in
doubt, it is a feature.**

| Type | Branch | Artefacts | Gates you record | Use for |
| --- | --- | --- | --- | --- |
| feature | `feat/<id>-<slug>` | intent, spec, plan | intent, spec, plan | new behaviour, a new integration, anything with a design question |
| fix | `fix/<id>-<slug>` | intent, plan | intent, plan | a live defect; the intent *is* the spec. The change carries a test that fails first |
| refactor | `refactor/<id>-<slug>` | intent, plan | intent, plan | structure changes that hold behaviour constant |
| adjustment | `adjust/<id>-<slug>` | intent | intent | wording, README, config, constants: at most 5 files and 60 lines, no core code |
| experiment | `exp/<id>-<slug>` | intent | intent | throwaway probes such as a prompt trial or a model comparison; never merged into core code as-is |

The declaration is a claim, and `npm run check:intent` is the evidence. It
compares what arrived against what the type should look like, and reports
`ROUTE` when they disagree. Examples: an "adjustment" that touched core code,
a "fix" with no test, a "refactor" that deleted test lines. A route is not a
block. Either re-declare the type (and add the missing artefacts), or say in
`review.md` why the mismatch is fine.

What counts as core code, as a test, and as code at all is defined at the
top of `scripts/intent-check-lib.mjs`. The rules are language-neutral until
§1 picks the stack and narrows `CORE_CODE`.

A fix whose defect came from an earlier intent's change records that in
`metadata.yml` as `follows_up: <id>`. That key is what lets
`npm run sdlc:scan` count follow-ups per review tier, so set it only for a
real cause.

If an intent turns out to be wrong after merge, either revert and keep the
original intent, or forward-fix with a new one. Don't rewrite the old
folder.

## Gates

Four of the strategy's six human gates live here, plus the live check when a
review says one is owed. You are the human at each.

| Gate | Recorded as | Meaning |
| --- | --- | --- |
| accept the intent | `intent_accepted: <date>` | the work is worth doing, and the problem statement is right |
| accept the spec | `spec_accepted: <date>` | this is what we will build |
| approve the plan | `plan_approved: <date>` | this is how we will build it; no code before this gate |
| live check, when owed | `live_checked: <date>` | you ran it yourself and saw what `review.md` → `## Live check` said you should; no merge before this gate (`REVIEW-POLICY.md` → "Live checks") |
| approve the change | `review.md` verdict + the merge commit | you read the report (and the diff, at the Reviewed tier) and take responsibility |

The other two gates stay outside `intents/`: authorising a release, and
triaging a finding (turning a defect into a new fix intent).

`check:intent` fails a change whose code moved before the gates its type
needs were recorded.

### Recording a gate

You record gates. An agent may write a gate date for you only under all of
these conditions:

- you asked for that gate on that intent in the current conversation. "Accept
  §3's intent" counts. So does "yes" in reply to a message that proposed
  recording that gate. A standing instruction, a memory or an earlier session
  does not count;
- the date is today's, and the line carries the comment
  `# recorded by agent on owner's request`;
- the commit that records it says so in its subject, for example `§3: plan
  approved (recorded on the owner's request)`.

`live_checked:` is the exception: only you write it, because its point is a
check by someone other than the model. This is the interim rule that
a fuller design may replace. Change it here and in the skills together.

## Who edits what

- **You** write or accept `intent.md`, `spec.md` and `plan.md`, and own every
  gate in `metadata.yml`. The skills draft; you decide.
- **The implementer agent** may only append to the `## Progress` section at
  the end of its item's `plan.md`, and set `status: in-review` when done.
- **The reviewer and `/review`** write `review.md` and nothing else here.

## Stamps

A file a skill produced starts with
`<!-- generated-by: freshflow-engineering-challenge/<skill>@<version> -->`. That line is how
the grid tells "written by hand" (L1) from "produced by a versioned skill"
(L2). Keep it when you edit the file. Remove it only if you rewrote the file
from scratch.

## Status values

`draft` → `accepted` → `in-progress` → `in-review` → `done`, or `abandoned`
or `deferred`. The status here is the source of truth. The one-line row in
`plan.md`'s queue mirrors it.
