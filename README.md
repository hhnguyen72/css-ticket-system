# CSS Ticket Management Tool — ID Generation Feature

## Project Structure --Needs Updating

```

css-ticket-system/
├── resources/spec_bundle
│   ├── acceptance_criteria.md
│   ├── architecture_decision_records.md
│   ├── bug_report.md
│   ├── goals_non_goals.md
│   ├── requirements_ears.md
│   └── user_stories.md   
├── src
│   ├── mock_classsifier.py       
│   ├── mock_router.py
│   ├── models.py
│   └── protocols.py  
├── tests/
│   └── test_ticket_id.py   # Unit tests mapping to TDD-01 through TDD-05
├ AGENTS.md
├ CLAUDE.md
├ main.py
├ pytest.ini
├ README.md
├ requirements.txt

```

## Team Ownership

| Module                       | Owner                | Implement Here?  |
|------------------------------|----------------------|------------------|
| `/models.py`                 | Shared               | ✅ Shared types  |
| `/protocols.py`              | Shared               | ❌ No bodies     |
| `src/mock_classifier.py`     | ID Generation team   | ✅ Mock only     |
| `src/mock_router.py`         | ID Generation team   | ✅ Mock only     |
| `src/test_ticket_id.py`      | ID Generation team   | ✅ Tests only    |
| `service/classifier.py`      | ID Generation team   | ✅ Tests only    |
| `service/queue_store.py`     | ID Generation team   | ✅ Tests only    |
| `service/redactor.py`        | ID Generation team   | ✅ Tests only    |
| `service/router.py`          | ID Generation team   | ✅ Tests only    |
| `service/sequence_counter.py`|  ID Generation team  | ✅ Tests only    |
| `service/ticket_id.py`       | ID Generation team   | ✅ Tests only    |


## Boundary Rules

- `Classifier` and `Router` interface bodies are owned by their respective teams.
- Mock implementations in `mocks/` must never be used in production.
- ID is assigned **after** classification and **before** enqueue — always.
- Redaction is applied **before** storage or display — always.

## Running Tests

```bash
pip install pytest
pytest tests/test_ticket_id.py -v
```

## Ticket ID Format

```
CSS-YYYYMMDD-NNNN
└─┬─┘└──┬───┘└┬─┘
  │     │     └── Zero-padded sequence, min 4 digits, no upper cap
  │     └──────── Local server date (EST/EDT)
  └────────────── Fixed prefix
```

## Guardrails

- DoD IDs matching `\b\d{10}\b` → replaced with `[DOD_ID_REDACTED]`
- 100% redaction rate required — zero tolerance
- Non-DoD 10-digit numbers must not be redacted
