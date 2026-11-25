REVIEWER_PROMPT = """\
Review the current implementation in this repository against the design doc below.
Explore the codebase as needed using your file reading tools.

Do not run tests, linters, formatters, builds, servers, or commands that mutate \
the repository. Tests are run separately outside the review process. Prefer \
built-in read, search, and glob tools. If your backend exposes a read-only \
shell, you may also use inspection commands such as git diff/status/show, rg, \
sed, and ls.

OUTPUT FORMAT: {reviewer_output_format}
- "severity": one of "critical", "high", "medium", "low"
- "category": one of "bug", "missing_requirement", "design_mismatch", "code_quality", "review_guideline", "other"
- "file": the file path (or "general" if not file-specific)
- "description": concise description of the issue

{review_guideline_tagging_instruction}\
Focus on alignment with the Essential Requirements section of the design doc.

REVIEW DISCIPLINE:

1. Do not flag pre-existing patterns that are not introduced or materially \
altered by this branch, even when the branch touches adjacent code. Review \
is scoped to this branch's changes, not a full codebase audit.

2. Before raising a "critical" or "high" severity issue about missing \
behavior or a missing code path, verify the Essential Requirements section \
actually requires it. If the design doc does not require it, the issue is \
at most "medium" severity.

3. When an issue is a stylistic or architectural preference with no \
concrete correctness or maintainability impact on this branch, keep it at \
"low" severity or omit entirely.

If no issues are found, respond with an empty JSON array: []{assessment_instruction}

INFRASTRUCTURE FAILURES:
An inability to inspect the repository is not an implementation finding. Never \
encode denied/canceled file access, missing tool access, or an incomplete review \
as a severity issue. If tool or file access prevents a reliable review, respond \
only with this object instead:
{{"infrastructure_status":"tool_failed","status_detail":"concise failure reason","issues":[]}}

DESIGN DOC:
{design_doc_content}

{review_guidelines_section}\
{deferred_issues_section}\
"""

REVIEWER_GUIDELINE_TAGGING_INSTRUCTION = """\
If an issue traces to a specific review guideline rule (the R-tagged sections \
in ADDITIONAL REVIEW GUIDELINES below), set "category" to "review_guideline" \
and include a "review_guideline_id" field with the rule's tag (e.g. "R3"). \
Use the "review_guideline" category only for issues that genuinely trace to a \
tagged guideline rule.

"""

REVIEWER_DEFERRED_ISSUES_SECTION = """
DEFERRED ISSUES FROM PRIOR ITERATIONS:
The coder deferred these to human review. Do not re-raise unless you have \
reasoning the coder's rationale has not already addressed.

{formatted_deferrals}
"""

REVIEW_JSON_REPAIR_PROMPT = """\
Convert the reviewer output below into the required JSON array format.

Rules:
- Output only a JSON array.
- Preserve the reviewer's issues exactly; do not add, remove, or reinterpret issues.
- Each issue must be an object with at least "severity", "category", "file", and "description" when those fields are present in the reviewer output.
- If the reviewer found no issues, output [].
- If the reviewer output contains no recoverable issue list, output null.

{previous_attempt_section}\
REVIEWER OUTPUT:
{raw_output}
"""

CODER_PROMPT = """\
The selected reviewers have assessed the current implementation against \
the design doc below.

DESIGN DOC:
{design_doc_content}

{review_guidelines_section}\
REVIEWER FINDINGS:
{consolidated_reviews}

{prior_deferrals_context}\
Assess which issues are legitimate and fix them. Prioritize issues with \
blocking severities ({blocking_severities}). Address non-blocking severity \
issues only when the fix is simple and clearly beneficial. Stay within the \
scope of the design doc's Essential Requirements.

When a reviewer flags tests that pass only incidentally — because a default \
value happens to satisfy the fixture rather than because the test exercises \
the rule under test — address the fragility in the same iteration. The \
coupling is silent and surfaces as a future regression.

End your response with a CODER_DECISIONS block:

CODER_DECISIONS
```json
{{
  "stop_run": false,
  "stop_category": null,
  "stop_reason": null,
  "deferred_issues": []
}}
```

deferred_issues — reviewer concerns you chose not to act on. When uncertain \
whether an issue is legitimate, prefer deferring over speculatively fixing. \
Each entry: {{summary, reviewer, agent, role, severity, rationale}}. Use the \
reviewer's `agent:role` label for `reviewer`, and populate `agent` and `role` \
separately when the finding identifies them.

stop_run — escalate when the design doc itself has a gap or contradiction \
that makes further iteration premature. Pick one stop_category:

  flawed_requirement — a logical contradiction, a major architectural \
decision the design doc did not anticipate, or an `Agent-Drafted (Unreviewed)` \
Essential Requirement that the architecture critic flagged for introducing \
unrequested operational gates, state machines, or durable surfaces beyond \
the linked Verbatim Human Intent Reference. Another strong signal is when the \
same Essential Requirement keeps surfacing new, distinct violations across \
iterations despite successive fixes — that usually means the ER is an \
under-specified invariant (e.g., missing a path enumeration) and is better \
revisited by a human than patched incrementally.
  incomplete_requirements — a critical requirement is missing and has \
multiple non-trivial paths where the choice belongs in the design doc, not \
the code.

Do not stop_run for small unspecified details with an obvious solution \
(ship it). Err on the side of stopping when uncertain: a brief human review \
is cheaper than architectural work that will be scrapped.
"""

CODER_PRIOR_DEFERRALS_CONTEXT = """\
DEFERRED ISSUES FROM PRIOR ITERATIONS:
A prior coder pass deferred these to human review. If a reviewer has \
re-raised one with new reasoning that changes your assessment, you may \
address it. Otherwise, leave them.

{formatted_deferrals}

"""

INITIAL_CODER_PROMPT = """\
Take a first pass at implementing the design doc below. The working tree \
may already contain related code (e.g. a prior version being refactored) — \
inspect what is there and bring the implementation into alignment with the \
design doc, focusing on the Essential Requirements section.

DESIGN DOC:
{design_doc_content}

{review_guidelines_section}\
Stay within the scope of the Essential Requirements. Do not add features, \
refactor, or introduce abstractions beyond what the design requires.

After this initial pass, the selected reviewers will assess your \
implementation and feed findings back to a coder agent for refinement, so \
focus this pass on getting the structure and Essential Requirements right \
rather than polishing every detail.

End your response with a CODER_DECISIONS block:

CODER_DECISIONS
```json
{{
  "stop_run": false,
  "stop_category": null,
  "stop_reason": null,
  "deferred_issues": []
}}
```

stop_run — escalate when the design doc itself has a gap or contradiction \
that makes implementation premature. Pick one stop_category:

  flawed_requirement — a logical contradiction, a major architectural \
decision the design doc did not anticipate, or an `Agent-Drafted (Unreviewed)` \
Essential Requirement that introduces unrequested operational gates, state \
machines, or durable surfaces beyond the linked Verbatim Human Intent Reference.
  incomplete_requirements — a critical requirement is missing and has \
multiple non-trivial paths where the choice belongs in the design doc, not \
the code.

Do not stop_run for small unspecified details with an obvious solution \
(ship it). Err on the side of stopping when uncertain: a brief human review \
is cheaper than architectural work that will be scrapped.

deferred_issues — leave empty for the initial implementation pass; deferral \
applies to issues raised by reviewers in later iterations.
"""
