# Presentation Patterns

Select patterns by the reader's task, not by the document's filename or the amount of content. Combine patterns when the reader has multiple distinct tasks. Each pattern describes information relationships and useful interactions; adapt its structure and create the visual design for the current content.

Example IDs refer to the local HTML files indexed in `example-index.md`. Consult only the examples relevant to the selected patterns.

## Compare & Decide

### P1 — Parallel options

- **Use for:** implementation approaches, design directions, product interventions, or any choice with meaningful trade-offs.
- **Structure:** shared evaluation criteria → parallel options with comparable detail → inline trade-offs → recommendation or decision prompt.
- **Interaction:** render design options live when seeing them matters; optionally let the reader mark options to keep, reject, or combine and copy the resulting decision.
- **Why it works:** parallel presentation removes the need to remember sequential prose while comparing.
- **Examples:** E01, E02, U03, U05.

### P2 — Decision-centered implementation plan

- **Use for:** implementation plans, technical specs, migration plans, and handoffs.
- **Structure:** decision context → milestones or workstreams → data flow and interface changes → mockups or critical code → risks and open questions.
- **Interaction:** expose alternatives for high-impact decisions; collapse mechanical detail so the reader can focus on choices that change the design.
- **Why it works:** the plan becomes a review surface rather than a flat checklist.
- **Examples:** E16, U08.

### P3 — Guided requirements interview

- **Use for:** ambiguous features or requests where important decisions are still missing.
- **Structure:** one question at a time, ordered by architectural impact → captured answers → decisions table → ready-to-use implementation brief.
- **Interaction:** answer controls, progress indication, backtracking, and an export of the decisions.
- **Why it works:** it separates clarification from implementation and makes unresolved choices visible.
- **Examples:** U06.

### P4 — Blindspot review

- **Use for:** unfamiliar domains, risky plans, or prompts that may omit important constraints.
- **Structure:** blindspot cards → why each matters → a question or prompt correction for each → consolidated improved brief.
- **Interaction:** copy individual fixes or the complete revised brief; allow dismissing findings that do not apply.
- **Why it works:** it turns vague concern into specific, actionable discoveries.
- **Examples:** U01.

## Understand & Review Code

### P5 — Annotated diff review

- **Use for:** pull request review, code findings, and focused analysis of a change.
- **Structure:** change summary and statistics → annotated diff → severity and margin notes → prioritized action items.
- **Interaction:** jump links between findings and code, file navigation, and filters for severity or file.
- **Why it works:** evidence and judgement remain spatially connected.
- **Examples:** E03.

### P6 — Reviewer-oriented PR narrative

- **Use for:** explaining the author's intent and helping another person review a change.
- **Structure:** motivation → before/after behavior → file-by-file tour explaining why → review focus areas and validation.
- **Interaction:** navigation by file or concern; links from claims to relevant code.
- **Why it works:** it communicates intent and reading order instead of presenting an unstructured diff.
- **Examples:** E17.

### P7 — Module and call-path map

- **Use for:** unfamiliar packages, architecture walkthroughs, and execution-path explanations.
- **Structure:** system map → highlighted hot path → entry points → annotated key code → gotchas.
- **Interaction:** select a module or path to reveal its responsibilities, inputs, outputs, and related code.
- **Why it works:** the reader can move between system shape and implementation detail without losing context.
- **Examples:** E04.

### P8 — Reference implementation mapping

- **Use for:** ports, rewrites, compatibility work, and comparisons with a reference implementation.
- **Structure:** semantics map → matched source and target excerpts → edge-case table → compatibility risks and open questions.
- **Interaction:** select a concept to highlight both implementations; filter mismatches and unresolved cases.
- **Why it works:** it demonstrates semantic understanding before mechanical translation begins.
- **Examples:** U07.

### P9 — Implementation deviation log

- **Use for:** long builds, iterative agent work, and retrospective handoffs.
- **Structure:** chronological implementation notes → each deviation from plan → the decision and its rationale → lessons for the next attempt.
- **Interaction:** filter by decision type or severity; copy the lessons into a future prompt.
- **Why it works:** knowledge discovered during implementation remains available instead of disappearing into the final diff.
- **Examples:** U09.

## Explain & Present

### P10 — Feature explainer

- **Use for:** explaining how a product feature or repository mechanism works.
- **Structure:** concise summary → request or execution path → annotated configuration or code → FAQ and gotchas.
- **Interaction:** collapsible steps, tabbed alternatives, and links between explanation and evidence.
- **Why it works:** different readers can control depth without losing the main path.
- **Examples:** E14.

### P11 — Interactive concept explainer

