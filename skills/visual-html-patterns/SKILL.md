---
name: visual-html-patterns
description: Generate single-file HTML with content-led presentation patterns and flexible visual styling.
disable-model-invocation: true
argument-hint: "<content or topic to turn into HTML>"
---

# Visual HTML Patterns

Choose the presentation from the reader's task. Treat source examples as information-design references, not visual templates.

## Workflow

1. **Frame the reader's task.**
   Identify the audience, available source material, and the primary action the reader needs to take: compare, understand, learn, decide, monitor, operate, present, discover, or verify. Use one primary task and any necessary supporting tasks.
   *Done:* you can state who the page is for, what they will do with it, and which source facts it must preserve.

2. **Select one or more presentation patterns.**
   Read the matching sections of `references/presentation-patterns.md` before choosing a layout:
   - Comparing options, planning work, interviews, or blindspot discovery → **Compare & Decide**
   - Reviewing code, explaining architecture, or recording implementation decisions → **Understand & Review Code**
   - Teaching, presenting, diagramming, or building a case for approval → **Explain & Present**
   - Documenting design or exploring motion and interaction → **Design & Prototype**
   - Communicating progress or incidents → **Monitor & Report**
   - Manipulating state or testing comprehension → **Operate & Verify**

   Choose a primary pattern and supporting patterns only when they serve distinct reader tasks. If none fits, design a new form from the reader's task and record why it fits better.
   *Done:* you have either named the selected pattern IDs and explained their fit, or named the custom form and explained why no existing pattern fits; you have identified any source example IDs worth consulting.

3. **Consult only the useful local source examples.**
   When selected examples would add useful detail, use `references/example-index.md` to locate and read their local HTML. Study their information hierarchy, sequencing, and interactions; their colors, typography, spacing, and component styling are not defaults. Use online originals only when the user explicitly asks to check or update the upstream version. If a local example is missing, record the gap and continue from the local pattern descriptions.
   *Done:* you have extracted the structural ideas needed for this artifact from local examples or pattern descriptions, recorded any missing local examples, and identified any user-requested online consultation.

4. **Design the information architecture before the visuals.**
   Outline the sections, evidence, reading order, and controls. Preserve supplied facts and uncertainty; omit unsupported sections rather than inventing content to fill a pattern. Add interaction only when it improves comparison, exploration, explanation, input, or export.
   *Done:* every planned section and control has a specific content or reader-task purpose.

5. **Create a content-led visual design.**
   Derive layout, typography, palette, density, and graphic language from the subject, audience, brand, and user instructions. Patterns constrain information relationships, not the page's skin. Use cards only for genuinely discrete items; continuous prose, tables, timelines, diagrams, and freeform compositions are equally valid.
   *Done:* you can name the layout, typography, palette, and density decisions and the content requirement that each decision serves.

6. **Build the artifact.**
   Unless the user requests another setup, create one self-contained `.html` file with inline CSS, JavaScript, and SVG and no runtime network dependency. Use semantic HTML, responsive layouts, accessible controls, keyboard support where relevant, and reduced-motion handling for substantial animation.
   *Done:* the file contains the complete experience and works without a build step.

7. **Verify the delivered HTML.**
   When browser tools are available, open the generated file and exercise every control, check the reading order and narrow-screen layout, and confirm that exports reflect the current UI state. When browser tools are unavailable, perform static checks on the generated HTML and list the untested interactions and responsive behavior in the response.
   *Done:* the browser-based checks have passed, or static checks are complete and every unverified browser behavior is listed in the response.

## Response

Return the file path, the selected pattern IDs or custom form and the reason for that choice, instructions for opening the artifact, and a concise summary of its interactions and verification.
