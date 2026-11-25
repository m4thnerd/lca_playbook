# UI/UX Design Patterns: Standing Rules

Rules for any user-facing UI work, each learned from a real review. Read this
before designing, redesigning, or judging a user-facing page. Entries are short
on purpose: the pattern, where it was seen, why it fails, and what to do
instead. Add an entry only when a human has called a pattern out on a real
product; do not pad this file with general taste.

## DP-001: Never put a marketing hero on an internal page

**Never again.** Do not give a signed-in or task page a landing-page hero: a
one-line slogan or "poetic" headline set in a massive display font, usually
with an uppercase eyebrow label above it and a lede sentence below, taking most
of the space above the fold before any information appears.

Seen on a web application prototype across nearly every internal tour page:
"Preview a sample workspace", "Your preferences, quietly remembered",
"One record. Zero clutter.", "Your handoff summary", each filling
the top third of the screen. The technical lead called it out the next day: it
reads as fake, as trying to be cool, and as marketing poetry on pages where the
user came to do a job.

Why it fails: the best case is a small smirk on the first visit. Every later
visit, the same user scrolls past a block that carries zero information, zero
signal, and zero affordance, and gets more annoyed each time. On a phone the
hero alone can fill the first screen. It also pushes the real content, the
first action, and the status the user came for below the fold.

Where it can belong: the hero section of a public homepage or a landing page,
once, and even there only when the copy says something concrete.

Do instead, on every internal page:

- Lead with the page's name at ordinary heading size (the document, the file,
  the application) and the one status or number the user came back for.
- Put the first action and the current state above the fold, before any
  explanation.
- Let the page be plain. Good internal pages look like a well-organized form,
  table, or record, not a poster.
- Write copy that tells the reader a fact or what to do next. If a sentence
  would survive being deleted, delete it.
- Keep decorative photos off task pages; a domain user knows what their tools
  look like.

How to catch it before a human does: when reviewing screenshots, ask each
reviewer persona, in character, whether anything on the page is annoying or is
trying to be fancy in a dumb way, and to name the element. Give the same
question to a persona for each user type, and treat any element two personas
name as a defect, not a taste disagreement.

## DP-002: Never tell an end user which model produced a response

Standing rule: no user-facing page, message, or export shows which language
model, model version, vendor, or internal prompt/extractor version produced a
response. Model names belong in logs, audit trails, and internal operator tools
only. Saying "an AI wrote this" where a disclosure rule requires it is fine;
naming the AI model or vendor is not.

Seen on a prototype document-reading page where the attempt header printed the
model and prompt versions to the customer. The model is an implementation
detail that changes without notice; showing it invites the reader to judge by
vendor rather than by the evidence, and makes every vendor switch a visible
product change.
