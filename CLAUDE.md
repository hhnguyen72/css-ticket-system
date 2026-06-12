# Css-ticket-system Application — Claude Code Guide

# css-ticket-system

A structured ticket-parsing agent that extracts and populates six fields from free-text CSS team requests, enforces DoD ID redaction before output, and assigns every request to one of three defined categories.

## End Goal — Target CLI Output

The queue view is the north star for this project. The output must render exactly like this:

```
#     ID         Severity   Description
-------------------------------------------------------
1     3a2f1b4c   Critical   Database server unresponsive
2     9d4e7a1f   High       Login page returning 500 error
3     1c8b2d9e   Medium     Report export running slowly
```

- Rows are sorted: Critical first, then High, Medium, Low.
- Within the same severity, cases appear oldest-first.
- Column widths are fixed (`#` 5, `ID` 10, `Severity` 10, `Description` free).

## Key Files

| File | Purpose |
|---|---|
| `triage.py` | Core domain — `Severity` enum, `Case` dataclass, `TriageQueue` |
| `main.py` | CLI loop — menu, `display_queue`, `submit_case`, `resolve_case` |
| `resources/user_stories.md` | Acceptance criteria for every feature (source of truth for correct behaviour) |
| `resources/bug_report.md` | Known bugs and reproduction steps |
| `tests/` | pytest suite |

## User Stories (summary)

See [`resources/user_stories.md`](resources/user_stories.md) for full acceptance criteria.

- **Story 1 — Submit a case**: operator provides description + severity; system assigns a unique ID and places the case in priority order. Empty descriptions and invalid severity values must be rejected.
- **Story 2 — Resolve a case**: operator provides a case ID; system removes it from the active queue and confirms the closure. An unknown ID must produce an error with no side effects.

## Known Bugs

See [`resources/bug_report.md`](resources/bug_report.md) for reproduction steps.

1. **Empty / whitespace-only descriptions** are accepted when they should be rejected.
2. **Queue display is inverted** — lowest-severity cases surface first instead of Critical.

## Setup & Run

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python main.py   # run the app
pytest           # run the test suite
```

## Coding Conventions

- Domain logic lives in `triage.py`; I/O lives in `main.py`. Keep them separate.
- `Severity` values drive sort order — higher `.value` = higher priority.
- Case IDs are the first 8 characters of a UUID4.
- No persistence — the queue lives in memory only.
