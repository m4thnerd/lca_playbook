# Glossary

- **LCA (Lead Coding Agent):** the coordinating agent responsible for
  maintaining human intent, delegating implementation and line-level review,
  adjudicating findings, and reporting truthful status to the human owner.
- **EngD (Engineering Director):** an optional coordination layer above multiple
  LCAs used *only* when independently progressing workstreams have a concrete
  cross-stream interface, lock, or deployment dependency.
- **User Story:** a stakeholder, a desired outcome, and the reason that outcome
  matters (`As a ..., I want ..., so that ...`).
- **Verbatim Human Intent Reference:** a companion file preserving the human's
  exact words and scope boundaries across turns so autonomous preflights and
  critics can detect unrequested agent-invented scope.
- **Essential Requirement (ER):** one of the 1-10 plain-language behaviors or
  constraints in `# Essential Requirements` whose absence would make an
  implementation materially wrong; serves simultaneously as the compact human
  specification anchor and the `convergence-review` scope anchor.
- **Architecture Pressure (1-5):** a score measuring the *steady-state
  maintenance burden* (durable code, contracts, tables, consumers, compatibility
  paths) a change leaves behind after landing, independent of short-term coding
  effort; paired with signed **Architecture Pressure Delta** for simplifications
  and refactors.
- **Convergence Review (`convergence-review`):** an automated build-review-fix
  loop that runs a coder and independent `core` + `architecture` reviewers
  against `# Essential Requirements`.
- **General Stability Review (`general-stability-review` / GSR):** an
  independent read-only sampling pass for ordinary correctness, data-integrity,
  security, deployment, and UX defects outside the narrow ER list, optionally
  paired with `--mode staff-engineer`.
- **Module Charter:** a short, durable record of a module's owned
  responsibilities, invariants, public contracts, and explicit non-ownership.
- **Spec-Driven Development (SDD):** development where an accepted specification
  governs implementation and verification (**Full-Spec** and **Fast** are the
  two SDD lane postures).
- **Positional Lane:** an architectural change posture applied to a specific
  code responsibility where its conditions hold:
  - **Critical:** high blast radius, shared state, or costly silent failure.
  - **Careful:** meaningful domain contracts requiring steady boundary care.
  - **Full-Spec** *(formerly Rebuildable)*: complete material behavior captured
    in a Responsibility Charter + thin public contract + independent contract
    tests so internal implementation is replaceable from its spec.
  - **Fast:** isolated edge/leaf surface passing the deletion test.
- **Deletion Test:** deleting a Fast-lane surface removes only that surface
  without breaking core consumers.
- **Implementation-Substitution Test:** a Full-Spec responsibility's internal
  code can be replaced from its specification while its charter, public
  boundary, and verified behavior remain intact.
- **Hazard Tag:** a sparse inline code annotation recording non-local failure
  knowledge and the protective action required when touching that site.
