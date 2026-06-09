---
name: to-tasks
description: Break a plan, spec, or PRD into independently-grabbable tasks on the project task tracker using tracer-bullet vertical slices. Use when user wants to convert a plan into tasks, requirements into tasks, create implementation tasks or break down work into tasks.
---

# To Tasks

The word "Task" is synonymous with JIRA's "Ticket" and Github's "Issues": a mechanism with which work is captured and tracked through to completion in an system.

Break a plan into independently-grabbable tasks using vertical slices (tracer bullets). Each task should be no more than one PR/MR worth of work.

Domain knowledge can be found in `CONTEXT.md` or if there are many domain documents in the codebase then `CONTEXT-MAP.md` will contain references to their locations. Use this documentation to ensure your wording is inline with the codebase architecture.

ADRs can be found in a `docs/adr/` directory, or if a `CONTEXT-MAP.md` exists then there may be an `docs/adr/` directory alongside each `CONTEXT.md` file.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes an issue reference (issue number, URL, or path) as an argument, fetch it from the issue tracker and read its full body and comments.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code. Issue titles and descriptions should use the project's domain glossary vocabulary, and respect ADRs in the area you're touching.

### 3. Draft vertical slices

Break the plan into **tracer bullet** tasks. Each issue is a thin vertical slice that cuts through ALL integration layers end-to-end, NOT a horizontal slice of one layer.

<vertical-slice-rules>
- Each slice delivers a narrow but COMPLETE path through every layer (schema, API, UI, tests)
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones
</vertical-slice-rules>

### 4. Quiz the user

Present the proposed breakdown as a numbered list. For each slice, show:

- **Title**: short descriptive name
- **Blocked by**: which other slices (if any) must complete first
- **User stories covered**: which user stories this addresses (if the source material has them)

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the dependency relationships correct?
- Should any slices be merged or split further?

Iterate until the user approves the breakdown.

### 5. Publish the issues to the issue tracker

For each approved slice, publish a task to the task tracker. If there is already a parent task, then create sub-tasks if the workload is greater than one PR/MR. Use the task body template below.

Publish tasks in dependency order (blockers first) so you can reference real issue identifiers in the "Blocked by" field.

<task-template>
# Summary of Task


## What to build

A concise description of this vertical slice. Describe the end-to-end behavior, not layer-by-layer implementation.

Avoid specific file paths or code snippets — they go stale fast.

## User Story

The user story being implemented by this task.

### Acceptance criteria

The acceptance criteria to fulfil this user story.

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Blocked by

- A reference to the blocking task (if any)

Or "No blockers - can start immediately" if no blockers.

</task-template>

Do NOT close or modify any parent issue.
