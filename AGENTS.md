# Triage Application — Agent Guide

## What This Project Is

A Python CLI triage queue. Operators submit cases with a severity and description, view the sorted queue, and resolve cases by ID. The queue always shows the most critical cases at the top.

## Target Output (the goal)

When an operator views the queue, the CLI must produce exactly this format:

```
#     ID         Severity   Description
-------------------------------------------------------
1     3a2f1b4c   Critical   Database server unresponsive
2     9d4e7a1f   High       Login page returning 500 error
3     1c8b2d9e   Medium     Report export running slowly
```

All work in this repo is oriented toward making the application produce correct output matching this template.

## Source of Truth for Correct Behaviour

Before making any change, read:

- [`resources/spec_bundle/bug_report.md`](resources/spec_bundle/bug_report.md) — two known bugs with reproduction steps
- [`resources/spec_bundle/user_stories.md`](resources/spec_bundle/user_stories.md) - intentions of the application
- [`resources/spec_bundle/acceptance_criteria.md`](resources/spec_bundle/acceptance_criteria.md) - acceptance criteria for Submit and Resolve flows
- [`resources/spec_bundle/goals_non_goals.md`](resources/spec_bundle/goals_non_goals.md) - 
- [`resources/spec_bundle/requirements_ears.md`](resources/spec_bundle/requirements_ears.md) - 
- [`resources/spec_bundle/bug_report.md`](resources/spec_bundle/bug_report.md) - 

These documents define what "correct" means. Tests and implementation should align with them.

## Codebase Map

```
triage.py          — Severity enum, Case dataclass, TriageQueue class
main.py            — CLI menu, display_queue(), submit_case(), resolve_case()
tests/             — pytest suite
resources/         — user_stories.md, bug_report.md
```

## Acceptance Criteria (quick reference)

**Submit a case**
- Requires a non-empty, non-whitespace description and a valid severity (Critical / High / Medium / Low, case-insensitive).
- Invalid inputs must be rejected with an error; no case is created.
- The new case must appear in the queue at the correct severity position, oldest-first within a tier.

**Resolve a case**
- Requires a valid, open case ID.
- On success, the case is removed from the active queue and the system confirms the closure.
- An unknown ID must produce an error with no side effects.

## Sort Order

```
Critical (4) > High (3) > Medium (2) > Low (1)
```

Within the same severity, cases are ordered by `created_at` ascending (oldest first).

## Running the Project

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py   # launch the CLI
pytest           # run tests
```

## Constraints

- No database — queue is in-memory only; data does not persist between runs.
- Domain logic belongs in `triage.py`; all I/O belongs in `main.py`.
- Case IDs are the first 8 hex characters of a UUID4.
