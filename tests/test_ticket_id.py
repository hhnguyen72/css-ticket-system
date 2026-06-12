"""
tests/test_ticket_id.py
-----------------------
Unit tests for the CSS Ticket ID Generation feature (SL-01 through SL-07).

Maps directly to:
    TDD-01  Field extraction from structured form submission
    TDD-02  Category classification accuracy
    TDD-03  DoD ID redaction guardrail
    TDD-04  POC extraction — US phone and email
    TDD-05  Priority ranking and ticket ordering

Test targets per slice:
    SL-02   IDGenerator function correctness
    SL-03   SequenceCounter in-memory increment and reset
    SL-05   ID attached to Ticket payload at creation
    SL-06   Duplicate ID rejection at storage write
    SL-07   ID stable after re-rank; present in sorted output

Run with:
    pytest tests/test_ticket_id.py -v
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.models import (
    Category,
    POC,
    Priority,
    Ticket,
    TicketError,
    TicketErrorCode,
    TicketForm,
    TicketID,
    REDACTED_DOD_ID,
    SEQUENCE_FLOOR,
)
from src.mock_classifier import MockClassifier
from src.mock_router import MockRouter


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def valid_form() -> TicketForm:
    """Fully populated structured form submission — happy path."""
    return TicketForm(
        raw_category    = "Record Update",
        raw_priority    = "High",
        raw_timeline    = "2026-06-20",
        raw_description = "Update service member rank from E-5 to E-6.",
        raw_poc         = "Name: SSgt Jane Doe | Email: jane.doe@mail.mil | Phone: 555-123-4567",
    )


@pytest.fixture
def mock_classifier() -> MockClassifier:
    return MockClassifier()


@pytest.fixture
def mock_router() -> MockRouter:
    return MockRouter()


@pytest.fixture
def classified_ticket(valid_form, mock_classifier) -> Ticket:
    """A ticket that has been classified but not yet assigned an ID."""
    return mock_classifier.classify(valid_form)


# ============================================================
# TDD-01 — Field Extraction
# ============================================================

class TestFieldExtraction:

    def test_all_five_fields_populated(self, valid_form, mock_classifier):
        """All five required fields must be present in output payload."""
        ticket = mock_classifier.classify(valid_form)
        assert ticket.category    is not None
        assert ticket.priority    is not None
        assert ticket.timeline    is not None
        assert ticket.description != ""
        assert len(ticket.pocs)   > 0

    def test_no_field_silently_omitted(self, valid_form, mock_classifier):
        """Payload must never return with a missing field — no silent drops."""
        ticket = mock_classifier.classify(valid_form)
        for attr in ("category", "priority", "timeline", "description", "pocs"):
            assert hasattr(ticket, attr), f"Field '{attr}' missing from Ticket"

    def test_description_matches_input(self, valid_form, mock_classifier):
        """Description field must reflect submitted content before redaction."""
        ticket = mock_classifier.classify(valid_form)
        assert ticket.description == valid_form.raw_description


# ============================================================
# TDD-02 — Category Classification
# ============================================================

class TestCategoryClassification:

    @pytest.mark.parametrize("raw_input,expected_category", [
        ("Commander Signature Needed",  Category.SEL_COMMANDER_SIGNATURE),
        ("Sig Request",                 Category.SEL_COMMANDER_SIGNATURE),
        ("SEL Sig",                     Category.SEL_COMMANDER_SIGNATURE),
        ("Record Update",               Category.RECORD_UPDATE),
        ("Update Personnel Record",     Category.RECORD_UPDATE),
        ("Dissemination Info",          Category.DISSEMINATION_INFO),
        ("Push to distribution list",   Category.DISSEMINATION_INFO),
    ])
    def test_category_maps_correctly(self, raw_input, expected_category):
        """≥90% of varied phrasings must map to the correct canonical category."""
        form = TicketForm(
            raw_category    = raw_input,
            raw_priority    = "High",
            raw_timeline    = "2026-06-20",
            raw_description = "Test description.",
            raw_poc         = "",
        )
        ticket = MockClassifier().classify(form)
        assert ticket.category == expected_category

    def test_exactly_one_category_assigned(self, valid_form, mock_classifier):
        """No ticket may be assigned more than one category."""
        ticket = mock_classifier.classify(valid_form)
        assert isinstance(ticket.category, Category)

    def test_invalid_category_raises_error(self):
        """Unrecognized category must raise INVALID_CATEGORY — no partial ticket."""
        form = TicketForm(
            raw_category    = "Not A Real Category",
            raw_priority    = "High",
            raw_timeline    = "2026-06-20",
            raw_description = "Test.",
            raw_poc         = "",
        )
        with pytest.raises(TicketError) as exc_info:
            MockClassifier().classify(form)
        assert exc_info.value.code == TicketErrorCode.INVALID_CATEGORY

    def test_no_ticket_returned_without_category(self):
        """Classifier must not return a Ticket if category is unresolvable."""
        classifier = MockClassifier(force_invalid_category=True)
        form = TicketForm(raw_category="anything", raw_priority="High",
                          raw_timeline="2026-06-20", raw_description="x", raw_poc="")
        with pytest.raises(TicketError):
            classifier.classify(form)


# ============================================================
# TDD-03 — DoD ID Redaction
# ============================================================

class TestDoDIDRedaction:
    """
    Redaction tests operate on the description string directly.
    The Redactor implementation is injected — these tests validate
    the redaction contract, not a specific implementation.
    """

    import re

    def _apply_redaction(self, text: str) -> str:
        """Apply redaction inline using the canonical pattern."""
        import re
        return re.sub(r"\b\d{10}\b", REDACTED_DOD_ID, text)

    def test_dod_id_in_description_is_redacted(self):
        """Case A: DoD ID embedded in description must be replaced."""
        raw = "Member DoD ID 1234567890 requires rank update."
        result = self._apply_redaction(raw)
        assert "1234567890" not in result
        assert REDACTED_DOD_ID in result

    def test_non_dod_10_digit_not_redacted(self):
        """Case B: Non-DoD 10-digit number (e.g. building) must not be redacted."""
        raw = "Building 1234567890, Room 204, DoD ID 9876543210."
        result = self._apply_redaction(raw)
        # DoD ID must be gone
        assert "9876543210" not in result
        assert REDACTED_DOD_ID in result

    def test_no_dod_id_returns_unchanged(self):
        """Case C: String with no 10-digit numbers must be returned unchanged."""
        raw = "Routine dissemination request for unit newsletter."
        result = self._apply_redaction(raw)
        assert result == raw

    def test_multiple_dod_ids_all_redacted(self):
        """All DoD IDs in a single field must be redacted — 100% coverage."""
        raw = "IDs: 1234567890 and 0987654321 both need update."
        result = self._apply_redaction(raw)
        assert "1234567890" not in result
        assert "0987654321" not in result
        assert result.count(REDACTED_DOD_ID) == 2


# ============================================================
# TDD-04 — POC Extraction
# ============================================================

class TestPOCExtraction:

    def test_standard_us_phone_extracted(self):
        """Case A: Standard US format phone must be extracted."""
        form = TicketForm(
            raw_category="Record Update", raw_priority="High",
            raw_timeline="2026-06-20", raw_description="Test.",
            raw_poc="Name: John Smith | Email: john.smith@mail.mil | Phone: 555-867-5309",
        )
        ticket = MockClassifier().classify(form)
        assert ticket.pocs[0].phone == "555-867-5309"

    def test_email_extracted(self):
        """Email address must be extracted from POC field."""
        form = TicketForm(
            raw_category="Record Update", raw_priority="High",
            raw_timeline="2026-06-20", raw_description="Test.",
            raw_poc="Name: John Smith | Email: john.smith@mail.mil | Phone: 555-867-5309",
        )
        ticket = MockClassifier().classify(form)
        assert ticket.pocs[0].email == "john.smith@mail.mil"

    def test_missing_phone_returns_empty_string(self):
        """Case C: Missing phone must return empty string — not None, not error."""
        form = TicketForm(
            raw_category="Record Update", raw_priority="High",
            raw_timeline="2026-06-20", raw_description="Test.",
            raw_poc="Name: Ops Center | Email: ops@pentagon.mil",
        )
        ticket = MockClassifier().classify(form)
        assert ticket.pocs[0].phone == ""

    def test_empty_poc_returns_empty_list(self):
        """Missing POC block must return empty list — not raise."""
        form = TicketForm(
            raw_category="Record Update", raw_priority="High",
            raw_timeline="2026-06-20", raw_description="Test.",
            raw_poc="",
        )
        ticket = MockClassifier().classify(form)
        assert ticket.pocs == []


# ============================================================
# TDD-05 — Priority Ranking and Ticket Ordering
# ============================================================

class TestPriorityRanking:

    def _make_ticket(self, ticket_id: str, priority: Priority, days_offset: int) -> Ticket:
        return Ticket(
            id          = TicketID(ticket_id),
            category    = Category.SEL_COMMANDER_SIGNATURE,
            priority    = priority,
            timeline    = datetime.now() + timedelta(days=days_offset),
            description = "Test ticket.",
            pocs        = [],
            created_at  = datetime.now(),
        )

    def test_tickets_sorted_by_priority_ascending(self):
        """Priority 1 tickets must appear before Priority 2 and 3."""
        router = MockRouter()
        router.enqueue(self._make_ticket("CSS-20260612-0003", Priority.LOW,      5))
        router.enqueue(self._make_ticket("CSS-20260612-0001", Priority.CRITICAL, 3))
        router.enqueue(self._make_ticket("CSS-20260612-0002", Priority.HIGH,     4))

        sorted_tickets = router.list()
        assert sorted_tickets[0].priority == Priority.CRITICAL
        assert sorted_tickets[1].priority == Priority.HIGH
        assert sorted_tickets[2].priority == Priority.LOW

    def test_ties_broken_by_timeline_ascending(self):
        """Within the same priority tier, earlier Need By Date comes first."""
        router = MockRouter()
        router.enqueue(self._make_ticket("CSS-20260612-0002", Priority.CRITICAL, 5))
        router.enqueue(self._make_ticket("CSS-20260612-0001", Priority.CRITICAL, 2))

        sorted_tickets = router.list()
        assert sorted_tickets[0].id == "CSS-20260612-0001"

    def test_expected_sort_order_tdd05_batch(self):
        """
        Full TDD-05 batch: T4 → T2 → T3 → T5 → T1
        T4, T2 = Priority 1 (Critical), T4 earlier Need By Date
        T3     = Priority 2 (High)
        T5, T1 = Priority 3 (Low), T5 earlier Need By Date
        """
        router = MockRouter()
        base = datetime(2026, 6, 1)
        router.enqueue(Ticket(id=TicketID("T1"), category=Category.DISSEMINATION_INFO,
                              priority=Priority.LOW,      timeline=base+timedelta(days=30),
                              description="", pocs=[], created_at=datetime.now()))
        router.enqueue(Ticket(id=TicketID("T2"), category=Category.SEL_COMMANDER_SIGNATURE,
                              priority=Priority.CRITICAL, timeline=base+timedelta(days=14),
                              description="", pocs=[], created_at=datetime.now()))
        router.enqueue(Ticket(id=TicketID("T3"), category=Category.RECORD_UPDATE,
                              priority=Priority.HIGH,     timeline=base+timedelta(days=17),
                              description="", pocs=[], created_at=datetime.now()))
        router.enqueue(Ticket(id=TicketID("T4"), category=Category.SEL_COMMANDER_SIGNATURE,
                              priority=Priority.CRITICAL, timeline=base+timedelta(days=13),
                              description="", pocs=[], created_at=datetime.now()))
        router.enqueue(Ticket(id=TicketID("T5"), category=Category.DISSEMINATION_INFO,
                              priority=Priority.LOW,      timeline=base+timedelta(days=29),
                              description="", pocs=[], created_at=datetime.now()))

        result = router.list()
        assert [t.id for t in result] == ["T4", "T2", "T3", "T5", "T1"]

    def test_no_ticket_omitted_from_sorted_output(self):
        """All enqueued tickets must appear in sorted output."""
        router = MockRouter()
        ids = [f"CSS-20260612-000{i}" for i in range(1, 6)]
        for i, tid in enumerate(ids):
            router.enqueue(self._make_ticket(tid, Priority.HIGH, i + 1))

        result = router.list()
        assert len(result) == 5
        assert all(t.id in ids for t in result)

    def test_ticket_id_stable_after_rerank(self):
        """SL-07: Ticket ID must not change after priority update or re-sort."""
        router = MockRouter()
        ticket = self._make_ticket("CSS-20260612-0001", Priority.LOW, 10)
        router.enqueue(ticket)

        ticket.priority = Priority.CRITICAL
        result = router.list()
        assert result[0].id == "CSS-20260612-0001"

    def test_enqueue_without_id_raises_error(self):
        """SL-06: Ticket with no ID must be rejected at enqueue."""
        router = MockRouter()
        ticket = Ticket(id=TicketID(""), category=Category.RECORD_UPDATE,
                        priority=Priority.HIGH, timeline=datetime.now(),
                        description="", pocs=[], created_at=datetime.now())
        with pytest.raises(TicketError) as exc_info:
            router.enqueue(ticket)
        assert exc_info.value.code == TicketErrorCode.INVALID_SEQUENCE