- **Use for:** abstract concepts, unfamiliar vocabulary, and topics best learned by manipulation.
- **Structure:** mental model → live demonstration → guided manipulation → comparison with alternatives → linked glossary.
- **Interaction:** let the reader change the model's inputs and observe consequences; connect terms to the exact concept they clarify.
- **Why it works:** the reader tests the model rather than memorizing a description.
- **Examples:** E15, U02.

### P12 — Figure or flowchart sheet

- **Use for:** spatial processes, pipelines, article illustrations, and relationships that prose flattens.
- **Structure:** one clear visual idea per figure → concise annotation → legend and supporting detail.
- **Interaction:** clickable nodes for process detail; selectable figures or SVG fragments for reuse.
- **Why it works:** topology, direction, and branching remain visible.
- **Examples:** E10, E13.

### P13 — Keyboard-driven deck

- **Use for:** meetings, narrative walkthroughs, pitches, and sequential storytelling.
- **Structure:** one message per slide → visual evidence or example → concise takeaway → closing decision or action.
- **Interaction:** arrow-key and space navigation, visible progress, and an overview for non-linear access.
- **Why it works:** pacing and attention match a spoken presentation.
- **Examples:** E09.

### P14 — Evidence-led buy-in document

- **Use for:** ship decisions, design approval, stakeholder alignment, and anticipated objections.
- **Structure:** outcome and demonstration → evidence → objections with direct responses → ownership and sign-off requirements.
- **Interaction:** animated or clickable demonstration when behavior is central; navigation by stakeholder concern.
- **Why it works:** the reader can evaluate the result and locate the answer to their specific objection.
- **Examples:** U10.

## Design & Prototype

### P15 — Living design reference

- **Use for:** design tokens, component inventories, visual audits, and component variant review.
- **Structure:** actual rendered values and components → organized scales or variant matrices → usage notes and relevant source references.
- **Interaction:** copy values, compare states, and isolate one dimension such as size, intent, or state.
- **Why it works:** the design language is inspected directly rather than imagined from descriptions.
- **Examples:** E05, E06.

### P16 — Motion or interaction prototype

- **Use for:** animation tuning, click-through flows, placement choices, and interaction questions that require direct experience.
- **Structure:** focused stage → minimal controls → realistic sequence or parameters → decisions to feed back into implementation.
- **Interaction:** real easing, duration, navigation, toggles, or placement controls; export the chosen values or responses.
- **Why it works:** it answers experiential questions that static prose cannot settle.
- **Examples:** E07, E08, U04.

## Monitor & Report

### P17 — Status report

- **Use for:** weekly updates, project health, delivery summaries, and recurring metrics.
- **Structure:** headline state → completed and delayed work → meaningful trend or chart → risks and next actions.
- **Interaction:** filter by workstream or period only when the underlying data supports it.
- **Why it works:** the reader sees state and exceptions before narrative detail.
- **Examples:** E11.

### P18 — Incident timeline

- **Use for:** incident reviews, postmortems, outages, and chronological investigations.
- **Structure:** impact summary → minute-by-minute events → logs and evidence → contributing causes → follow-up checklist.
- **Interaction:** connect timeline events to evidence and filter detection, response, and recovery phases.
- **Why it works:** sequence and causality remain clear while supporting evidence stays close.
- **Examples:** E12.

## Operate & Verify

### P19 — Triage board

- **Use for:** prioritizing tickets, ideas, findings, or other discrete items.
- **Structure:** meaningful buckets → draggable items → visible ordering and rationale → export.
- **Interaction:** drag-and-drop plus keyboard-accessible movement, item details, and export of the current ordering.
- **Why it works:** prioritization becomes direct manipulation rather than a rewritten list.
- **Examples:** E18.

### P20 — Configuration editor

- **Use for:** feature flags, settings, rule changes, and dependency-sensitive configuration.
- **Structure:** grouped settings → current and proposed state → dependency warnings → changed-values export.
- **Interaction:** toggles or fields, validation, reset, and an export containing only meaningful changes.
- **Why it works:** the reader can safely explore consequences and bring the result back into the workflow.
- **Examples:** E19.

### P21 — Live template tuner

- **Use for:** prompt templates, message templates, configuration text, and repeated structured writing.
- **Structure:** editable template → highlighted variables → representative sample inputs → live previews → export.
- **Interaction:** edit once and compare several previews immediately; copy the final template or generated output.
- **Why it works:** variation and edge cases become visible while editing.
- **Examples:** E20.

### P22 — Comprehension check

- **Use for:** merge readiness, training, handoffs, and verifying that a reader understood the artifact.
- **Structure:** focused review material → short diagnostic quiz → answer-specific pointers back to evidence → readiness summary.
- **Interaction:** answer questions, receive explanatory feedback, and revisit the exact section that resolves a mistake.
- **Why it works:** it tests understanding and routes the reader back to missing knowledge.
- **Examples:** U11.
