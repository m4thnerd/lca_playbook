# Verbatim Human Intent Reference Playbook

When an LCA drafts or updates a design doc, the design doc itself should stay
clean, structured, and easy for humans to read. However, downstream AI
reviewers (`ER Justification Preflight`, the `architecture` critic in
`convergence-review`, and `general-stability-review`) need access to **what the
human owner actually asked for** so they can detect requirements risk -
specifically, when an agent-authored `# Essential Requirements` bullet or
design-doc section invents operational refusal gates, state machines, or scope
that the human never requested.

Pasting raw human prompts directly into the design doc creates two problems:

1. **Human readability:** Voice-transcribed prompts are often long,
   stream-of-consciousness, exploratory, or repetitive. Dumping them into the
   design doc makes the design doc harder for humans to scan.
2. **Multi-turn context loss:** Human intent is frequently established across
   several turns, including short replies to LCA questions or numbered options
   (for example, *"Agreed on #1 and #3; for #2 let's keep it on the frontend"*,
   or *"Agreed on all fronts. Please make it happen."*) and mid-conversation
   course corrections that supersede earlier instructions. Without the specific
   LCA context being replied to, those human turns cannot be interpreted
   accurately.

To solve both problems, maintain a separate **Verbatim Human Intent Reference**
file alongside the design doc (for example,
`docs/design/<feature>_human_intent.md` or a companion file in `tmp/`) and link
to it at the top of the design doc:

```markdown
Verbatim Human Intent Reference: docs/design/<feature>_human_intent.md
```

---

## Core Rule: Verbatim Words + Minimal Context Stitching (Never Paraphrase into Spec-Speak)

The primary purpose of the Verbatim Human Intent Reference is **requirements-risk
detection** (answering: *"Did the human actually ask for this mechanism, or did
an agent extrapolate it?"*).

Do **not** summarize or rewrite the human's words into formal requirements
prose - that paraphrase step is the exact point where agent extrapolation slips
in. Instead, keep the human's words **verbatim** in chronological turns and
apply only three lightweight structural annotations:

### 1. Inject `[LCA Context Referenced]` Above Context-Dependent Replies

Whenever a human turn responds to LCA questions, numbered options, or a proposed
approach, insert a concise `**[LCA Context Referenced]**` block directly above
the human quote containing the exact options or proposal the human is replying
to.

**Example (Saved Views & Side-Panel Notes):**

```markdown
### Turn 2 (Decisions on Open Questions)
**[LCA Context Referenced: 6 open questions from `docs/design/saved_views_refresh.md` - (1) prototype Slice 2 first vs. 1-shot; (2) fixed 10 rows/page vs. user-selected page size; (3) browser-local filter persistence vs. session-only; (4) row-side "quick notes" drawer as its own slice; (5) keeping selection across pagination vs. resetting; (6) staging-only first vs. feature branch]**
> "1. Prototype first? ... - Let's go for a full 1-shot implementation.
> 2. Page size: ... - Let's continue allowing the user to select their preferred row count.
> 3. Browser-local filter memory: ... Local persistence is approved.
> 4. Quick-notes drawer: ... - Let's include this in the shipment as its own slice, though it'll likely need a minor adjustment on the backend registering a new 'SAVED_VIEW' note context type. Let's keep the backend changes to a minimum, and retain the existing drawer policy of closing the side panel any time the active row changes (fresh panel state per row).
> 5. Pagination selection: ... - Reset selection when changing pages so bulk actions never hit off-screen rows.
> 6. Where this lands first: ... - Let's put it on its own saved-views-refresh feature branch."
```

**Example (Session Dashboard):**

```markdown
### Turn 8 (Approving Completion Goals & Status Labels)
**[LCA Context Referenced: LCA proposed a ~60-line approach: (1) store optional completion goals in `goals/<session_id>.md` edited via an expanded-row textarea; (2) prepend the goal file to judge/brief prompts; (3) add a `follow-through` status label between `merge` and `quick-answer`; (4) add a deterministic `active` status label for sessions active in the last hour without a model call.]**
> "Agreed on all fronts. Please make it happen."
```

### 2. Mark In-Turn Voice-Dictation Self-Reversals with `~~Strikethrough~~` + `[Self-Corrected in Turn N]`

In voice-dictated prompts, humans often think out loud through an option and
then reject it mid-message. If left unmarked, a fast-scanning agent may mistake
the rejected brainstorm for an active requirement. Strike through the discarded
clause while keeping the text visible, and add a bracketed note.

**Example:**

```markdown
### Turn 4 (Cancelling Session Grouping in Favor of Semantic Tags)
**[LCA Context Referenced: Naming options proposed by LCA - `1. Control`, `2. Queue Board`, `3. Dispatch`]**
> "I think I'm gonna go with Queue Board. ...
> ~~Having those highly related ones clustered together in a simple grouping would be really helpful... we could have a model called something like a session group, and all it contains is one title... and then within it, each session card that we currently have maybe just has a foreign key into that group.~~ **[Self-corrected in Turn 4: grouping & foreign-key model explicitly rejected]**
> Maybe as I'm thinking about it, this might just be getting too complicated. Yeah, let's forget it. Let's forget the whole grouping idea. Maybe if we were to do anything there, we would maybe just have semantic tags. We want to lean towards being simple rather than complex."
```

### 3. Mark Cross-Turn Superseding Decisions with `~~Strikethrough~~` + `[Superseded by Turn M]`

When a later turn changes or narrows an earlier instruction, do not silently
delete the history. Strike through the superseded sentence in the earlier turn
and point to the later turn so reviewers see both the evolution and the currently
active rule.

**Example:**

```markdown
### Turn 2 (Layout Compaction & Confidence Band Rule)
> "Clarifying: we never show sub-skill deltas with the confidence band toggled off. The confidence band is always visible by default going forward. ...
> ~~I think what we should do is eliminate the practice score banner~~ **[Self-corrected in Turn 2: keep as a compact 30-50px top bar]** Maybe when I said eliminate the practice score banner, maybe that's not the right phrasing. I think we shift it to something that appears at the very top, but we make it a very, very short card. ...
> ~~I'm thinking it could also be a good idea to let users collapse the visible height of the Score Summary card itself.~~ **[Superseded by Turn 6 #4: Score Summary card must be collapsed by default with a 1-line summary preview]**"
```

---

## When to Update the File

- **Before ER Preflight:** Create the initial Verbatim Human Intent Reference
  file when drafting the design doc and `# Essential Requirements`.
- **After Any New Human Turn:** Whenever the human replies with answers to open
  questions, visual feedback, or scope adjustments, append the new turn (with
  any `[LCA Context Referenced]` and `[Superseded by Turn M]` tags) before
  running the next implementation, `convergence-review`, or `GSR` pass.
- **How Reviewers Use It:** Reviewers do not need this file to be polished
  prose; they use it as a ceiling check against unrequested mechanisms. If an
  `Agent-Drafted (Unreviewed)` ER or code change introduces a refusal gate,
  state machine, or durable surface that has no basis in the Verbatim Human
  Intent Reference, reviewers flag it for removal.
